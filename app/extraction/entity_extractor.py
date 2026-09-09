from __future__ import annotations

import json
from typing import Dict, List

from app.generation.llm_client import LLMClient


class EntityExtractor:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def extract(self, text: str) -> List[Dict[str, str]]:
        prompt = f"""
Extract named entities from the fictional archive passage below.

Return ONLY valid JSON in this exact shape:
{{
  "entities": [
    {{"name": "...", "type": "PERSON|FACTION|EVENT|PLACE|ARTIFACT|OBJECT|OTHER"}}
  ]
}}

Do not invent entities.

PASSAGE:
{text}
"""
        raw = self.llm.generate(prompt, temperature=0)
        data = self.llm.parse_json(raw)
        return data.get("entities", [])
