from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable, List


def normalize_entity_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


class EntityResolver:
    def __init__(self, threshold: float = 0.93) -> None:
        self.threshold = threshold

    def best_match(self, name: str, candidates: Iterable[str]) -> str:
        normalized = normalize_entity_name(name)
        best = name
        best_score = 0.0

        for candidate in candidates:
            score = SequenceMatcher(
                None, normalized, normalize_entity_name(candidate)
            ).ratio()
            if score > best_score:
                best = candidate
                best_score = score

        return best if best_score >= self.threshold else name
