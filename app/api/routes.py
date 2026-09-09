from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import AskRequest, AskResponse
from app.generation.answer_generator import AnswerGenerator
from app.generation.citation_builder import CitationBuilder
from app.retrieval.hybrid_retriever import HybridRetriever

router = APIRouter()

retriever = HybridRetriever()
generator = AnswerGenerator()
citation_builder = CitationBuilder()


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    try:
        evidence = retriever.retrieve(
            payload.question,
            vector_top_k=payload.vector_top_k,
            graph_max_hops=payload.graph_max_hops,
            final_top_k=payload.final_evidence_top_k,
        )
        answer = generator.generate(payload.question, evidence)
        citations = citation_builder.build(evidence)
        return AskResponse(
            question=payload.question,
            answer=answer,
            citations=citations,
            evidence=evidence,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
