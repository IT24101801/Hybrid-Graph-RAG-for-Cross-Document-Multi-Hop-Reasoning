from __future__ import annotations

from typing import Dict, List

from app.graph.graph_repository import GraphRepository
from app.retrieval.query_analyzer import QueryAnalyzer


class GraphRetriever:
    def __init__(
        self,
        repository: GraphRepository | None = None,
        analyzer: QueryAnalyzer | None = None,
    ) -> None:
        self.repository = repository or GraphRepository()
        self.analyzer = analyzer or QueryAnalyzer()

    def retrieve(self, query: str, max_hops: int = 3) -> List[Dict]:
        analysis = self.analyzer.analyze(query)
        if not analysis.candidate_entities:
            return []

        matched = self.repository.search_entities(analysis.candidate_entities)
        names = [x["name"] for x in matched]

        if not names:
            return []

        return self.repository.multi_hop_paths(
            names,
            max_hops=max_hops,
        )
