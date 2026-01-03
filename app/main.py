import os
import traceback
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from pydantic import BaseModel, Field

from .cv_ingest import extract_text_from_pdf, chunk_text, Chunk
from .vector_store import build_faiss_index, save_index, load_index, semantic_search

from .job_parse import extract_requirements
from .schemas import JobAnalyzeReq, JobRequirements

from .agent import run_agent


# -----------------------------
# App + Persistent Index State
# -----------------------------
app = FastAPI(title="CV Cover Letter Agent")

FAISS_INDEX = None
FAISS_META = []

# Load persisted index at startup (if exists)
FAISS_INDEX, FAISS_META = load_index()

# -----------------------------
# Storage
# -----------------------------
DATA_DIR = Path("data")
CV_DIR = DATA_DIR / "cv"
CV_DIR.mkdir(parents=True, exist_ok=True)

# RAM (debug only)
CV_TEXT: Optional[str] = None
CV_CHUNKS: List[Chunk] = []


# -----------------------------
# Health
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# CV Ingest
# -----------------------------
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


# -----------------------------
# CV Search (Semantic)
# -----------------------------
class SearchReq(BaseModel):
    query: str
    top_k: int = 5


@app.post("/cv-search")
def cv_search(req: SearchReq):
    if FAISS_INDEX is None or not FAISS_META:
        raise HTTPException(status_code=400, detail="No CV index found. Upload via /ingest-cv first.")
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
        "first_400_chars": CV_TEXT[:400],
    }


# -----------------------------
# Job Analyze (Requirements JSON)
# -----------------------------
@app.post("/analyze-job", response_model=JobRequirements)
def analyze_job(req: JobAnalyzeReq):
    try:
        # IMPORTANT: default must be a model you actually have access to
        model = req.model or os.getenv("GEMINI_TEXT_MODEL", "gemini-2.0-flash")

        data = extract_requirements(req.job_text, model=model)
        return JobRequirements(**data)

    except Exception as e:
        print("----- /analyze-job ERROR -----")
        traceback.print_exc()
        print("----- END ERROR -----")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Agent: Generate Cover Letter + Fit Score
# -----------------------------
class GenerateReq(BaseModel):
    job_text: str = Field(..., min_length=30)
    requirements: JobRequirements
    model: str | None = None


@app.post("/generate")
def generate(req: GenerateReq):
    try:
        if FAISS_INDEX is None or not FAISS_META:
            raise HTTPException(status_code=400, detail="No CV index found. Upload via /ingest-cv first.")

        model = req.model or os.getenv("GEMINI_TEXT_MODEL", "gemini-2.0-flash")

        result = run_agent(
            job_text=req.job_text,
            req_json=req.requirements.model_dump(),
            faiss_index=FAISS_INDEX,
            faiss_meta=FAISS_META,
            model=model,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        print("----- /generate ERROR -----")
        traceback.print_exc()
        print("----- END ERROR -----")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/generate-from-job-text")
def generate_from_job_text(job_text: str = Body(..., media_type="text/plain")):
    try:
        if FAISS_INDEX is None or not FAISS_META:
            raise HTTPException(status_code=400, detail="No CV index found. Upload via /ingest-cv first.")

        model = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.0-flash")

        # 1) analyze job -> requirements
        reqs = extract_requirements(job_text, model=model)
        reqs_obj = JobRequirements(**reqs)

        # 2) run agent -> cover letter + fit
        result = run_agent(
            job_text=job_text,
            req_json=reqs_obj.model_dump(),
            faiss_index=FAISS_INDEX,
            faiss_meta=FAISS_META,
            model=model,
        )

        return {"requirements": reqs_obj, "result": result}

    except HTTPException:
        raise
    except Exception as e:
        print("----- /generate-from-job-text ERROR -----")
        traceback.print_exc()
        print("----- END ERROR -----")
        raise HTTPException(status_code=500, detail=str(e))

