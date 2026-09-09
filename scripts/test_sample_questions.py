from __future__ import annotations

import json
from pathlib import Path

from scripts.ask_hybrid import (
    extract_seed_entity,
    hybrid_retrieve,
    build_context,
    build_prompt,
)

from app.generation.llm_client import LLMClient


QUESTIONS_PATH = Path("sample_questions.json")

MAX_QUESTIONS = 9


def main() -> None:
    if not QUESTIONS_PATH.exists():
        print(
            f"Could not find {QUESTIONS_PATH}"
        )
        return

    data = json.loads(
        QUESTIONS_PATH.read_text(
            encoding="utf-8"
        )
    )

    if isinstance(data, dict):
        questions = (
            data.get("questions")
            or data.get("items")
            or []
        )
    else:
        questions = data

    if not questions:
        print(
            "No questions found."
        )
        return

    llm = LLMClient()

    print("=" * 70)
    print("ASHENGRAPH SAMPLE QUESTION TEST")
    print("=" * 70)

    for index, item in enumerate(
        questions[11:20],
        start=1,
    ):

        if isinstance(item, str):
            question = item
        else:
            question = (
                item.get("question")
                or item.get("query")
                or ""
            )

        if not question:
            continue

        print("\n" + "=" * 70)
        print(
            f"QUESTION {index}"
        )
        print("=" * 70)

        print(
            question
        )

        try:
            seed_entity = extract_seed_entity(
                question
            )

            print(
                "\nSeed entity:",
                seed_entity,
            )

            (
                graph_neighbors,
                expansion_entities,
                results,
            ) = hybrid_retrieve(
                question=question,
                seed_entity=seed_entity,
                top_k=10,
            )

            print(
                "Retrieved chunks:",
                len(results),
            )

            print(
                "Expansion entities:",
                expansion_entities,
            )

            if not results:
                print(
                    "\nNO EVIDENCE FOUND"
                )
                continue

            context = build_context(
                results,
                max_items=15,
            )

            prompt = build_prompt(
                question=question,
                seed_entity=seed_entity,
                graph_neighbors=graph_neighbors,
                evidence_context=context,
            )

            answer = llm.generate(
                prompt
            )

            print(
                "\nANSWER"
            )

            print(
                answer
            )

        except Exception as exc:
            print(
                "\nFAILED:"
            )
            print(
                exc
            )


if __name__ == "__main__":
    main()