from __future__ import annotations

from typing import Dict, List

from app.generation.llm_client import LLMClient


class RelationExtractor:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def extract(self, text: str) -> List[Dict[str, str]]:
        prompt = f"""
Extract explicit relationships from the fictional archive passage.

Return ONLY JSON:
{{
  "relations": [
    {{
      "subject": "...",
      "predicate": "UPPER_SNAKE_CASE",
      "object": "...",
      "evidence": "short supporting phrase"
    }}
  ]
}}

Rules:
- Only extract relationships supported by the passage.
- Keep subject/object names close to the source wording.
- Do not infer unsupported facts.

PASSAGE:
{text}
"""
        raw = self.llm.generate(prompt, temperature=0)
        data = self.llm.parse_json(raw)
        return data.get("relations", [])
