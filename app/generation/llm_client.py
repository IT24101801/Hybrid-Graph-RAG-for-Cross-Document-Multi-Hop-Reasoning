from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict

import requests


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 90,
        max_retries: int = 5,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.model = model or os.getenv("LLM_MODEL")
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")
        if not self.model:
            raise ValueError("LLM_MODEL is not configured.")

    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code == 429:
                    raise requests.HTTPError("Rate limited", response=response)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)

        raise RuntimeError("LLM request failed unexpectedly.")

    @staticmethod
    def parse_json(text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.S)
            if not match:
                raise
            return json.loads(match.group(0))
