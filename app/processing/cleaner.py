"""
app/processing/cleaner.py

Text cleaning utilities for AshenGraph.

Responsibilities:
- Normalize whitespace
- Remove null/control characters
- Repair common PDF extraction artifacts
- Reduce repeated blank lines
- Preserve paragraph structure
- Avoid aggressive cleaning that could destroy evidence

The archive contains fictional names, terminology, and potentially
conflicting sources, so this cleaner intentionally avoids spelling
correction or semantic rewriting.
"""

from __future__ import annotations

import re
import unicodedata


MULTIPLE_SPACES_RE = re.compile(
    r"[ \t]{2,}"
)

MULTIPLE_BLANK_LINES_RE = re.compile(
    r"\n{3,}"
)

HYPHENATED_LINEBREAK_RE = re.compile(
    r"(\w)-\n(\w)"
)

SPACE_BEFORE_PUNCT_RE = re.compile(
    r"\s+([,.;:!?])"
)

SPACE_AFTER_PUNCT_RE = re.compile(
    r"([,.;:!?])([A-Za-z])"
)


def remove_control_characters(
    text: str,
) -> str:
    """
    Remove unwanted Unicode control characters while preserving
    useful whitespace characters such as newline and tab.
    """

    allowed = {
        "\n",
        "\r",
        "\t",
    }

    return "".join(
        char
        for char in text
        if char in allowed
        or unicodedata.category(char)[0] != "C"
    )


def normalize_unicode(
    text: str,
) -> str:
    """
    Normalize Unicode characters.

    NFKC helps standardize visually equivalent characters while
    preserving semantic content.
    """

    return unicodedata.normalize(
        "NFKC",
        text,
    )


def fix_hyphenated_linebreaks(
    text: str,
) -> str:
    """
    Repair common PDF extraction artifacts.

    Example:
        "inter-\nnational"
        becomes
        "international"

    This is useful for text extracted from PDFs where words are
    split across line endings.
    """

    return HYPHENATED_LINEBREAK_RE.sub(
        r"\1\2",
        text,
    )


def normalize_line_endings(
    text: str,
) -> str:
    """
    Convert Windows/Mac line endings into standard Unix newlines.
    """

    return (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def normalize_whitespace(
    text: str,
) -> str:
    """
    Normalize excessive spaces while preserving paragraphs.
    """

    lines: list[str] = []

    for line in text.splitlines():
        line = MULTIPLE_SPACES_RE.sub(
            " ",
            line,
        )

        lines.append(
            line.strip()
        )

    text = "\n".join(lines)

    text = MULTIPLE_BLANK_LINES_RE.sub(
        "\n\n",
        text,
    )

    return text.strip()


def fix_punctuation_spacing(
    text: str,
) -> str:
    """
    Repair small punctuation spacing issues introduced during
    extraction.
    """

    text = SPACE_BEFORE_PUNCT_RE.sub(
        r"\1",
        text,
    )

    text = SPACE_AFTER_PUNCT_RE.sub(
        r"\1 \2",
        text,
    )

    return text


def clean_text(
    text: str | None,
) -> str:
    """
    Main text-cleaning pipeline.

    The order is deliberate:
    1. remove invalid/control characters
    2. normalize Unicode
    3. normalize line endings
    4. repair PDF line-break hyphenation
    5. normalize spaces and blank lines
    6. clean punctuation spacing

    Parameters
    ----------
    text:
        Raw extracted text.

    Returns
    -------
    str
        Cleaned text.
    """

    if not text:
        return ""

    text = remove_control_characters(
        text
    )

    text = normalize_unicode(
        text
    )

    text = normalize_line_endings(
        text
    )

    text = fix_hyphenated_linebreaks(
        text
    )

    text = normalize_whitespace(
        text
    )

    text = fix_punctuation_spacing(
        text
    )

    return text.strip()


def clean_for_embedding(
    text: str | None,
) -> str:
    """
    Produce embedding-friendly text.

    Unlike clean_text(), this collapses internal line breaks into
    spaces because embedding models generally do not require exact
    page formatting.
    """

    cleaned = clean_text(
        text
    )

    if not cleaned:
        return ""

    cleaned = re.sub(
        r"\s*\n\s*",
        " ",
        cleaned,
    )

    cleaned = MULTIPLE_SPACES_RE.sub(
        " ",
        cleaned,
    )

    return cleaned.strip()