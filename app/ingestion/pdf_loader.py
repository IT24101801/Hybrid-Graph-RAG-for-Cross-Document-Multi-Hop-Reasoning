"""
app/ingestion/pdf_loader.py

PDF loader for AshenGraph.

Responsibilities:
- Extract text from PDF pages
- Preserve physical page numbers
- Detect pages with very little or no extractable text
- Mark likely scanned pages for later OCR handling
- Preserve extraction metadata
- Fail gracefully on unreadable PDFs

This file performs text extraction only.
OCR is intentionally left as a later pipeline stage.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pypdf import PdfReader


logger = logging.getLogger(__name__)


MIN_TEXT_LENGTH_FOR_DIGITAL_PAGE = 20


def _clean_text(text: str | None) -> str:
    """
    Normalize extracted PDF text without aggressively altering content.
    """

    if not text:
        return ""

    text = text.replace("\x00", "")

    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]

    cleaned_lines: list[str] = []

    previous_blank = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(stripped)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()


def _extract_page_text(
    page: Any,
) -> tuple[str, str, float]:
    """
    Extract text from one pypdf page.

    Returns
    -------
    tuple:
        text,
        extraction_method,
        extraction_confidence
    """

    try:
        raw_text = page.extract_text()
    except Exception as exc:
        logger.warning(
            "Failed to extract PDF page text: %s",
            exc,
        )

        return "", "pdf_text_failed", 0.0

    text = _clean_text(raw_text)

    if len(text) < MIN_TEXT_LENGTH_FOR_DIGITAL_PAGE:
        return text, "pdf_text_low_content", 0.35

    return text, "pdf_text", 0.95


def load_pdf(
    file_path: str | Path,
):
    """
    Load a PDF document into a list of LoadedPage objects.

    Parameters
    ----------
    file_path:
        Path to the PDF.

    Returns
    -------
    list[LoadedPage]

    Notes
    -----
    Physical PDF page numbering is preserved using 1-based indexing.

    Pages with little or no extractable text are marked as likely
    scanned pages through metadata. A later OCR stage can inspect
    these pages.
    """

    # Lazy import avoids circular import with loader.py.
    from app.ingestion.loader import LoadedPage

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file does not exist: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected PDF file, got: {path}"
        )

    logger.info(
        "Reading PDF: %s",
        path,
    )

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise RuntimeError(
            f"Unable to open PDF '{path}': {exc}"
        ) from exc

    pages: list[LoadedPage] = []

    for page_number, pdf_page in enumerate(
        reader.pages,
        start=1,
    ):
        text, method, confidence = _extract_page_text(
            pdf_page
        )

        likely_scan = (
            len(text) < MIN_TEXT_LENGTH_FOR_DIGITAL_PAGE
        )

        metadata: dict[str, Any] = {
            "physical_page": page_number,
            "likely_scanned_page": likely_scan,
        }

        try:
            metadata["rotation"] = int(
                pdf_page.get("/Rotate", 0) or 0
            )
        except Exception:
            metadata["rotation"] = 0

        page = LoadedPage(
            text=text,
            page=page_number,
            extraction_method=method,
            extraction_confidence=confidence,
            metadata=metadata,
        )

        pages.append(page)

    logger.info(
        "PDF loaded: %s | pages=%d",
        path.name,
        len(pages),
    )

    return pages