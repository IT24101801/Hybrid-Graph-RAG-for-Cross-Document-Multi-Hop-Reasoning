from __future__ import annotations

from typing import Dict, Iterable


class ContextBuilder:
    def build(self, evidence: Iterable[Dict]) -> str:
        blocks = []
        for i, item in enumerate(evidence, start=1):
            md = item.get("metadata", {})
            chunk_id = item.get("chunk_id") or md.get("chunk_id", "unknown")
            file_name = item.get("file_name") or md.get("file_name", "unknown")
            page = item.get("page") or md.get("page")
            source_type = item.get("source_type") or md.get("source_type", "unknown")

            source = f"{file_name}"
            if page is not None:
                source += f", page {page}"

            blocks.append(
                f"[E{i}] chunk_id={chunk_id}; source={source}; source_type={source_type}\n"
                f"{item.get('text', '')}"
            )
        return "\n\n".join(blocks)
