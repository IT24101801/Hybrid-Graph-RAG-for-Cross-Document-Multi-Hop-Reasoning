from __future__ import annotations

import argparse

from app.generation.answer_generator import AnswerGenerator
from app.generation.citation_builder import CitationBuilder
from app.retrieval.hybrid_retriever import HybridRetriever


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="+")
    args = parser.parse_args()
    question = " ".join(args.question)

    retriever = HybridRetriever()
    evidence = retriever.retrieve(question)
    answer = AnswerGenerator().generate(question, evidence)
    citations = CitationBuilder().build(evidence)

    print("\nANSWER\n------")
    print(answer)
    print("\nCITATIONS\n---------")
    for citation in citations:
        print(citation)


if __name__ == "__main__":
    main()
