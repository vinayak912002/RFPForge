from sentence_transformers import SentenceTransformer
import torch
import hashlib
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np

def load_embedding_model(
    model_name: str = "BAAI/bge-large-en-v1.5",
    device: str | None = None
):
    """
    Loads and returns a SentenceTransformer model
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    model = SentenceTransformer(model_name, device=device)
    return model

def get_cache_key(text: str, model_name: str) -> str:
    """
    Deterministic hash for a model + chunk
    """
    payload = f"{model_name}::{text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def load_cached_embedding(
        cache_dir: Path,
        cache_key: str
)->Optional[List[float]]:
    path = cache_dir / f"{cache_key}.pkl"
    if not path.exists():
        return None
    
    with open(path, "rb") as f:
        return pickle.load(f)
    
def save_cached_embedding(
        cache_dir: Path,
        cache_key: str,
        embeddings: List[float]
)->None:
    path = cache_dir / f"{cache_key}.pkl"
    with open(path, "wb") as f:
        pickle.dump(embeddings, f)

def embed_documents(
    documents: List,
    model,
    cache_dir: Path,
    batch_size: int = 16,
    model_name: str = "BAAI/bge-large-en-v1.5"
) -> Dict[str, Any]:
    """
    Input:
      List[Document]

    Output:
      {
        "embeddings": List[List[float]],
        "metadatas": List[dict],
        "metrics": dict
      }
    """

    cache_dir.mkdir(parents=True, exist_ok=True)

    texts = [doc.page_content.strip() for doc in documents]
    metadatas = [doc.metadata for doc in documents]

    embeddings: List[List[float] | None] = [None] * len(texts)
    to_embed = []
    to_embed_indices = []

    # --- cache lookup ---
    for idx, text in enumerate(texts):
        key = get_cache_key(text, model_name)
        cached = load_cached_embedding(cache_dir, key)

        if cached is not None:
            embeddings[idx] = cached
        else:
            to_embed.append(text)
            to_embed_indices.append(idx)

    # --- batch embedding ---
    if to_embed:
        new_embeddings = model.encode(
            to_embed,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        for idx, emb in zip(to_embed_indices, new_embeddings):
            emb = emb.tolist()
            embeddings[idx] = emb

            key = get_cache_key(texts[idx], model_name)
            save_cached_embedding(cache_dir, key, emb)

    # --- metrics ---
    token_counts = [len(t.split()) for t in texts]
    vector_norms = [np.linalg.norm(e) for e in embeddings]

    metrics = {
        "total_chunks": len(texts),
        "avg_tokens_per_chunk": sum(token_counts) / len(token_counts),
        "min_tokens": min(token_counts),
        "max_tokens": max(token_counts),
        "embedding_dim": len(embeddings[0]),
        "avg_vector_norm": float(np.mean(vector_norms)),
        "cache_hit_ratio": 1 - (len(to_embed) / len(texts))
    }

    return {
        "embeddings": embeddings,
        "metadatas": metadatas,
        "metrics": metrics
    }