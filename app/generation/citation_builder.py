from __future__ import annotations

from typing import Dict, Iterable, List


class CitationBuilder:
    def build(self, evidence: Iterable[Dict]) -> List[Dict]:
        citations = []
        for i, item in enumerate(evidence, start=1):
            md = item.get("metadata", {})
            citations.append(
                {
                    "marker": f"E{i}",
                    "chunk_id": item.get("chunk_id") or md.get("chunk_id"),
                    "document_id": item.get("document_id") or md.get("document_id"),
                    "file_name": item.get("file_name") or md.get("file_name"),
                    "page": item.get("page") or md.get("page"),
                    "section": item.get("section") or md.get("section"),
                    "source_type": item.get("source_type") or md.get("source_type"),
                }
            )
        return citations
