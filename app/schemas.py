from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class JobAnalyzeReq(BaseModel):
    job_text: str = Field(..., min_length=30)
    model: str | None = None


class JobRequirements(BaseModel):
    title: str = ""
    company: str = ""
    seniority: Optional[str] = ""     
    location_type: Optional[str] = ""  
    must_have: List[str] = []
    nice_to_have: List[str] = []
    responsibilities: List[str] = []
    keywords: List[str] = []
