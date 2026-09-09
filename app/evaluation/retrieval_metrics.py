from __future__ import annotations

from typing import Iterable, Sequence, Set


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    relevant: Set[str] = set(relevant_ids)
    if not relevant:
        return 0.0
    return len(set(retrieved_ids[:k]) & relevant) / len(relevant)


def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    if k <= 0:
        return 0.0
    relevant = set(relevant_ids)
    hits = len(set(retrieved_ids[:k]) & relevant)
    return hits / min(k, len(retrieved_ids)) if retrieved_ids else 0.0


def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Iterable[str]) -> float:
    relevant = set(relevant_ids)
    for i, item in enumerate(retrieved_ids, start=1):
        if item in relevant:
            return 1.0 / i
    return 0.0
