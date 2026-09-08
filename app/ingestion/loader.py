"""
app/ingestion/loader.py

Unified document loader for the AshenGraph project.

Responsibilities:
- Discover files in the Ashen Era corpus
- Detect supported file types
- Infer source category
- Generate stable document IDs
- Route files to the appropriate file-specific loader
- Preserve consistent metadata
- Continue processing even if individual files fail

This module does NOT perform:
- Chunking
- Embedding
- Entity extraction
- Graph insertion

Those happen later in the pipeline.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from app.config.settings import get_settings
from app.config.source_config import SourceType, infer_source_type

# These loaders will be implemented in separate files.
from app.ingestion.pdf_loader import load_pdf
from app.ingestion.docx_loader import load_docx
from app.ingestion.markdown_loader import load_markdown
from app.ingestion.text_loader import load_text


logger = logging.getLogger(__name__)


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".md",
    ".markdown",
    ".txt",
}


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class LoadedPage:
    """
    Represents one logical page/section/unit extracted from a document.

    For PDFs:
        one LoadedPage usually maps to one physical page.

    For DOCX/Markdown/TXT:
        page may be None unless a parser can infer page boundaries.
    """

    text: str

    page: int | None = None

    section: str | None = None

    chapter: str | None = None

    extraction_method: str = "unknown"

    extraction_confidence: float = 1.0

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedDocument:
    """
    Unified representation of an ingested document.

    All downstream stages should work with this structure instead
    of handling PDF/DOCX/Markdown/TXT independently.
    """

    document_id: str

    file_name: str

    file_path: str

    extension: str

    source_type: str

    title: str

    pages: list[LoadedPage]

    metadata: dict[str, Any] = field(default_factory=dict)

    ingestion_error: str | None = None

    @property
    def text(self) -> str:
        """
        Convenience property returning all extracted text.
        """

        return "\n\n".join(
            page.text.strip()
            for page in self.pages
            if page.text and page.text.strip()
        )

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def is_empty(self) -> bool:
        return not bool(self.text.strip())


@dataclass
class IngestionResult:
    """
    Result of loading a corpus or collection of files.
    """

    documents: list[LoadedDocument] = field(default_factory=list)

    failed_files: list[dict[str, str]] = field(default_factory=list)

    skipped_files: list[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.documents)

    @property
    def failure_count(self) -> int:
        return len(self.failed_files)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_files)


# ============================================================
# ID GENERATION
# ============================================================

def generate_document_id(
    file_path: Path,
    corpus_root: Path | None = None,
) -> str:
    """
    Generate a deterministic document ID.

    A stable ID is important because the same document ID must
    later be shared between:

    - ChromaDB
    - Neo4j
    - extracted claims
    - citations
    - evaluation output

    We use the relative path when possible rather than hashing
    the absolute machine-specific path.

    Example:
        chronicles/book_01.pdf

    might become:
        doc_9f8b1a72dcd7
    """

    resolved_path = file_path.resolve()

    if corpus_root is not None:
        try:
            identifier = str(
                resolved_path.relative_to(corpus_root.resolve())
            )
        except ValueError:
            identifier = str(resolved_path)
    else:
        identifier = str(resolved_path)

    identifier = identifier.replace("\\", "/").lower()

    digest = hashlib.sha256(
        identifier.encode("utf-8")
    ).hexdigest()[:12]

    return f"doc_{digest}"


# ============================================================
# TITLE HELPERS
# ============================================================

def infer_title(file_path: Path) -> str:
    """
    Create a reasonable fallback title from the filename.

    Example:
        siege_of_blackhold.pdf

    becomes:
        Siege Of Blackhold

    File-specific loaders may later replace this with a proper
    document title extracted from the document itself.
    """

    title = file_path.stem

    title = title.replace("_", " ")
    title = title.replace("-", " ")

    title = " ".join(title.split())

    return title.title()


# ============================================================
# FILE TYPE DETECTION
# ============================================================

def get_extension(file_path: Path) -> str:
    """
    Normalize a file extension to lowercase.
    """

    return file_path.suffix.lower()


def is_supported_file(file_path: Path) -> bool:
    """
    Return True if the file extension is supported.
    """

    return (
        file_path.is_file()
        and get_extension(file_path) in SUPPORTED_EXTENSIONS
    )


# ============================================================
# LOADER ROUTING
# ============================================================

def _run_specific_loader(
    file_path: Path,
) -> list[LoadedPage]:
    """
    Dispatch a file to the correct format-specific parser.

    Every format-specific loader should return:

        list[LoadedPage]

    This keeps the rest of the pipeline format-independent.
    """

    extension = get_extension(file_path)

    if extension == ".pdf":
        return load_pdf(file_path)

    if extension == ".docx":
        return load_docx(file_path)

    if extension in {".md", ".markdown"}:
        return load_markdown(file_path)

    if extension == ".txt":
        return load_text(file_path)

    raise ValueError(
        f"Unsupported file extension: {extension}"
    )


# ============================================================
# SINGLE DOCUMENT LOADING
# ============================================================

def load_document(
    file_path: str | Path,
    corpus_root: str | Path | None = None,
) -> LoadedDocument:
    """
    Load one corpus document into the unified LoadedDocument model.

    Parameters
    ----------
    file_path:
        Path to the input document.

    corpus_root:
        Root directory of the corpus.

        Used for:
        - stable document IDs
        - relative path metadata
        - source type inference

    Returns
    -------
    LoadedDocument

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.

    ValueError
        If the file type is unsupported.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Expected a file but received: {path}"
        )

    extension = get_extension(path)

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{extension}' "
            f"for file: {path}"
        )

    root_path = (
        Path(corpus_root)
        if corpus_root is not None
        else None
    )

    document_id = generate_document_id(
        path,
        corpus_root=root_path,
    )

    # Prefer relative corpus path when available.
    if root_path is not None:
        try:
            relative_path = str(
                path.resolve().relative_to(
                    root_path.resolve()
                )
            )
        except ValueError:
            relative_path = str(path)
    else:
        relative_path = str(path)

    relative_path = relative_path.replace("\\", "/")

    source_type = infer_source_type(
        relative_path
    )

    title = infer_title(path)

    logger.info(
        "Loading document: %s",
        relative_path,
    )

    try:
        pages = _run_specific_loader(path)

    except Exception as exc:
        logger.exception(
            "Failed to load document %s",
            path,
        )

        return LoadedDocument(
            document_id=document_id,
            file_name=path.name,
            file_path=relative_path,
            extension=extension,
            source_type=source_type.value,
            title=title,
            pages=[],
            metadata={
                "absolute_path": str(path.resolve()),
            },
            ingestion_error=str(exc),
        )

    # Add common metadata to every page.
    for page_index, page in enumerate(
        pages,
        start=1,
    ):
        if page.page is None and extension == ".pdf":
            page.page = page_index

        page.metadata.setdefault(
            "document_id",
            document_id,
        )

        page.metadata.setdefault(
            "file_name",
            path.name,
        )

        page.metadata.setdefault(
            "file_path",
            relative_path,
        )

        page.metadata.setdefault(
            "source_type",
            source_type.value,
        )

    document = LoadedDocument(
        document_id=document_id,
        file_name=path.name,
        file_path=relative_path,
        extension=extension,
        source_type=source_type.value,
        title=title,
        pages=pages,
        metadata={
            "absolute_path": str(path.resolve()),
            "relative_path": relative_path,
        },
    )

    if document.is_empty:
        logger.warning(
            "Document produced no text: %s",
            relative_path,
        )

    logger.info(
        "Loaded %s | pages=%d | source=%s",
        relative_path,
        document.page_count,
        source_type.value,
    )

    return document


