from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scripts.ask_hybrid import (
    extract_seed_entity,
    hybrid_retrieve,
    build_context,
    build_prompt,
)

from app.generation.llm_client import LLMClient


app = FastAPI(
    title="AshenGraph API",
    description="Hybrid Graph RAG for cross-document multi-hop reasoning",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    seed_entity: str
    answer: str
    evidence_count: int


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AshenGraph",
    }


@app.post(
    "/ask",
    response_model=AskResponse,
)
def ask(request: AskRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        seed_entity = extract_seed_entity(
            question
        )

        (
            graph_neighbors,
            expansion_entities,
            results,
        ) = hybrid_retrieve(
            question=question,
            seed_entity=seed_entity,
            top_k=10,
        )

        if not results:
            raise HTTPException(
                status_code=404,
                detail="No supporting evidence found.",
            )

        context = build_context(
            results,
            max_items=15,
        )

        prompt = build_prompt(
            question=question,
            seed_entity=seed_entity,
            graph_neighbors=graph_neighbors,
            evidence_context=context,
        )

        llm = LLMClient()

        answer = llm.generate(
            prompt
        )

        return AskResponse(
            question=question,
            seed_entity=seed_entity,
            answer=answer,
            evidence_count=min(
                len(results),
                15,
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )