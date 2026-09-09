from __future__ import annotations

from typing import Dict, List

from app.retrieval.vector_retriever import VectorRetriever
from app.retrieval.graph_retriever import GraphRetriever
from app.retrieval.evidence_ranker import EvidenceRanker


class HybridRetriever:
    def __init__(
        self,
        vector_retriever: VectorRetriever | None = None,
        graph_retriever: GraphRetriever | None = None,
        ranker: EvidenceRanker | None = None,
    ) -> None:
        self.vector = vector_retriever or VectorRetriever()
        self.graph = graph_retriever or GraphRetriever()
        self.ranker = ranker or EvidenceRanker()

    @staticmethod
    def _graph_to_evidence(paths: List[Dict]) -> List[Dict]:
        evidence = []
        for path in paths:
            hops = max(path.get("hops", 1), 1)
            graph_score = 1.0 / hops
            for rel in path.get("relationships", []):
                if not rel.get("evidence"):
                    continue
                evidence.append(
                    {
                        "kind": "graph",
                        "text": rel["evidence"],
                        "chunk_id": rel.get("chunk_id"),
                        "document_id": rel.get("document_id"),
                        "source_type": rel.get("source_type"),
                        "predicate": rel.get("predicate"),
                        "score": graph_score,
                    }
                )
        return evidence

    def retrieve(
        self,
        query: str,
        vector_top_k: int = 10,
        graph_max_hops: int = 3,
        final_top_k: int = 8,
    ) -> List[Dict]:
        vector_hits = self.vector.retrieve(query, top_k=vector_top_k)
        for hit in vector_hits:
            hit["kind"] = "vector"

        graph_paths = self.graph.retrieve(query, max_hops=graph_max_hops)
        graph_evidence = self._graph_to_evidence(graph_paths)

        dedup = {}
        for item in vector_hits + graph_evidence:
            key = item.get("chunk_id") or item.get("text", "")
            if key not in dedup or item.get("score", 0) > dedup[key].get("score", 0):
                dedup[key] = item

        return self.ranker.rank(dedup.values(), top_k=final_top_k)
