from __future__ import annotations

import json
from pathlib import Path

from app.generation.answer_generator import AnswerGenerator
from app.retrieval.hybrid_retriever import HybridRetriever


def main() -> None:
    questions_path = Path("data/sample_questions.json")
    data = json.loads(questions_path.read_text(encoding="utf-8"))

    retriever = HybridRetriever()
    generator = AnswerGenerator()

    for i, item in enumerate(data, start=1):
        question = item["question"]
        evidence = retriever.retrieve(question)
        answer = generator.generate(question, evidence)
        print(f"\n[{i}] {question}\n{answer}\n")


if __name__ == "__main__":
    main()
