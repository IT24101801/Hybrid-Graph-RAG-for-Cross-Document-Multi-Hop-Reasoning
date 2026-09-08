"""
app/processing/metadata.py

Metadata models and helpers for AshenGraph.

Responsibilities:
- Define a normalized chunk representation
- Preserve provenance from the source document
- Create stable chunk IDs
- Convert chunk objects into dictionaries suitable for:
  - ChromaDB metadata
  - JSON serialization
  - debugging
  - evaluation

This module does not perform text cleaning or chunk splitting.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ChunkMetadata:
    """
    Provenance and structural metadata attached to a chunk.

    Keeping this metadata consistent is especially important for
    Sub-track 1B because evidence from multiple documents will later
    be connected through vector and graph retrieval.
    """

    document_id: str
    chunk_id: str

    file_name: str
    file_path: str

    source_type: str

    page: int | None = None
    section: str | None = None
    chapter: str | None = None

    chunk_index: int = 0

    start_char: int | None = None
    end_char: int | None = None

    extraction_method: str | None = None
    extraction_confidence: float | None = None

    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class TextChunk:
    """
    Normalized text chunk used by downstream components.

    This will later be:
    - embedded and stored in ChromaDB
    - linked to graph claims
    - retrieved as evidence
    - passed to the LLM
    """

    chunk_id: str
    document_id: str

    text: str

    metadata: ChunkMetadata

    @property
    def is_empty(self) -> bool:
        return not bool(self.text.strip())

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


def generate_chunk_id(
    document_id: str,
    chunk_index: int,
    text: str | None = None,
) -> str:
    """
    Generate a deterministic chunk ID.

    Example:
        doc_a82f91_chunk_0007_d04a9c

    The text hash helps detect content changes while keeping the
    chunk ID readable.
    """

    base = f"{document_id}:{chunk_index}"

    if text:
        digest = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()[:6]
    else:
        digest = "000000"

    return (
        f"{document_id}_chunk_"
        f"{chunk_index:04d}_"
        f"{digest}"
    )


def chunk_to_dict(
    chunk: TextChunk,
) -> dict[str, Any]:
    """
    Convert TextChunk into a JSON-serializable dictionary.
    """

    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "text": chunk.text,
        "char_count": chunk.char_count,
        "word_count": chunk.word_count,
        "metadata": asdict(chunk.metadata),
    }


def chunk_to_flat_dict(
    chunk: TextChunk,
) -> dict[str, Any]:
    """
    Flatten chunk metadata into a single dictionary.

    Useful when saving processed chunks as JSONL/CSV.
    """

    metadata = asdict(chunk.metadata)

    extra = metadata.pop("extra", {})

    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "text": chunk.text,
        "char_count": chunk.char_count,
        "word_count": chunk.word_count,
        **metadata,
        **extra,
    }


def chunk_to_chroma_metadata(
    chunk: TextChunk,
) -> dict[str, Any]:
    """
    Convert chunk metadata into a Chroma-compatible dictionary.

    Chroma metadata values should stay simple:
    str, int, float, or bool.

    None values and nested dictionaries are omitted.
    """

    metadata = chunk.metadata

    result: dict[str, Any] = {
        "document_id": metadata.document_id,
        "chunk_id": metadata.chunk_id,
        "file_name": metadata.file_name,
        "file_path": metadata.file_path,
        "source_type": metadata.source_type,
        "chunk_index": metadata.chunk_index,
    }

    if metadata.page is not None:
        result["page"] = metadata.page

    if metadata.section:
        result["section"] = metadata.section

    if metadata.chapter:
        result["chapter"] = metadata.chapter

    if metadata.start_char is not None:
        result["start_char"] = metadata.start_char

    if metadata.end_char is not None:
        result["end_char"] = metadata.end_char

    if metadata.extraction_method:
        result["extraction_method"] = (
            metadata.extraction_method
        )

    if metadata.extraction_confidence is not None:
        result["extraction_confidence"] = (
            metadata.extraction_confidence
        )

    # Only include simple extra values.
    for key, value in metadata.extra.items():
        if isinstance(
            value,
            (str, int, float, bool),
        ):
            result[key] = value

    return result