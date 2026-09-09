from __future__ import annotations

import os
import chromadb
from chromadb.api.models.Collection import Collection


def get_chroma_collection() -> Collection:
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "ashen_era_chunks")

    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
