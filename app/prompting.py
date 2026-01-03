from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict

from .gemini_client import generate_text


def render_prompt(path: str, **kwargs) -> str:
    template = Path(path).read_text(encoding="utf-8")
    for k, v in kwargs.items():
        template = template.replace(f"{{{{{k}}}}}", v)
    return template


def call_json(model: str, prompt: str) -> Dict[str, Any]:
    raw = generate_text(model=model, prompt=prompt)

    # extract JSON object
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in model output:\n{raw}")

    json_text = raw[start:end + 1]
    return json.loads(json_text)
