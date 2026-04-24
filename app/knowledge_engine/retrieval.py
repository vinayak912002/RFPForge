import logging
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple



# ==========================================================
# Logging Configuration
# ==========================================================

logger = logging.getLogger("retrieval")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RetrievalService:
    """
    Production-Grade RFP Retrieval Layer

    Features:
    - Embedding-based retrieval
    - Optional Cross-Encoder reranking (BGE)
    - Graceful fallback
    - Latency monitoring
    - Metadata filtering
    - Structured logging
    - Thread-safe lazy model loading
    """

    def __init__(
        self,
        embedding_service,
        vector_store_service,
        score_threshold: float = 0.0,
        rerank: bool = True,
        rerank_top_k: int = 5,
        max_latency_ms: int = 2000,
        reranker_cls=None,
    ):
        """
        Initialize RetrievalService.

        Args:
            embedding_service: Service responsible for generating query embeddings.
            vector_store_service: Service handling similarity search.
            score_threshold: Minimum similarity score to include results.
            rerank: Whether to enable cross-encoder reranking.
            rerank_top_k: Number of documents to retain after reranking.
            max_latency_ms: Maximum acceptable latency before fallback.
        """

        self.embedding_service = embedding_service
        self.vector_store_service = vector_store_service
        self.score_threshold = score_threshold

        self.rerank_enabled = rerank
        self.rerank_top_k = rerank_top_k
        self.max_latency_ms = max_latency_ms

        self._reranker = None
        self._reranker_lock = threading.Lock()
        self.reranker_cls=reranker_cls 

    # ==========================================================
    # Public Search API
    # ==========================================================

    def search(
        self,
        query: str,
        top_k: int = 15,
        doc_type: Optional[str] = None,
        section: Optional[str] = None,
        recency_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute retrieval search with optional reranking.

        Returns:
            List of result dictionaries containing:
            - content
            - score
            - metadata
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        start_time = time.time()

        filters = self._build_filter(doc_type, section, recency_days)

        try:
            query_embedding = self.embedding_service.embed_query(query)

            docs_and_scores = self.vector_store_service.similarity_search(
                collection_name=self.vector_store_service.collection_name,
                query_embedding=query_embedding,
                k=top_k,
                filter=filters if filters else None,
            )

            # Apply similarity threshold filtering
            docs_and_scores = [
                (doc, score)
                for doc, score in docs_and_scores
                if score >= self.score_threshold
            ]

            # Optional reranking
            rerank_latency = 0
            if self.rerank_enabled and docs_and_scores:
                rerank_start = time.time()

                try:
                    docs_and_scores = self._apply_reranker(
                        query,
                        docs_and_scores,
                        self.rerank_top_k,
                    )
                except Exception as e:
                    logger.warning(f"Reranker failed, fallback to embedding-only. Error: {e}")

                rerank_latency = round((time.time() - rerank_start) * 1000, 2)

            results = self._format_results(docs_and_scores)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

        total_latency = round((time.time() - start_time) * 1000, 2)

        self._log_retrieval(
            query=query,
            top_k=top_k,
            filters=filters,
            result_count=len(results),
            latency_ms=total_latency,
            rerank_latency_ms=rerank_latency if self.rerank_enabled else 0,
        )


        return results

    # ==========================================================
    # Reranker
    # ==========================================================

    def _lazy_load_reranker(self):
        """
        Lazily load cross-encoder reranker in thread-safe manner.
        """
        if self._reranker is None:
                with self._reranker_lock:
                    if self._reranker is None:
                        logger.info("Loading BGE reranker...")

                        if self.reranker_cls is not None:
                            # used in tests 
                            self._reranker = self.reranker_cls()
                        else: 
                            from FlagEmbedding import FlagReranker
                            self._reranker = FlagReranker(
                                "BAAI/bge-reranker-large",
                                use_fp16=False,
                        )

       
            
    def _apply_reranker(
        self,
        query: str,
        docs_and_scores: List[Tuple[Any, float]],
        top_k: int,
    ) -> List[Tuple[Any, float]]:
        """
        Apply BGE cross-encoder reranking.

        Returns:
            Reranked list of (doc, score) tuples.
        """

        self._lazy_load_reranker()

        # Create query-document pairs
        pairs = [
            [query, doc.page_content]
            for doc, _ in docs_and_scores
        ]

        # Compute cross-encoder relevance scores
        scores = self._reranker.compute_score(pairs)

        # Combine original docs with new scores
        reranked = [
            (doc, score)
            for (doc, _), score in zip(docs_and_scores, scores)
        ]

        # Sort by reranker score
        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked[:top_k]

    # ==========================================================
    # Utilities
    # ==========================================================

    def _build_filter(
        self,
        doc_type: Optional[str],
        section: Optional[str],
        recency_days: Optional[int],
    ) -> Dict[str, Any]:
        """
        Construct metadata filter dictionary.
        """

        filters: Dict[str, Any] = {}

        if doc_type:
            filters["doc_type"] = doc_type.strip().lower()

        if section:
            filters["section"] = section.strip().lower()

        if recency_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=recency_days)
            filters["created_at"] = {"$gte": cutoff.isoformat()}

        return filters

    def _format_results(
        self,
        docs_and_scores: List[Tuple[Any, float]],
    ) -> List[Dict[str, Any]]:
        """
        Convert raw results into API-safe dictionary format.
        """

        return sorted(
            [
                {
                    "content": doc.page_content,
                    "score": score,
                    "metadata": doc.metadata,
                }
                for doc, score in docs_and_scores
            ],
            key=lambda x: x["score"],
            reverse=True,
        )

    def _log_retrieval(
        self,
        query: str,
        top_k: int,
        filters: Dict[str, Any],
        result_count: int,
        latency_ms: float,
        rerank_latency_ms: float,
    ):
        """
        Log structured retrieval metadata.
        """

        logger.info(
            {
                "event": "retrieval",
                "query": query,
                "top_k": top_k,
                "filters": filters,
                "result_count": result_count,
                "latency_ms": latency_ms,
                "rerank_latency_ms": rerank_latency_ms,
                "rerank_enabled": self.rerank_enabled,
            }
        )