# ============================================================
# FILE DISCOVERY
# ============================================================

def discover_files(
    root_dir: str | Path,
    recursive: bool = True,
) -> list[Path]:
    """
    Discover supported corpus files under a directory.

    Parameters
    ----------
    root_dir:
        Root directory containing the Ashen Era corpus.

    recursive:
        Search recursively if True.

    Returns
    -------
    list[Path]
        Sorted list of supported files.
    """

    root = Path(root_dir)

    if not root.exists():
        raise FileNotFoundError(
            f"Corpus directory does not exist: {root}"
        )

    if not root.is_dir():
        raise ValueError(
            f"Expected corpus directory, got: {root}"
        )

    iterator: Iterable[Path]

    if recursive:
        iterator = root.rglob("*")
    else:
        iterator = root.glob("*")

    files = [
        path
        for path in iterator
        if is_supported_file(path)
    ]

    # Deterministic ordering makes ingestion reproducible.
    files.sort(
        key=lambda p: str(p).lower()
    )

    return files


# ============================================================
# CORPUS INGESTION
# ============================================================

def load_corpus(
    root_dir: str | Path | None = None,
    recursive: bool = True,
) -> IngestionResult:
    """
    Load the entire Ashen Era corpus.

    One broken file must NOT stop ingestion of the other files.

    Parameters
    ----------
    root_dir:
        Corpus root directory.

        If omitted, RAW_DATA_DIR from settings is used.

    recursive:
        Whether to search recursively.

    Returns
    -------
    IngestionResult
    """

    settings = get_settings()

    root = Path(
        root_dir
        if root_dir is not None
        else settings.raw_data_dir
    )

    result = IngestionResult()

    logger.info(
        "Discovering corpus files under: %s",
        root,
    )

    files = discover_files(
        root,
        recursive=recursive,
    )

    logger.info(
        "Found %d supported files",
        len(files),
    )

    for index, file_path in enumerate(
        files,
        start=1,
    ):
        logger.info(
            "[%d/%d] Ingesting %s",
            index,
            len(files),
            file_path,
        )

        try:
            document = load_document(
                file_path=file_path,
                corpus_root=root,
            )

            if document.ingestion_error:
                result.failed_files.append(
                    {
                        "file": str(file_path),
                        "error": document.ingestion_error,
                    }
                )
                continue

            result.documents.append(
                document
            )

        except Exception as exc:
            logger.exception(
                "Unexpected ingestion failure: %s",
                file_path,
            )

            result.failed_files.append(
                {
                    "file": str(file_path),
                    "error": str(exc),
                }
            )

    logger.info(
        (
            "Corpus ingestion complete | "
            "success=%d | failed=%d | skipped=%d"
        ),
        result.success_count,
        result.failure_count,
        result.skipped_count,
    )

    return result


