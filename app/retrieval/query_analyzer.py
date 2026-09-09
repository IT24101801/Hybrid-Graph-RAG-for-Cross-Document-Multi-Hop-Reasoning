from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class QueryAnalysis:
    original_query: str
    candidate_entities: List[str]


class QueryAnalyzer:
    """Cheap candidate-entity extractor used before graph lookup."""

    def analyze(self, query: str) -> QueryAnalysis:
        # Captures capitalized phrases as graph seed candidates.
        candidates = re.findall(
            r"\b(?:[A-Z][\w'-]*)(?:\s+[A-Z][\w'-]*)*\b",
            query,
        )
        seen = []
        for item in candidates:
            if item not in seen:
                seen.append(item)
        return QueryAnalysis(query, seen)
