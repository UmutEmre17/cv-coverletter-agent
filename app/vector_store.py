from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import faiss
from dotenv import load_dotenv
import os

from google import genai

from .cv_ingest import Chunk

load_dotenv()

DATA_DIR = Path("data")
INDEX_DIR = DATA_DIR / "index"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

FAISS_PATH = INDEX_DIR / "cv.faiss"
META_PATH = INDEX_DIR / "cv_chunks.json"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Returns embeddings as float32 numpy array (N, D)
    """
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)

    # Gemini embeddings: embed_content supports single string or list of strings. :contentReference[oaicite:3]{index=3}
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts
    )

    # result.embeddings: list of embedding objects (vector values inside)
    vectors = []
    for e in result.embeddings:
        # google-genai returns embedding values typically under e.values
        vals = getattr(e, "values", None)
        if vals is None:
            # fallback for older shapes
            vals = e
        vectors.append(vals)

    return np.array(vectors, dtype=np.float32)


def build_faiss_index(chunks: List[Chunk]) -> Tuple[faiss.IndexFlatIP, List[Dict[str, Any]]]:
    texts = [c.text for c in chunks]
    X = embed_texts(texts)

    # cosine similarity: normalize and use inner product
    faiss.normalize_L2(X)

    dim = X.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(X)

    meta = [{"chunk_id": c.chunk_id, "text": c.text, "meta": c.meta} for c in chunks]
    return index, meta


def save_index(index: faiss.Index, meta: List[Dict[str, Any]]) -> None:
    faiss.write_index(index, str(FAISS_PATH))
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def load_index() -> Tuple[faiss.Index | None, List[Dict[str, Any]]]:
    if not FAISS_PATH.exists() or not META_PATH.exists():
        return None, []

    index = faiss.read_index(str(FAISS_PATH))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    return index, meta


def semantic_search(index: faiss.Index, meta: List[Dict[str, Any]], query: str, top_k: int = 5):
    qv = embed_texts([query])
    faiss.normalize_L2(qv)
    D, I = index.search(qv, top_k)

    results = []
    for score, idx in zip(D[0], I[0]):
        if idx == -1:
            continue
        item = meta[idx]
        results.append(
            {
                "score": float(score),
                "chunk_id": item["chunk_id"],
                "text": item["text"],
                "preview": item["text"][:350] + ("..." if len(item["text"]) > 350 else ""),
                "meta": item.get("meta", {}),
            }
        )
    return results
