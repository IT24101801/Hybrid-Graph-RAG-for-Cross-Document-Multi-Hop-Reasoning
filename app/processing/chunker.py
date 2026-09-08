"""
app/processing/chunker.py

Provenance-aware text chunker for AshenGraph.

Responsibilities:
- Convert LoadedDocument objects into TextChunk objects
- Preserve page, chapter, section, and source metadata
- Split large units into overlapping chunks
- Generate stable chunk IDs
- Avoid mixing unrelated documents or pages unnecessarily

This is designed for the Sub-track 1B Hybrid Graph RAG pipeline.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable

from app.ingestion.loader import (
    LoadedDocument,
    LoadedPage,
)
from app.processing.cleaner import clean_text
from app.processing.metadata import (
    ChunkMetadata,
    TextChunk,
    generate_chunk_id,
)


logger = logging.getLogger(__name__)


DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_MIN_CHUNK_SIZE = 100


SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+"
)


def split_into_sentences(
    text: str,
) -> list[str]:
    """
    Lightweight sentence splitter.

    This avoids adding a heavy NLP dependency at the chunking stage.
    """

    text = text.strip()

    if not text:
        return []

    sentences = SENTENCE_SPLIT_RE.split(
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def _fallback_character_chunks(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[tuple[str, int, int]]:
    """
    Fall back to character-based splitting when sentence-level
    splitting cannot create reasonable chunks.

    Returns:
        [(chunk_text, start_char, end_char), ...]
    """

    results: list[
        tuple[str, int, int]
    ] = []

    if not text:
        return results

    step = max(
        chunk_size - chunk_overlap,
        1,
    )

    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[start:end].strip()

        if chunk:
            results.append(
                (
                    chunk,
                    start,
                    end,
                )
            )

        if end >= len(text):
            break

        start += step

    return results


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
) -> list[tuple[str, int, int]]:
    """
    Split text into overlapping chunks while preferring sentence
    boundaries.

    Parameters
    ----------
    chunk_size:
        Approximate maximum characters per chunk.

    chunk_overlap:
        Approximate overlap between adjacent chunks.

    min_chunk_size:
        Very small trailing chunks are merged with the previous chunk.

    Returns
    -------
    list of:
        (chunk_text, start_char, end_char)
    """

    text = clean_text(
        text
    )

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero"
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative"
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    if len(text) <= chunk_size:
        return [
            (
                text,
                0,
                len(text),
            )
        ]

    sentences = split_into_sentences(
        text
    )

    if len(sentences) <= 1:
        return _fallback_character_chunks(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    chunks: list[
        tuple[str, int, int]
    ] = []

    current_sentences: list[str] = []

    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        projected_length = (
            current_length
            + sentence_length
            + (
                1
                if current_sentences
                else 0
            )
        )

        if (
            current_sentences
            and projected_length > chunk_size
        ):
            chunk_text = " ".join(
                current_sentences
            ).strip()

            start_char = text.find(
                chunk_text
            )

            if start_char < 0:
                start_char = 0

            end_char = (
                start_char
                + len(chunk_text)
            )

            chunks.append(
                (
                    chunk_text,
                    start_char,
                    end_char,
                )
            )

            # -----------------------------
            # Build overlap from the end
            # -----------------------------
            overlap_sentences: list[str] = []
            overlap_length = 0

            for old_sentence in reversed(
                current_sentences
            ):
                candidate_length = (
                    overlap_length
                    + len(old_sentence)
                    + (
                        1
                        if overlap_sentences
                        else 0
                    )
                )

                if (
                    candidate_length
                    > chunk_overlap
                ):
                    break

                overlap_sentences.insert(
                    0,
                    old_sentence,
                )

                overlap_length = (
                    candidate_length
                )

            current_sentences = (
                overlap_sentences
            )

            current_length = len(
                " ".join(
                    current_sentences
                )
            )

        current_sentences.append(
            sentence
        )

        current_length = len(
            " ".join(
                current_sentences
            )
        )

    if current_sentences:
        chunk_text = " ".join(
            current_sentences
        ).strip()

        start_char = text.rfind(
            chunk_text
        )

        if start_char < 0:
            start_char = max(
                len(text)
                - len(chunk_text),
                0,
            )

        end_char = (
            start_char
            + len(chunk_text)
        )

        chunks.append(
            (
                chunk_text,
                start_char,
                end_char,
            )
        )

    # ---------------------------------------
    # Merge tiny final chunk where possible
    # ---------------------------------------
    if (
        len(chunks) >= 2
        and len(chunks[-1][0]) < min_chunk_size
    ):
        previous_text, previous_start, _ = (
            chunks[-2]
        )

        final_text, _, final_end = (
            chunks[-1]
        )

        combined = (
            f"{previous_text} {final_text}"
        ).strip()

        chunks[-2] = (
            combined,
            previous_start,
            final_end,
        )

        chunks.pop()

    return chunks


def chunk_page(
    document: LoadedDocument,
    page: LoadedPage,
    start_chunk_index: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
) -> tuple[list[TextChunk], int]:
    """
    Chunk a single LoadedPage.

    Returns:
        list[TextChunk],
        next available chunk index
    """

    cleaned_text = clean_text(
        page.text
    )

    if not cleaned_text:
        return [], start_chunk_index

    pieces = split_text(
        cleaned_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chunk_size=min_chunk_size,
    )

    chunks: list[TextChunk] = []

    chunk_index = start_chunk_index

    for (
        chunk_text,
        start_char,
        end_char,
    ) in pieces:
        chunk_id = generate_chunk_id(
            document_id=document.document_id,
            chunk_index=chunk_index,
            text=chunk_text,
        )

        metadata = ChunkMetadata(
            document_id=document.document_id,
            chunk_id=chunk_id,

            file_name=document.file_name,
            file_path=document.file_path,

            source_type=document.source_type,

            page=page.page,
            section=page.section,
            chapter=page.chapter,

            chunk_index=chunk_index,

            start_char=start_char,
            end_char=end_char,

            extraction_method=(
                page.extraction_method
            ),

            extraction_confidence=(
                page.extraction_confidence
            ),

            extra={
                "extension": document.extension,
                "title": document.title,
            },
        )

        chunk = TextChunk(
            chunk_id=chunk_id,
            document_id=document.document_id,
            text=chunk_text,
            metadata=metadata,
        )

        chunks.append(
            chunk
        )

        chunk_index += 1

    return chunks, chunk_index


def chunk_document(
    document: LoadedDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
) -> list[TextChunk]:
    """
    Chunk one LoadedDocument.

    Pages/sections are chunked independently to avoid accidentally
    mixing provenance across different source locations.
    """

    if document.ingestion_error:
        logger.warning(
            "Skipping failed document: %s",
            document.file_path,
        )

        return []

    chunks: list[TextChunk] = []

    next_chunk_index = 0

    for page in document.pages:
        page_chunks, next_chunk_index = (
            chunk_page(
                document=document,
                page=page,
                start_chunk_index=(
                    next_chunk_index
                ),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                min_chunk_size=min_chunk_size,
            )
        )

        chunks.extend(
            page_chunks
        )

    logger.info(
        (
            "Chunked document %s | "
            "pages=%d | chunks=%d"
        ),
        document.file_name,
        document.page_count,
        len(chunks),
    )

    return chunks


def chunk_documents(
    documents: Iterable[LoadedDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
) -> list[TextChunk]:
    """
    Chunk multiple documents.

    This is the main helper used by the corpus processing script.
    """

    all_chunks: list[TextChunk] = []

    document_count = 0

    for document in documents:
        document_count += 1

        chunks = chunk_document(
            document=document,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
        )

        all_chunks.extend(
            chunks
        )

    logger.info(
        (
            "Chunking complete | "
            "documents=%d | chunks=%d"
        ),
        document_count,
        len(all_chunks),
    )

    return all_chunks