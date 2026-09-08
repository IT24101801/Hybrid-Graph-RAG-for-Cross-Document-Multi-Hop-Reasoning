"""
app/ingestion/markdown_loader.py

Markdown loader for AshenGraph.

Responsibilities:
- Read Markdown safely
- Preserve heading hierarchy
- Split content into logical sections
- Retain source structure for later chunking and citations

The loader deliberately keeps Markdown semantics lightweight.
Complex markdown parsing can be added later if the corpus needs it.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path


logger = logging.getLogger(__name__)


HEADING_PATTERN = re.compile(
    r"^(#{1,6})\s+(.+?)\s*$"
)


def _clean_block(
    text: str,
) -> str:
    """
    Clean a markdown content block without destroying structure.
    """

    text = text.replace("\x00", "")

    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]

    while lines and not lines[0].strip():
        lines.pop(0)

    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines).strip()


def _flush_buffer(
    pages: list,
    buffer: list[str],
    current_section: str | None,
    current_chapter: str | None,
    block_index: int,
):
    """
    Convert buffered markdown lines into one LoadedPage.

    Returns the updated block index.
    """

    from app.ingestion.loader import LoadedPage

    text = _clean_block(
        "\n".join(buffer)
    )

    buffer.clear()

    if not text:
        return block_index

    block_index += 1

    pages.append(
        LoadedPage(
            text=text,
            page=None,
            section=current_section,
            chapter=current_chapter,
            extraction_method="markdown_text",
            extraction_confidence=1.0,
            metadata={
                "content_type": "markdown_block",
                "block_index": block_index,
            },
        )
    )

    return block_index


def load_markdown(
    file_path: str | Path,
):
    """
    Load Markdown into logical sections.

    Heading behavior:
    - H1 becomes chapter + section
    - H2-H6 become section
    """

    from app.ingestion.loader import LoadedPage

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Markdown file does not exist: {path}"
        )

    if path.suffix.lower() not in {
        ".md",
        ".markdown",
    }:
        raise ValueError(
            f"Expected Markdown file, got: {path}"
        )

    logger.info(
        "Reading Markdown: %s",
        path,
    )

    try:
        content = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        content = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    pages: list[LoadedPage] = []

    current_section: str | None = None
    current_chapter: str | None = None

    buffer: list[str] = []

    block_index = 0
    heading_index = 0

    for line in content.splitlines():
        match = HEADING_PATTERN.match(
            line
        )

        if match:
            block_index = _flush_buffer(
                pages=pages,
                buffer=buffer,
                current_section=current_section,
                current_chapter=current_chapter,
                block_index=block_index,
            )

            hashes = match.group(1)
            title = match.group(2).strip()

            level = len(hashes)

            if level == 1:
                current_chapter = title
                current_section = title
            else:
                current_section = title

            heading_index += 1

            pages.append(
                LoadedPage(
                    text=title,
                    page=None,
                    section=current_section,
                    chapter=current_chapter,
                    extraction_method="markdown_heading",
                    extraction_confidence=1.0,
                    metadata={
                        "content_type": "heading",
                        "heading_level": level,
                        "heading_index": (
                            heading_index
                        ),
                    },
                )
            )

            continue

        buffer.append(line)

    _flush_buffer(
        pages=pages,
        buffer=buffer,
        current_section=current_section,
        current_chapter=current_chapter,
        block_index=block_index,
    )

    logger.info(
        "Markdown loaded: %s | units=%d",
        path.name,
        len(pages),
    )

    return pages