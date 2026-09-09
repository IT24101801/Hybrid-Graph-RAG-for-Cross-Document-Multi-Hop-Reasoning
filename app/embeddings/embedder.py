from __future__ import annotations

import os
from typing import Iterable, List

from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


load_dotenv()


class HuggingFaceEmbedder:
    """Local Hugging Face embedding client using BGE."""

    def __init__(
        self,
        model_name: str | None = None,
    ) -> None:

        self.model_name = (
            model_name
            or os.getenv(
                "EMBEDDING_MODEL",
                "BAAI/bge-small-en-v1.5",
            )
        )

        print(
            f"[Embeddings] Loading local model: "
            f"{self.model_name}"
        )

        self.model = SentenceTransformer(
            self.model_name
        )

        print("[Embeddings] Model loaded successfully.")

    def embed_documents(
        self,
        texts: Iterable[str],
        batch_size: int = 64,
    ) -> List[List[float]]:

        texts = list(texts)

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        text: str,
    ) -> List[float]:

        if not text.strip():
            raise ValueError(
                "Query text cannot be empty."
            )

        # BGE retrieval models benefit from a retrieval
        # instruction on the query side.
        query = (
            "Represent this sentence for searching "
            "relevant passages: "
            + text
        )

        embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        return embedding.tolist()