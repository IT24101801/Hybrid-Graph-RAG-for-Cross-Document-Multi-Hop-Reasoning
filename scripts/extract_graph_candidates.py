from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.extraction.claim_extractor import ClaimExtractor


INPUT_PATH = Path(
    "data/processed/graph_candidates.json"
)

OUTPUT_PATH = Path(
    "data/processed/graph_extractions.json"
)


def dict_to_chunk(item: dict) -> SimpleNamespace:
    metadata_dict = item.get("metadata") or {}

    metadata = SimpleNamespace(
        **metadata_dict
    )

    return SimpleNamespace(
        chunk_id=(
            item.get("chunk_id")
            or metadata_dict.get("chunk_id")
        ),
        text=(
            item.get("text")
            or item.get("content")
            or ""
        ),
        content=(
            item.get("content")
            or item.get("text")
            or ""
        ),
        metadata=metadata,
    )


def main() -> None:
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        candidates = json.load(f)

    print(
        f"Loaded {len(candidates)} graph candidates."
    )

    extractor = ClaimExtractor()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    for index, item in enumerate(
        candidates,
        start=1,
    ):
        chunk = dict_to_chunk(item)

        text = chunk.text.strip()

        if len(text) < 100:
            print(
                f"[{index}/{len(candidates)}] "
                "Skipped short chunk."
            )
            continue

        print("\n" + "=" * 70)

        print(
            f"[{index}/{len(candidates)}] "
            f"Extracting {chunk.chunk_id}"
        )

        print(
            text[:180].replace(
                "\n",
                " "
            )
        )

        try:
            extraction = (
                extractor.extract_from_chunk(
                    chunk
                )
            )

            result = {
                "chunk_id": chunk.chunk_id,
                "text": text,
                "metadata": item.get(
                    "metadata",
                    {},
                ),
                "matched_questions": item.get(
                    "matched_questions",
                    [],
                ),
                "entities": extraction.get(
                    "entities",
                    [],
                ),
                "claims": extraction.get(
                    "claims",
                    [],
                ),
            }

            results.append(result)

            # Save after every chunk.
            # This prevents losing all progress
            # if the API fails later.
            with OUTPUT_PATH.open(
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    results,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            print(
                f"Entities: "
                f"{len(result['entities'])}"
            )

            print(
                f"Claims  : "
                f"{len(result['claims'])}"
            )

        except Exception as exc:
            print(
                f"FAILED: {exc}"
            )

            # Continue processing the next chunk.
            continue

    total_entities = sum(
        len(item["entities"])
        for item in results
    )

    total_claims = sum(
        len(item["claims"])
        for item in results
    )

    print("\n" + "=" * 70)
    print("GRAPH EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        f"Candidates processed : "
        f"{len(results)}"
    )

    print(
        f"Entities extracted   : "
        f"{total_entities}"
    )

    print(
        f"Claims extracted     : "
        f"{total_claims}"
    )

    print(
        f"Saved to             : "
        f"{OUTPUT_PATH}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()