from __future__ import annotations

import os
import time
from typing import Iterable, List

import requests


class VoyageEmbedder:
    """Voyage AI embedding client with simple retry/backoff."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://api.voyageai.com/v1/embeddings",
        timeout: int = 60,
        max_retries: int = 5,
    ) -> None:
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        self.model = model or os.getenv("EMBEDDING_MODEL", "voyage-4-lite")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("VOYAGE_API_KEY is not configured.")

    def _embed_batch(self, texts: List[str], input_type: str) -> List[List[float]]:
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": input_type,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code == 429:
                    raise requests.HTTPError("Rate limited", response=response)
                response.raise_for_status()
                data = response.json()["data"]
                return [item["embedding"] for item in data]
            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)

        raise RuntimeError("Embedding request failed unexpectedly.")

    def embed_documents(self, texts: Iterable[str], batch_size: int = 64) -> List[List[float]]:
        texts = list(texts)
        result: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            result.extend(self._embed_batch(texts[i : i + batch_size], "document"))
        return result

    def embed_query(self, text: str) -> List[float]:
        return self._embed_batch([text], "query")[0]
