from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.vector_store.vector_repository import VectorRepository


QUESTIONS_PATH = Path("sample_questions.json")

OUTPUT_PATH = Path(
    "data/processed/graph_candidates.json"
)

TOP_K_PER_QUESTION = 10

MIN_TEXT_LENGTH = 100


def load_questions() -> List[str]:
    with QUESTIONS_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    questions: List[str] = []

    # Supports:
    # [
    #   {"question": "..."},
    #   ...
    # ]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                questions.append(item)

            elif isinstance(item, dict):
                question = (
                    item.get("question")
                    or item.get("query")
                    or item.get("text")
                )

                if question:
                    questions.append(question)

    # Supports:
    # {
    #   "questions": [...]
    # }
    elif isinstance(data, dict):
        raw_questions = data.get(
            "questions",
            []
        )

        for item in raw_questions:
            if isinstance(item, str):
                questions.append(item)

            elif isinstance(item, dict):
                question = (
                    item.get("question")
                    or item.get("query")
                    or item.get("text")
                )

                if question:
                    questions.append(question)

    return questions


def get_chunk_id(
    result: Dict[str, Any],
) -> str | None:

    metadata = (
        result.get("metadata")
        or {}
    )

    return (
        result.get("chunk_id")
        or metadata.get("chunk_id")
        or result.get("id")
    )


def get_text(
    result: Dict[str, Any],
) -> str:

    return (
        result.get("text")
        or result.get("content")
        or result.get("document")
        or ""
    )


def main() -> None:

    questions = load_questions()

    if not questions:
        raise RuntimeError(
            "No questions were found in "
            f"{QUESTIONS_PATH}"
        )

    print(
        f"Loaded {len(questions)} questions."
    )

    repo = VectorRepository()

    candidates: Dict[
        str,
        Dict[str, Any],
    ] = {}

    for index, question in enumerate(
        questions,
        start=1,
    ):

        print("\n" + "=" * 70)

        print(
            f"QUESTION {index}/"
            f"{len(questions)}"
        )

        print(question)

        results = repo.search(
            question,
            top_k=TOP_K_PER_QUESTION,
        )

        print(
            f"Retrieved "
            f"{len(results)} chunks."
        )

        for result in results:

            text = get_text(result)

            # Skip title-only / tiny chunks.
            if len(text.strip()) < MIN_TEXT_LENGTH:
                continue

            chunk_id = get_chunk_id(
                result
            )

            if not chunk_id:
                continue

            if chunk_id not in candidates:

                candidates[chunk_id] = {
                    "chunk_id": chunk_id,
                    "text": text,
                    "metadata": (
                        result.get(
                            "metadata"
                        )
                        or {}
                    ),
                    "matched_questions": [
                        question
                    ],
                }

            else:

                matched = candidates[
                    chunk_id
                ][
                    "matched_questions"
                ]

                if question not in matched:
                    matched.append(question)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = list(
        candidates.values()
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("GRAPH CANDIDATE SELECTION COMPLETE")
    print("=" * 70)

    print(
        f"Questions processed : "
        f"{len(questions)}"
    )

    print(
        f"Unique candidates   : "
        f"{len(output)}"
    )

    print(
        f"Saved to            : "
        f"{OUTPUT_PATH}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()