from __future__ import annotations
from typing import List, Dict, Any
import re
import unicodedata

from .cv_ingest import Chunk


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    return s.lower()


def simple_keyword_search(chunks: List[Chunk], query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    q = _norm(query).strip()
    if not q:
        return []

    # Kelimeleri çıkar (harf/sayı dışını temizle)
    q_words = re.findall(r"[a-z0-9]+", q)

    scored = []
    for c in chunks:
        text_l = _norm(c.text)

        # 1) Direkt substring bonusu (tek kelimede çok iş görüyor)
        base = 3 if q in text_l else 0

        # 2) Kelime eşleşme skoru
        score = base + sum(text_l.count(w) for w in q_words)

        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, c in scored[:top_k]:
        results.append(
            {
                "score": score,
                "chunk_id": c.chunk_id,
                "preview": c.text[:350] + ("..." if len(c.text) > 350 else ""),
                "meta": c.meta,
            }
        )
    return results
