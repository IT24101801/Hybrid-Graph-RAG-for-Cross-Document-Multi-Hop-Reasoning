from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    vector_top_k: int = 10
    graph_max_hops: int = 3
    final_evidence_top_k: int = 8


class Citation(BaseModel):
    marker: str
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    file_name: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    source_type: Optional[str] = None


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    evidence: List[Dict[str, Any]]
