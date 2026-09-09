from __future__ import annotations

from typing import Dict, Iterable, List


DEFAULT_SOURCE_AUTHORITY = {
    "official_codex": 1.00,
    "chronicle": 0.90,
    "wiki": 0.80,
    "ephemera": 0.65,
    "unknown": 0.50,
}


class EvidenceRanker:
    def __init__(self, source_authority: Dict[str, float] | None = None) -> None:
        self.source_authority = source_authority or DEFAULT_SOURCE_AUTHORITY

    def rank(self, evidence: Iterable[Dict], top_k: int = 8) -> List[Dict]:
        ranked = []
        for item in evidence:
            source_type = item.get("source_type") or item.get("metadata", {}).get("source_type", "unknown")
            authority = self.source_authority.get(source_type, 0.5)
            retrieval_score = float(item.get("score", 0.5))

            copy = dict(item)
            copy["authority_score"] = authority
            copy["final_score"] = 0.75 * retrieval_score + 0.25 * authority
            ranked.append(copy)

        ranked.sort(key=lambda x: x["final_score"], reverse=True)
        return ranked[:top_k]
