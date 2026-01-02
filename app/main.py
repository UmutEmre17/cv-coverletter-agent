import os
from .job_parse import extract_requirements
from .schemas import JobAnalyzeReq, JobRequirements
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
from fastapi import HTTPException
import traceback
from .cv_ingest import extract_text_from_pdf, chunk_text, Chunk
from .vector_store import build_faiss_index, save_index, load_index, semantic_search

FAISS_INDEX = None
FAISS_META = []

app = FastAPI(title="CV Cover Letter Agent")
FAISS_INDEX, FAISS_META = load_index()

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
    global CV_TEXT, CV_CHUNKS, FAISS_INDEX, FAISS_META

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    save_path = CV_DIR / "cv.pdf"
    content = await file.read()
    save_path.write_bytes(content)

    text = extract_text_from_pdf(str(save_path))
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    chunks = chunk_text(text, max_chars=1200, overlap=150)

    FAISS_INDEX, FAISS_META = build_faiss_index(chunks)
    save_index(FAISS_INDEX, FAISS_META)

    CV_TEXT = text
    CV_CHUNKS = chunks

    return {
        "message": "CV ingested successfully",
        "chars": len(text),
        "chunks": len(chunks),
        "indexed": True,
    }


class SearchReq(BaseModel):
    query: str
    top_k: int = 5


@app.post("/cv-search")
def cv_search(req: SearchReq):
    if FAISS_INDEX is None or not FAISS_META:
        raise HTTPException(status_code=400, detail="No FAISS index found. Upload via /ingest-cv first.")

    results = semantic_search(FAISS_INDEX, FAISS_META, req.query, top_k=req.top_k)
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

@app.post("/analyze-job", response_model=JobRequirements)
def analyze_job(req: JobAnalyzeReq):
    try:
        model = req.model or os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")
        data = extract_requirements(req.job_text, model=model)
        return JobRequirements(**data)
    except Exception as e:
        # terminale detay bas
        print("----- /analyze-job ERROR -----")
        traceback.print_exc()
        print("----- END ERROR -----")
        # swagger'a da detay dön
        raise HTTPException(status_code=500, detail=str(e))
