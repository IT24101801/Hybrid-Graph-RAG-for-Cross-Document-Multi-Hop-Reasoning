from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

from app.vector_store.vector_repository import VectorRepository
from app.generation.llm_client import LLMClient


load_dotenv()


NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "bolt://localhost:7687",
)

NEO4J_USERNAME = os.getenv(
    "NEO4J_USERNAME",
    "neo4j",
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD",
)

NEO4J_DATABASE = os.getenv(
    "NEO4J_DATABASE",
    "neo4j",
)


NOISE_ENTITIES = {
    "This",
    "Instead",
    "The",
    "A",
    "An",
    "Which",
    "What",
    "Who",
    "Whose",
    "Any",
    "Likewise",
    "Descriptions",
    "Registry",
}


def get_graph_neighbors(
    entity_name: str,
    limit: int = 20,
) -> list[str]:
    """
    Retrieve graph neighbors for a seed entity.
    """

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USERNAME,
            NEO4J_PASSWORD,
        ),
    )

    neighbors: list[str] = []

    with driver.session(
        database=NEO4J_DATABASE,
    ) as session:

        result = session.run(
            """
            MATCH (seed:Entity)

            WHERE
                toLower(seed.name)
                CONTAINS
                toLower($entity_name)

                OR

                toLower($entity_name)
                CONTAINS
                toLower(seed.name)

            MATCH
                (seed)-[:CO_OCCURS_WITH]-
                (related:Entity)

            RETURN DISTINCT
                related.name AS name

            LIMIT $limit
            """,
            entity_name=entity_name,
            limit=limit,
        )

        for record in result:
            name = record["name"]

            if not name:
                continue

            if name in NOISE_ENTITIES:
                continue

            neighbors.append(name)

    driver.close()

    return neighbors


def extract_seed_entity(
    question: str,
) -> str:
    """
    Simple seed extraction for the demo.

    Looks for the most likely capitalized named entity.
    """

    words = question.replace(
        "?",
        "",
    ).split()

    candidates: list[str] = []

    current: list[str] = []

    stopwords = {
        "Which",
        "What",
        "Who",
        "Whose",
        "Where",
        "When",
        "According",
        "In",
        "On",
        "To",
        "The",
        "A",
        "An",
    }

    for word in words:

        clean = word.strip(
            ",.:;()[]{}\"'"
        )

        if (
            clean
            and clean[0].isupper()
            and clean not in stopwords
        ):
            current.append(clean)

        else:
            if len(current) >= 2:
                candidates.append(
                    " ".join(current)
                )

            current = []

    if len(current) >= 2:
        candidates.append(
            " ".join(current)
        )

    if candidates:
        return candidates[-1]

    return question


def choose_expansion_entities(
    neighbors: list[str],
) -> list[str]:
    """
    Prefer likely organizations/factions.
    """

    keywords = (
        "Cartel",
        "Vanguard",
        "House",
        "Order",
        "Guild",
        "Legion",
        "Council",
        "Faction",
        "Brotherhood",
        "Covenant",
    )

    preferred = [
        name
        for name in neighbors
        if any(
            keyword in name
            for keyword in keywords
        )
    ]

    if preferred:
        return preferred[:3]

    return neighbors[:3]


def result_text(
    result: dict[str, Any],
) -> str:

    return (
        result.get("text")
        or result.get("content")
        or result.get("document")
        or ""
    )


def result_metadata(
    result: dict[str, Any],
) -> dict[str, Any]:

    return (
        result.get("metadata")
        or {}
    )


def result_chunk_id(
    result: dict[str, Any],
) -> str | None:

    metadata = result_metadata(
        result
    )

    return (
        result.get("chunk_id")
        or result.get("id")
        or metadata.get("chunk_id")
    )


def hybrid_retrieve(
    question: str,
    seed_entity: str,
    top_k: int = 10,
) -> tuple[
    list[str],
    list[str],
    list[dict[str, Any]],
]:
    """
    Graph hop followed by vector retrieval.
    """

    print(
        "\n[1] Running graph retrieval..."
    )

    neighbors = get_graph_neighbors(
        seed_entity,
        limit=20,
    )

    print(
        "Graph neighbors:",
        neighbors,
    )

    expansion_entities = (
        choose_expansion_entities(
            neighbors
        )
    )

    print(
        "Expansion entities:",
        expansion_entities,
    )

    print(
        "\n[2] Running vector retrieval..."
    )

    vector_repo = VectorRepository()

    results: list[dict[str, Any]] = []
    seen_chunks: set[str] = set()

    # Search original question too.
    queries = [question]

    for entity in expansion_entities:
        queries.append(
            f"{entity} {question}"
        )

        queries.append(
            f"{entity} accord war conflict "
            f"victory won winner"
        )

    for query in queries:

        retrieved = vector_repo.search(
            query,
            top_k=top_k,
        )

        for result in retrieved:

            chunk_id = result_chunk_id(
                result
            )

            if not chunk_id:
                continue

            if chunk_id in seen_chunks:
                continue

            seen_chunks.add(
                chunk_id
            )

            results.append(
                result
            )

    return (
        neighbors,
        expansion_entities,
        results,
    )


