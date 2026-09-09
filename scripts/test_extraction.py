from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.extraction.entity_extractor import EntityExtractor
from app.extraction.relation_extractor import RelationExtractor
from app.extraction.claim_extractor import ClaimExtractor


CHUNKS_PATH = Path(
    "data/processed/chunks/chunks.json"
)


def dict_to_chunk(chunk: dict) -> SimpleNamespace:
    """
    Convert a JSON chunk dictionary into an object
    compatible with ClaimExtractor.extract_from_chunk().
    """

    metadata_dict = chunk.get("metadata") or {}

    metadata = SimpleNamespace(
        **metadata_dict
    )

    return SimpleNamespace(
        chunk_id=(
            chunk.get("chunk_id")
            or metadata_dict.get("chunk_id")
        ),
        text=(
            chunk.get("text")
            or chunk.get("content")
            or ""
        ),
        content=(
            chunk.get("content")
            or chunk.get("text")
            or ""
        ),
        metadata=metadata,
    )


def main() -> None:
    with CHUNKS_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        chunks = json.load(f)

    # Only test a few chunks.
    sample_chunks = chunks[:5]

    entity_extractor = EntityExtractor()
    relation_extractor = RelationExtractor()

    # Reuse the same extractors so we don't
    # unnecessarily create more LLM clients.
    claim_extractor = ClaimExtractor(
        entity_extractor=entity_extractor,
        relation_extractor=relation_extractor,
    )

    for index, chunk_dict in enumerate(
        sample_chunks,
        start=1,
    ):
        chunk = dict_to_chunk(
            chunk_dict
        )

        text = chunk.text

        print("\n" + "=" * 70)
        print(f"CHUNK {index}")
        print("=" * 70)

        print(
            f"Chunk ID: {chunk.chunk_id}"
        )

        print(
            text[:500]
        )

        print("\nENTITIES")

        entities = entity_extractor.extract(
            text
        )

        print(entities)

        print("\nRELATIONS")

        relations = relation_extractor.extract(
            text
        )

        print(relations)

        print("\nCLAIMS")

        result = (
            claim_extractor.extract_from_chunk(
                chunk
            )
        )

        print(
            result["claims"]
        )


if __name__ == "__main__":
    main()