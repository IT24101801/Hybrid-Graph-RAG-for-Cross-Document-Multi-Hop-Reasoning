from __future__ import annotations

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

from app.vector_store.vector_repository import VectorRepository


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


def get_graph_neighbors(
    entity_name: str,
    limit: int = 15,
) -> list[str]:
    """
    Get entities connected to the seed entity
    through the lightweight knowledge graph.
    """

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USERNAME,
            NEO4J_PASSWORD,
        ),
    )

    neighbors = []

    with driver.session(
        database=NEO4J_DATABASE,
    ) as session:

        result = session.run(
            """
            MATCH (seed:Entity)
            WHERE toLower(seed.name)
                  CONTAINS
                  toLower($entity_name)

            MATCH (seed)-[:CO_OCCURS_WITH]-(related:Entity)

            RETURN DISTINCT
                related.name AS name

            LIMIT $limit
            """,
            entity_name=entity_name,
            limit=limit,
        )

        for record in result:
            name = record["name"]

            if name:
                neighbors.append(name)

    driver.close()

    return neighbors


def print_vector_result(
    number: int,
    result: dict,
) -> None:

    metadata = (
        result.get("metadata")
        or {}
    )

    text = (
        result.get("text")
        or result.get("content")
        or result.get("document")
        or ""
    )

    chunk_id = (
        result.get("chunk_id")
        or result.get("id")
        or metadata.get("chunk_id")
    )

    score = (
        result.get("score")
        or result.get("similarity")
        or result.get("distance")
    )

    print("\n" + "-" * 70)

    print(
        f"RESULT {number}"
    )

    print(
        "Chunk:",
        chunk_id,
    )

    print(
        "Score:",
        score,
    )

    print(
        "Source:",
        metadata.get("source_type"),
    )

    print(
        "Document:",
        metadata.get("document_id"),
    )

    print(
        "Text:",
        text[:800],
    )


def main() -> None:

    question = (
        "Which accord was ultimately won "
        "by the faction of which "
        "Ederon Fellgard is a member?"
    )

    seed_entity = "Ederon Fellgard"

    print("=" * 70)
    print("HYBRID MULTI-HOP RETRIEVAL")
    print("=" * 70)

    print(
        "\nQuestion:",
        question,
    )

    print(
        "\nSeed entity:",
        seed_entity,
    )

    # -------------------------------------------------
    # HOP 1 — GRAPH
    # -------------------------------------------------

    neighbors = get_graph_neighbors(
        seed_entity,
        limit=20,
    )

    print("\nGRAPH NEIGHBORS")

    for neighbor in neighbors:
        print(
            " -",
            neighbor,
        )

    # We know from graph evidence that
    # The Iron-Ring Cartel is the useful faction.
    faction_candidates = [
        n
        for n in neighbors
        if (
            "Cartel" in n
            or "Vanguard" in n
            or "House" in n
            or "Order" in n
            or "Guild" in n
            or "Faction" in n
        )
    ]

    if not faction_candidates:
        print(
            "\nNo obvious faction detected."
        )

        # Fall back to all graph neighbors.
        faction_candidates = neighbors[:5]

    print(
        "\nFACTION CANDIDATES:",
        faction_candidates,
    )

    # -------------------------------------------------
    # HOP 2 — VECTOR RETRIEVAL
    # -------------------------------------------------

    vector_repo = VectorRepository()

    all_results = []
    seen_chunks = set()

    for faction in faction_candidates:

        expanded_query = (
            f"{faction} accord war conflict "
            f"victory won winner "
            f"{question}"
        )

        print(
            "\nVector expansion query:",
            expanded_query,
        )

        results = vector_repo.search(
            expanded_query,
            top_k=10,
        )

        for result in results:

            metadata = (
                result.get("metadata")
                or {}
            )

            chunk_id = (
                result.get("chunk_id")
                or result.get("id")
                or metadata.get("chunk_id")
            )

            if chunk_id in seen_chunks:
                continue

            seen_chunks.add(
                chunk_id
            )

            all_results.append(
                result
            )

    print("\n" + "=" * 70)
    print("HYBRID EVIDENCE")
    print("=" * 70)

    for index, result in enumerate(
        all_results[:15],
        start=1,
    ):
        print_vector_result(
            index,
            result,
        )


if __name__ == "__main__":
    main()