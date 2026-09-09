from __future__ import annotations

from typing import Dict, List


class MultiHopReasoner:
    """Produces a concise textual representation of retrieved graph paths."""

    def summarize_paths(self, paths: List[Dict]) -> List[str]:
        summaries: List[str] = []
        for path in paths:
            nodes = path.get("nodes", [])
            rels = path.get("relationships", [])
            pieces = []
            for i, rel in enumerate(rels):
                if i + 1 >= len(nodes):
                    break
                pieces.append(
                    f"{nodes[i]} -[{rel.get('predicate', 'RELATED_TO')}]-> {nodes[i + 1]}"
                )
            if pieces:
                summaries.append(" | ".join(pieces))
        return summaries
