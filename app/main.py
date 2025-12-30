from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional

from .cv_ingest import extract_text_from_pdf, chunk_text, Chunk
from .search_demo import simple_keyword_search

app = FastAPI(title="CV Cover Letter Agent")

DATA_DIR = Path("data")
CV_DIR = DATA_DIR / "cv"
CV_DIR.mkdir(parents=True, exist_ok=True)

# RAM'de tutacağız (MVP)
CV_TEXT: Optional[str] = None
CV_CHUNKS: List[Chunk] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest-cv")
async def ingest_cv(file: UploadFile = File(...)):
    global CV_TEXT, CV_CHUNKS

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    save_path = CV_DIR / "cv.pdf"
    content = await file.read()
    save_path.write_bytes(content)

    text = extract_text_from_pdf(str(save_path))
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    chunks = chunk_text(text, max_chars=1200, overlap=150)

    CV_TEXT = text
    CV_CHUNKS = chunks

    return {
        "message": "CV ingested successfully",
        "chars": len(text),
        "chunks": len(chunks),
    }


class SearchReq(BaseModel):
    query: str
    top_k: int = 5


@app.post("/cv-search")
def cv_search(req: SearchReq):
    if not CV_CHUNKS:
        raise HTTPException(status_code=400, detail="No CV ingested yet. Upload via /ingest-cv first.")

    results = simple_keyword_search(CV_CHUNKS, req.query, top_k=req.top_k)
    return {"query": req.query, "results": results}

@app.get("/debug/cv-state")
def debug_cv_state():
    if not CV_TEXT or not CV_CHUNKS:
        return {"has_text": bool(CV_TEXT), "chunks": len(CV_CHUNKS), "note": "Upload CV again."}

    full = CV_TEXT.lower()
    return {
        "chars": len(CV_TEXT),
        "chunks": len(CV_CHUNKS),
        "contains_laravel_in_full_text": ("laravel" in full),
        "contains_php_in_full_text": ("php" in full),
        "first_400_chars": CV_TEXT[:400]
    }
