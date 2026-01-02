from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List


class JobAnalyzeReq(BaseModel):
    job_text: str = Field(..., min_length=30)
    model: str | None = None


class JobRequirements(BaseModel):
    title: str = ""
    company: str = ""
    seniority: str = ""
    location_type: str = ""
    must_have: List[str] = []
    nice_to_have: List[str] = []
    responsibilities: List[str] = []
    keywords: List[str] = []
