from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple


class ConflictDetector:
    """
    Lightweight contradiction detector.

    It flags cases where the same (subject, predicate) points to multiple objects.
    This is intentionally conservative and should be treated as a review signal,
    not proof that one source is false.
    """

    def detect(self, claims: Iterable[Dict]) -> List[Dict]:
        groups = defaultdict(list)
        for claim in claims:
            key = (claim.get("subject"), claim.get("predicate"))
            groups[key].append(claim)

        conflicts = []
        for (subject, predicate), items in groups.items():
            objects = {x.get("object") for x in items}
            if len(objects) > 1:
                conflicts.append(
                    {
                        "subject": subject,
                        "predicate": predicate,
                        "objects": sorted(x for x in objects if x is not None),
                        "claims": items,
                    }
                )
        return conflicts
