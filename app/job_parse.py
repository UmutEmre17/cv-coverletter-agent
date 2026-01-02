from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .gemini_client import generate_text


PROMPT_PATH = Path("app/prompts/extract_requirements.md")


def _load_prompt(job_text: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.replace("{{JOB_TEXT}}", job_text)


def _extract_json_block(text: str) -> str:
    """
    Robustly extract the first JSON object found in a model output.
    Handles cases where the model adds explanations or markdown.
    """
    if not text:
        raise ValueError("Empty response from Gemini.")

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in Gemini output:\n{text}")

    return text[start:end + 1]


def extract_requirements(job_text: str, model: str) -> Dict[str, Any]:
    """
    Call Gemini to extract structured job requirements and return parsed JSON.
    """
    prompt = _load_prompt(job_text)

    raw = generate_text(model=model, prompt=prompt)

    # --- DEBUG (istersen aç)
    # print("----- GEMINI RAW OUTPUT -----")
    # print(raw)
    # print("----- END -----")

    json_text = _extract_json_block(raw)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON from Gemini output.\n"
            f"Extracted JSON:\n{json_text}\n\n"
            f"Original output:\n{raw}"
        ) from e
