from __future__ import annotations

from typing import Dict, List

from app.vector_store.vector_repository import VectorRepository


class VectorRetriever:
    def __init__(self, repository: VectorRepository | None = None) -> None:
        self.repository = repository or VectorRepository()

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict]:
        return self.repository.search(query, top_k=top_k)
