from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path

from pypdf import PdfReader

@dataclass
class Chunk:
    chunk_id: str
    text: str
    meta: Dict[str, Any]

def extract_text_from_pdf(pdf_path: str) -> srt:
    """
    Read a PDF from disk and return extracted text.
    """
    reader = PdfReader(pdf_path)
    pages_text: List[str] = []

    for i, page in enumerate(reader.pages):
        t = page.extract_text() or ""
        t = t.replace("\x00", " ").strip()
        if t:
            pages_text.append(f"[PAGE {i+1}]\n{t}")
    
    return "\n\n".join(pages_text).strip()

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[Chunk]:
    """
    Simple character-based chunking (good enough for MVP).
    Later we can upgrade to token-based chunking.
    """
    if not text:
        return[]
    
    chunks: List[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(
                Chunk(
                    chunk_id=f"chunk_{idx}",
                    text=chunk,
                    meta={"start": start, "end": end},
                )
            )
            idx += 1
        start = end - overlap
        if start < 0:
            start = 0
        if end == len(text):
            break

    return chunks