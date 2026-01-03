from __future__ import annotations

import os
import json
from typing import Dict, Any

from .prompting import render_prompt, call_json
from .evidence import build_evidence, format_evidence


PROMPT_QUERIES = "app/prompts/evidence_query.md"
PROMPT_DRAFT = "app/prompts/cover_letter_draft.md"
PROMPT_CRITIQUE = "app/prompts/cover_letter_critique.md"
PROMPT_FIT = "app/prompts/fit_score.md"


def run_agent(
    *,
    job_text: str,
    req_json: Dict[str, Any],
    faiss_index,
    faiss_meta,
    model: str | None = None,
) -> Dict[str, Any]:
    text_model = model or os.getenv("GEMINI_TEXT_MODEL", "gemini-1.0-pro")

    req_str = json.dumps(req_json, ensure_ascii=False, indent=2)

    # 1) build evidence queries
    q_prompt = render_prompt(PROMPT_QUERIES, REQ_JSON=req_str)
    q_data = call_json(text_model, q_prompt)
    queries = q_data.get("queries", [])
    if not queries:
        # fallback
        queries = req_json.get("must_have", [])[:5]

    # 2) retrieve evidence
    evidence_items = build_evidence(faiss_index, faiss_meta, queries, top_k_each=3, max_total=10)
    evidence_text = format_evidence(evidence_items)

    # 3) draft cover letter
    draft_prompt = render_prompt(PROMPT_DRAFT, REQ_JSON=req_str, JOB_TEXT=job_text, EVIDENCE=evidence_text)
    draft_data = call_json(text_model, draft_prompt)

    draft_letter = draft_data.get("cover_letter", "")
    draft_map = draft_data.get("evidence_map", [])
    assumptions = draft_data.get("assumptions", [])

    # 4) critique + rewrite
    crit_prompt = render_prompt(PROMPT_CRITIQUE, REQ_JSON=req_str, DRAFT=draft_letter, EVIDENCE=evidence_text)
    crit_data = call_json(text_model, crit_prompt)

    final_letter = crit_data.get("final_cover_letter", "")
    final_map = crit_data.get("evidence_map", [])
    issues = crit_data.get("issues", [])
    improvements = crit_data.get("improvements", [])

    # 5) fit score
    fit_prompt = render_prompt(PROMPT_FIT, REQ_JSON=req_str, EVIDENCE=evidence_text)
    fit_data = call_json(text_model, fit_prompt)

    return {
        "queries": queries,
        "evidence": evidence_items,
        "draft": {
            "cover_letter": draft_letter,
            "evidence_map": draft_map,
            "assumptions": assumptions,
        },
        "final": {
            "cover_letter": final_letter,
            "evidence_map": final_map,
            "issues": issues,
            "improvements": improvements,
        },
        "fit": fit_data,
    }
