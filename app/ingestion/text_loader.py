"""
app/ingestion/text_loader.py

Plain-text loader for AshenGraph.

Responsibilities:
- Read TXT files
- Normalize encoding failures safely
- Preserve paragraph boundaries
- Detect simple chapter/section headings when possible
- Produce logical LoadedPage units

Plain text files do not contain reliable physical page numbers.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path


logger = logging.getLogger(__name__)


CHAPTER_PATTERN = re.compile(
    r"^(chapter|book|part|volume)\s+"
    r"([0-9ivxlcdm]+|\w+)"
    r"(?:\s*[:\-]\s*(.+))?$",
    re.IGNORECASE,
)


SECTION_PATTERN = re.compile(
    r"^(section|scene|act)\s+"
    r"([0-9ivxlcdm]+|\w+)"
    r"(?:\s*[:\-]\s*(.+))?$",
    re.IGNORECASE,
)


def _clean_text(
    text: str,
) -> str:
    text = text.replace("\x00", "")

    return "\n".join(
        line.rstrip()
        for line in text.splitlines()
    ).strip()


def _looks_like_uppercase_heading(
    text: str,
) -> bool:
    """
    Detect simple headings like:

        THE FIRST WAR
        BLACKHOLD
        ASHES OF THE NORTH

    This is intentionally conservative.
    """

    stripped = text.strip()

    if len(stripped) < 3:
        return False

    if len(stripped) > 100:
        return False

    if stripped.endswith(
        (".", "!", "?", ",", ";")
    ):
        return False

    letters = [
        char
        for char in stripped
        if char.isalpha()
    ]

    if not letters:
        return False

    return all(
        char.isupper()
        for char in letters
    )


def _split_paragraphs(
    text: str,
) -> list[str]:
    """
    Split text on blank lines.
    """

    blocks = re.split(
        r"\n\s*\n",
        text,
    )

    return [
        block.strip()
        for block in blocks
        if block.strip()
    ]


def load_text(
    file_path: str | Path,
):
    """
    Load a plain-text file into logical units.

    Heading detection is heuristic and intentionally limited.
    """

    from app.ingestion.loader import LoadedPage

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Text file does not exist: {path}"
        )

    if path.suffix.lower() != ".txt":
        raise ValueError(
            f"Expected TXT file, got: {path}"
        )

    logger.info(
        "Reading text file: %s",
        path,
    )

    try:
        raw_text = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        raw_text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    text = _clean_text(
        raw_text
    )

    if not text:
        return []

    blocks = _split_paragraphs(
        text
    )

    pages: list[LoadedPage] = []

    current_chapter: str | None = None
    current_section: str | None = None

    block_index = 0

    for block in blocks:
        block_index += 1

        single_line = (
            "\n" not in block
        )

        is_chapter = bool(
            single_line
            and CHAPTER_PATTERN.match(block)
        )

        is_section = bool(
            single_line
            and SECTION_PATTERN.match(block)
        )

        is_upper_heading = (
            single_line
            and _looks_like_uppercase_heading(
                block
            )
        )

        if is_chapter:
            current_chapter = block.strip()
            current_section = block.strip()

            pages.append(
                LoadedPage(
                    text=block.strip(),
                    page=None,
                    section=current_section,
                    chapter=current_chapter,
                    extraction_method="text_heading",
                    extraction_confidence=0.95,
                    metadata={
                        "content_type": "heading",
                        "heading_kind": "chapter",
                        "block_index": (
                            block_index
                        ),
                    },
                )
            )

            continue

        if is_section or is_upper_heading:
            current_section = block.strip()

            pages.append(
                LoadedPage(
                    text=block.strip(),
                    page=None,
                    section=current_section,
                    chapter=current_chapter,
                    extraction_method="text_heading",
                    extraction_confidence=0.85,
                    metadata={
                        "content_type": "heading",
                        "heading_kind": (
                            "section"
                            if is_section
                            else "heuristic"
                        ),
                        "block_index": (
                            block_index
                        ),
                    },
                )
            )

            continue

        pages.append(
            LoadedPage(
                text=block,
                page=None,
                section=current_section,
                chapter=current_chapter,
                extraction_method="text_paragraph",
                extraction_confidence=1.0,
                metadata={
                    "content_type": "paragraph",
                    "block_index": (
                        block_index
                    ),
                },
            )
        )

    logger.info(
        "Text file loaded: %s | units=%d",
        path.name,
        len(pages),
    )

    return pages