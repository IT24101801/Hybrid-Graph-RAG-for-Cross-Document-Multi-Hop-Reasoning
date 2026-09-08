"""
app/ingestion/docx_loader.py

DOCX loader for AshenGraph.

Responsibilities:
- Extract paragraphs from DOCX files
- Preserve headings and section structure when possible
- Extract tables as structured textual content
- Maintain useful metadata
- Avoid flattening the whole document into one string

DOCX files do not reliably expose physical page numbers,
so page values remain None.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


logger = logging.getLogger(__name__)


def _clean_text(
    text: str | None,
) -> str:
    if not text:
        return ""

    text = text.replace("\x00", "")
    return " ".join(text.split()).strip()


def _is_heading(
    paragraph: Paragraph,
) -> bool:
    """
    Detect whether a paragraph is styled as a heading.
    """

    style = paragraph.style

    if style is None:
        return False

    style_name = (
        style.name.lower()
        if style.name
        else ""
    )

    return style_name.startswith("heading")


def _heading_level(
    paragraph: Paragraph,
) -> int | None:
    """
    Extract heading level from styles such as Heading 1, Heading 2.
    """

    style = paragraph.style

    if style is None or not style.name:
        return None

    name = style.name.lower()

    if not name.startswith("heading"):
        return None

    try:
        return int(
            name.replace("heading", "").strip()
        )
    except ValueError:
        return None


def _table_to_text(
    table: Table,
) -> tuple[str, dict[str, Any]]:
    """
    Convert a DOCX table into a structured textual representation.

    Returns both text and metadata so a later table-processing
    stage can detect and re-process it if needed.
    """

    rows: list[list[str]] = []

    for row in table.rows:
        values = [
            _clean_text(cell.text)
            for cell in row.cells
        ]
        rows.append(values)

    if not rows:
        return "", {
            "row_count": 0,
            "column_count": 0,
        }

    max_columns = max(
        len(row)
        for row in rows
    )

    lines: list[str] = []

    for row_index, row in enumerate(
        rows,
        start=1,
    ):
        cells = [
            f"Column {column_index}: {value}"
            for column_index, value in enumerate(
                row,
                start=1,
            )
        ]

        lines.append(
            f"Row {row_index}: "
            + " | ".join(cells)
        )

    metadata = {
        "row_count": len(rows),
        "column_count": max_columns,
        "raw_rows": rows,
    }

    return "\n".join(lines), metadata


def load_docx(
    file_path: str | Path,
):
    """
    Load a DOCX file into logical LoadedPage units.

    Strategy
    --------
    Each heading, paragraph block, or table becomes an individual
    logical unit. This gives later chunking code more structure
    than storing the entire document as one giant string.

    Returns
    -------
    list[LoadedPage]
    """

    from app.ingestion.loader import LoadedPage

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"DOCX file does not exist: {path}"
        )

    if path.suffix.lower() != ".docx":
        raise ValueError(
            f"Expected DOCX file, got: {path}"
        )

    logger.info(
        "Reading DOCX: %s",
        path,
    )

    try:
        document = Document(str(path))
    except Exception as exc:
        raise RuntimeError(
            f"Unable to open DOCX '{path}': {exc}"
        ) from exc

    pages: list[LoadedPage] = []

    current_section: str | None = None
    current_chapter: str | None = None

    paragraph_index = 0
    table_index = 0

    for block in document.element.body.iterchildren():
        tag = block.tag.lower()

        # -------------------------
        # Paragraph
        # -------------------------
        if tag.endswith("}p"):
            paragraph = Paragraph(
                block,
                document,
            )

            text = _clean_text(
                paragraph.text
            )

            if not text:
                continue

            paragraph_index += 1

            if _is_heading(paragraph):
                level = _heading_level(
                    paragraph
                )

                if level == 1:
                    current_chapter = text
                    current_section = text
                else:
                    current_section = text

                pages.append(
                    LoadedPage(
                        text=text,
                        page=None,
                        section=current_section,
                        chapter=current_chapter,
                        extraction_method="docx_heading",
                        extraction_confidence=1.0,
                        metadata={
                            "content_type": "heading",
                            "heading_level": level,
                            "paragraph_index": (
                                paragraph_index
                            ),
                        },
                    )
                )

                continue

            pages.append(
                LoadedPage(
                    text=text,
                    page=None,
                    section=current_section,
                    chapter=current_chapter,
                    extraction_method="docx_paragraph",
                    extraction_confidence=1.0,
                    metadata={
                        "content_type": "paragraph",
                        "paragraph_index": (
                            paragraph_index
                        ),
                    },
                )
            )

        # -------------------------
        # Table
        # -------------------------
        elif tag.endswith("}tbl"):
            table = Table(
                block,
                document,
            )

            table_index += 1

            table_text, table_metadata = (
                _table_to_text(table)
            )

            if not table_text:
                continue

            pages.append(
                LoadedPage(
                    text=table_text,
                    page=None,
                    section=current_section,
                    chapter=current_chapter,
                    extraction_method="docx_table",
                    extraction_confidence=0.95,
                    metadata={
                        "content_type": "table",
                        "table_index": table_index,
                        **table_metadata,
                    },
                )
            )

    logger.info(
        "DOCX loaded: %s | units=%d",
        path.name,
        len(pages),
    )

    return pages