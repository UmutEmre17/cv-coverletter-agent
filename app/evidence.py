from __future__ import annotations

from typing import List, Dict, Any
from .vector_store import semantic_search


def build_evidence(index, meta: List[Dict[str, Any]], queries: List[str], top_k_each: int = 3, max_total: int = 10):
    """
    Run multiple semantic searches and dedupe by chunk_id.
    """
    seen = set()
    collected = []

    for q in queries:
        results = semantic_search(index, meta, q, top_k=top_k_each)
        for r in results:
            cid = r["chunk_id"]
            if cid in seen:
                continue
            seen.add(cid)
            collected.append(r)
            if len(collected) >= max_total:
                return collected

    return collected


def format_evidence(evidence_items: List[Dict[str, Any]]) -> str:
    """
    Format evidence as a text block for the LLM prompts.
    """
    lines = []
    for item in evidence_items:
        lines.append(f"- [{item['chunk_id']}] {item['text']}")
    return "\n".join(lines)
