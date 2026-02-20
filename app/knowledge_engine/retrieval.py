import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


# ==============================================
# Logging setup
# ==============================================

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
    """RFP-Aware Retrieval Layer"""

    def __init__(
        self,
        embedding_service,
        vector_store_service,
        score_threshold: float = 0.80,
    ):
        self.embedding_service = embedding_service
        self.vector_store_service = vector_store_service
        self.score_threshold = score_threshold

    # ==============================================
    # Public Search
    # ==============================================

    def search(
        self,
        query: str,
        top_k: int = 15,
        doc_type: Optional[str] = None,
        section: Optional[str] = None,
        recency_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        start_time = time.time()

        filter_dict = self._build_filter(
            doc_type=doc_type,
            section=section,
            recency_days=recency_days,
        )

        if " vs " in query.lower():
            results = self._handle_comparison_query(
                query, top_k, filter_dict
            )
        else:
            results = self._handle_single_query(
                query, top_k, filter_dict
            )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        self.log_retrieval(
            query=query,
            top_k=top_k,
            filters=filter_dict,
            results=results,
            latency_ms=latency_ms,
        )

        return results

    # ==============================================
    # Core Query Handling
    # ==============================================

    def _handle_single_query(
        self,
        query: str,
        top_k: int,
        filter_dict: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        query_embedding = self.embedding_service.embed_query(query)

        docs_and_scores = self.vector_store_service.similarity_search(
            query_embedding=query_embedding,
            k=top_k,
            filter=filter_dict if filter_dict else None,
        )

        return self._post_process(docs_and_scores)

    def _handle_comparison_query(
        self,
        query: str,
        top_k: int,
        filter_dict: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        parts = query.lower().split(" vs ")
        aggregated_results = []

        for part in parts:
            cleaned = part.strip()
            if not cleaned:
                continue

            embedding = self.embedding_service.embed_query(cleaned)

            docs_and_scores = self.vector_store_service.similarity_search(
                query_embedding=embedding,
                k=top_k,
                filter=filter_dict if filter_dict else None,
            )

            processed = self._post_process(docs_and_scores)
            aggregated_results.extend(processed)

        # Deduplicate AFTER loop
        unique_map = {
            r["content"]: r for r in aggregated_results
        }

        return list(unique_map.values())

    # ==============================================
    # Metadata Filter Building
    # ==============================================

    def _build_filter(
        self,
        doc_type: Optional[str],
        section: Optional[str],
        recency_days: Optional[int],
    ) -> Dict[str, Any]:

        filter_dict: Dict[str, Any] = {}

        if doc_type:
            filter_dict["doc_type"] = doc_type.strip().lower()

        if section:
            filter_dict["section"] = section.strip().lower()

        if recency_days:
            cutoff = datetime.utcnow() - timedelta(days=recency_days)
            filter_dict["created_at"] = {
                "$gte": cutoff.isoformat()
            }

        return filter_dict

    # ==============================================
    # Post Processing
    # ==============================================

    def _post_process(
        self,
        docs_and_scores,
    ) -> List[Dict[str, Any]]:

        results = []

        for doc, score in docs_and_scores:

            similarity = 1 - score if score > 1 else score

            if similarity < self.score_threshold:
                continue

            results.append({
                "content": doc.page_content,
                "score": similarity,
                "metadata": doc.metadata,
            })

        return results

    # ==============================================
    # Structured Logging
    # ==============================================

    def log_retrieval(
        self,
        query: str,
        top_k: int,
        filters: Dict[str, Any],
        results: List[Dict[str, Any]],
        latency_ms: float,
    ):

        log_payload = {
            "query": query,
            "top_k": top_k,
            "filters_applied": filters,
            "result_count": len(results),
            "scores": [r["score"] for r in results],
            "latency_ms": latency_ms,
        }

        logger.info(f"RETRIEVAL_LOG | {log_payload}")