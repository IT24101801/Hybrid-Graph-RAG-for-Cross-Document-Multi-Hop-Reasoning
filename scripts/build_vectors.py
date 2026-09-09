from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.vector_store.vector_repository import VectorRepository


def _as_chunk(item):
    metadata = SimpleNamespace(**item.get("metadata", {}))
    return SimpleNamespace(
        text=item.get("text") or item.get("content", ""),
        chunk_id=item.get("chunk_id") or item.get("metadata", {}).get("chunk_id"),
        metadata=metadata,
    )


def main() -> None:
    chunks_path = Path("data/processed/chunks/chunks.json")
    if not chunks_path.exists():
        raise FileNotFoundError(
            f"{chunks_path} not found. Export your processed chunks to this JSON file first."
        )

    data = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = [_as_chunk(item) for item in data]

    repo = VectorRepository()
    count = repo.add_chunks(chunks)
    print(f"Indexed {count} chunks into ChromaDB.")


if __name__ == "__main__":
    main()
