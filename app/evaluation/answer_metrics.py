from __future__ import annotations

import re
from typing import Iterable


def normalized_token_f1(prediction: str, reference: str) -> float:
    def tokens(text: str):
        return re.findall(r"\w+", text.lower())

    p = tokens(prediction)
    r = tokens(reference)

    if not p or not r:
        return float(p == r)

    p_counts = {}
    r_counts = {}
    for t in p:
        p_counts[t] = p_counts.get(t, 0) + 1
    for t in r:
        r_counts[t] = r_counts.get(t, 0) + 1

    overlap = sum(min(p_counts.get(t, 0), r_counts.get(t, 0)) for t in p_counts)
    if overlap == 0:
        return 0.0

    precision = overlap / len(p)
    recall = overlap / len(r)
    return 2 * precision * recall / (precision + recall)