def build_context(
    results: list[dict[str, Any]],
    max_items: int = 8,
) -> str:
    """
    Build compact provenance-aware evidence context.
    """

    sections: list[str] = []

    for index, result in enumerate(
        results[:max_items],
        start=1,
    ):

        metadata = result_metadata(
            result
        )

        text = result_text(
            result
        )

        chunk_id = result_chunk_id(
            result
        )

        source_type = metadata.get(
            "source_type",
            "unknown",
        )

        document_id = metadata.get(
            "document_id",
            "unknown",
        )

        section = (
            f"[Evidence {index}]\n"
            f"Chunk ID: {chunk_id}\n"
            f"Document ID: {document_id}\n"
            f"Source Type: {source_type}\n"
            f"Text: {text}\n"
        )

        sections.append(
            section
        )

    return "\n".join(
        sections
    )


def build_prompt(
    question: str,
    seed_entity: str,
    graph_neighbors: list[str],
    evidence_context: str,
) -> str:
    """
    Grounded answer prompt.
    """

    graph_context = ", ".join(
        graph_neighbors[:12]
    )

    return f"""
You are answering a question about the fictional Ashen Era Archive.

Use ONLY the supplied evidence.

The system performed hybrid retrieval:
1. Neo4j graph retrieval identified entities related to the seed entity.
2. Vector retrieval found supporting passages from the archive.

Do not invent missing information.

If the evidence is insufficient, explicitly say that the available evidence is insufficient.

For multi-hop questions, briefly connect the intermediate facts before giving the final answer.

When the question asks for one specific type of item, return the item matching that type.
For example, if evidence lists both a war and an accord but the question asks "Which accord?", return the accord.

Cite supporting evidence using [Evidence N].

Question:
{question}

Seed entity:
{seed_entity}

Graph-related entities:
{graph_context}

Retrieved evidence:
{evidence_context}

Return exactly this structure:

Answer:
<concise final answer>

Reasoning:
<1-3 concise sentences connecting the evidence>

Citations:
[Evidence N], [Evidence N]
""".strip()


def generate_answer(
    question: str,
    seed_entity: str,
    graph_neighbors: list[str],
    results: list[dict[str, Any]],
) -> str:

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

    llm = LLMClient()

    # If your LLMClient uses a different method name,
    # change this one line accordingly.
    response = llm.generate(
        prompt
    )

    return response


def print_evidence(
    results: list[dict[str, Any]],
    max_items: int = 15,
) -> None:

    print("\n" + "=" * 70)
    print("RETRIEVED EVIDENCE")
    print("=" * 70)

    for index, result in enumerate(
        results[:max_items],
        start=1,
    ):

        metadata = result_metadata(
            result
        )

        print(
            f"\n[Evidence {index}]"
        )

        print(
            "Chunk:",
            result_chunk_id(result),
        )

        print(
            "Document:",
            metadata.get(
                "document_id"
            ),
        )

        print(
            "Source:",
            metadata.get(
                "source_type"
            ),
        )

        print(
            "Text:",
            result_text(result)[:600],
        )


def main() -> None:

    print("=" * 70)
    print("ASHENGRAPH — HYBRID GRAPH RAG")
    print("=" * 70)

    question = input(
        "\nAsk a question: "
    ).strip()

    if not question:
        print(
            "No question supplied."
        )

        return

    seed_entity = extract_seed_entity(
        question
    )

    print(
        "\nDetected seed entity:",
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

    if not results:
        print(
            "\nNo evidence retrieved."
        )

        return

    print_evidence(
        results,
        max_items=8,
    )

    print("\n" + "=" * 70)
    print("GENERATING ANSWER")
    print("=" * 70)

    try:

        answer = generate_answer(
            question=question,
            seed_entity=seed_entity,
            graph_neighbors=graph_neighbors,
            results=results,
        )

        print()
        print(answer)

    except Exception as exc:

        print(
            "\nAnswer generation failed:"
        )

        print(exc)

        print(
            "\nThe retrieval stage still "
            "completed successfully."
        )


if __name__ == "__main__":
    main()