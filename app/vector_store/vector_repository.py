from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from app.embeddings.embedder import HuggingFaceEmbedder
from app.vector_store.chroma_client import get_chroma_collection


class VectorRepository:
    def __init__(self, embedder: HuggingFaceEmbedder | None = None) -> None:
        self.collection = get_chroma_collection()
        self.embedder = embedder or HuggingFaceEmbedder()

    @staticmethod
    def _chunk_text(chunk: Any) -> str:
        return getattr(chunk, "text", None) or getattr(chunk, "content", None) or str(chunk)

    @staticmethod
    def _chunk_id(chunk: Any) -> str:
        return getattr(chunk, "chunk_id", None) or getattr(getattr(chunk, "metadata", None), "chunk_id", None)

    @staticmethod
    def _metadata(chunk: Any) -> Dict[str, Any]:
        md = getattr(chunk, "metadata", None)
        if md is None:
            return {}
        if hasattr(md, "model_dump"):
            raw = md.model_dump()
        elif hasattr(md, "dict"):
            raw = md.dict()
        elif isinstance(md, dict):
            raw = md
        else:
            raw = vars(md)

        # Chroma metadata values must be primitive scalar values.
        return {
            str(k): v
            for k, v in raw.items()
            if isinstance(v, (str, int, float, bool)) and v is not None
        }

    def add_chunks(self, chunks: Sequence[Any], batch_size: int = 64) -> int:
        if not chunks:
            return 0

        for start in range(0, len(chunks), batch_size):
            batch = list(chunks[start : start + batch_size])
            documents = [self._chunk_text(c) for c in batch]
            ids = [self._chunk_id(c) for c in batch]

            if any(not i for i in ids):
                raise ValueError("Every chunk must contain a stable chunk_id.")

            embeddings = self.embedder.embed_documents(documents, batch_size=batch_size)
            metadatas = [self._metadata(c) for c in batch]

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

        return len(chunks)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        query_embedding = self.embedder.embed_query(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        hits: List[Dict[str, Any]] = []
        for i, chunk_id in enumerate(result["ids"][0]):
            distance = result["distances"][0][i]
            hits.append(
                {
                    "chunk_id": chunk_id,
                    "text": result["documents"][0][i],
                    "metadata": result["metadatas"][0][i] or {},
                    "distance": distance,
                    "score": 1.0 - float(distance),
                }
            )
        return hits