# ============================================================
# SERIALIZATION HELPER
# ============================================================

def document_to_dict(
    document: LoadedDocument,
) -> dict[str, Any]:
    """
    Convert LoadedDocument to a JSON-serializable dictionary.

    Useful for:
    - saving intermediate processed files
    - debugging
    - testing
    - generating ingestion reports
    """

    return {
        "document_id": document.document_id,
        "file_name": document.file_name,
        "file_path": document.file_path,
        "extension": document.extension,
        "source_type": document.source_type,
        "title": document.title,
        "page_count": document.page_count,
        "ingestion_error": document.ingestion_error,
        "metadata": document.metadata,
        "pages": [
            {
                "text": page.text,
                "page": page.page,
                "section": page.section,
                "chapter": page.chapter,
                "extraction_method": (
                    page.extraction_method
                ),
                "extraction_confidence": (
                    page.extraction_confidence
                ),
                "metadata": page.metadata,
            }
            for page in document.pages
        ],
    }


# ============================================================
# OPTIONAL LOCAL TEST
# ============================================================

if __name__ == "__main__":
    """
    Allows quick testing with:

        python -m app.ingestion.loader

    It uses RAW_DATA_DIR from .env.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    ingestion_result = load_corpus()

    print()
    print("=" * 60)
    print("ASHENGRAPH INGESTION SUMMARY")
    print("=" * 60)

    print(
        f"Successfully loaded: "
        f"{ingestion_result.success_count}"
    )

    print(
        f"Failed: "
        f"{ingestion_result.failure_count}"
    )

    print(
        f"Skipped: "
        f"{ingestion_result.skipped_count}"
    )

    if ingestion_result.failed_files:
        print()
        print("Failed files:")

        for failure in ingestion_result.failed_files:
            print(
                f"- {failure['file']}: "
                f"{failure['error']}"
            )