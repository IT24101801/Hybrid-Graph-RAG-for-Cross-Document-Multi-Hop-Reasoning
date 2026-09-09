"""
Corpus ingestion + processing script for AshenGraph.

Run from project root:
    python scripts/ingest.py
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.loader import document_to_dict, load_corpus
from app.processing.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_MIN_CHUNK_SIZE,
    chunk_documents,
)
from app.processing.metadata import chunk_to_dict

logger = logging.getLogger("ashengraph.ingest")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the corpus, process it, and save chunks.json."
    )
    parser.add_argument(
        "--raw-dir",
        default=os.getenv("RAW_DATA_DIR", "./data/raw"),
    )
    parser.add_argument(
        "--processed-dir",
        default=os.getenv("PROCESSED_DATA_DIR", "./data/processed"),
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
    )
    parser.add_argument(
        "--min-chunk-size",
        type=int,
        default=DEFAULT_MIN_CHUNK_SIZE,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    raw_dir = _resolve_path(args.raw_dir)
    processed_dir = _resolve_path(args.processed_dir)

    documents_json = processed_dir / "documents" / "documents.json"
    chunks_json = processed_dir / "chunks" / "chunks.json"
    report_json = processed_dir / "reports" / "ingestion_report.json"

    if not raw_dir.exists():
        logger.error("Raw corpus directory does not exist: %s", raw_dir)
        return 1

    logger.info("Loading corpus from: %s", raw_dir)
    result = load_corpus(root_dir=raw_dir, recursive=True)

    if not result.documents:
        logger.error("No documents were successfully loaded.")
        return 1

    _write_json(
        documents_json,
        [document_to_dict(doc) for doc in result.documents],
    )

    logger.info("Creating chunks...")
    chunks = chunk_documents(
        documents=result.documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        min_chunk_size=args.min_chunk_size,
    )

    _write_json(
        chunks_json,
        [chunk_to_dict(chunk) for chunk in chunks],
    )

    report = {
        "raw_dir": str(raw_dir),
        "processed_dir": str(processed_dir),
        "success_count": result.success_count,
        "failure_count": result.failure_count,
        "skipped_count": result.skipped_count,
        "chunk_count": len(chunks),
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "min_chunk_size": args.min_chunk_size,
        "failed_files": result.failed_files,
        "skipped_files": result.skipped_files,
    }
    _write_json(report_json, report)

    print()
    print("=" * 60)
    print("ASHENGRAPH INGESTION COMPLETE")
    print("=" * 60)
    print(f"Documents loaded : {result.success_count}")
    print(f"Documents failed : {result.failure_count}")
    print(f"Files skipped    : {result.skipped_count}")
    print(f"Chunks created   : {len(chunks)}")
    print(f"Chunks JSON      : {chunks_json}")
    print(f"Report           : {report_json}")
    print("=" * 60)

    if not chunks:
        return 2

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    raise SystemExit(main())
