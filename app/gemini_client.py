from __future__ import annotations

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in environment/.env")

client = genai.Client(api_key=API_KEY)


def generate_text(model: str, prompt: str) -> str:
    """
    Returns plain text from Gemini response, handling multiple SDK response shapes.
    Raises a clear error if no text is available.
    """
    resp = client.models.generate_content(
        model=model,
        contents=prompt
    )

    # 1) Most convenient field (may be empty sometimes)
    txt = getattr(resp, "text", None)
    if txt:
        return txt.strip()

    # 2) Fallback: candidates/parts
    try:
        cand0 = resp.candidates[0]
        content = getattr(cand0, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts and len(parts) > 0:
            part0 = parts[0]
            part_txt = getattr(part0, "text", None)
            if part_txt:
                return part_txt.strip()
    except Exception:
        pass

    # 3) Last resort: stringify for debugging
    raise RuntimeError(f"Gemini returned no text. Raw response: {resp!r}")
