from __future__ import annotations

import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase


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


QUERY_STOPWORDS = {
    "Which",
    "What",
    "Who",
    "Whose",
    "Where",
    "When",
    "Why",
    "How",
    "According",
    "The",
    "A",
    "An",
    "In",
    "On",
    "To",
    "From",
}


NOISY_ENTITIES = {
    "This",
    "Instead",
    "The",
    "A",
    "An",
    "Which",
    "What",
}


def extract_query_entities(
    query: str,
) -> list[str]:

    pattern = (
        r"\b(?:"
        r"[A-Z][A-Za-z'\-]+"
        r"(?:\s+(?:of|the|and))?"
        r"\s*){1,5}"
    )

    matches = re.findall(
        pattern,
        query,
    )

    entities = []

    for match in matches:

        entity = " ".join(
            match.split()
        ).strip()

        if entity in QUERY_STOPWORDS:
            continue

        if len(entity) < 3:
            continue

        entities.append(entity)

    return entities


def search_graph(
    query: str,
    limit: int = 20,
) -> list[dict]:

    query_entities = extract_query_entities(
        query
    )

    print(
        "Query entities:",
        query_entities,
    )

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USERNAME,
            NEO4J_PASSWORD,
        ),
    )

    all_results = []
    seen = set()

    with driver.session(
        database=NEO4J_DATABASE,
    ) as session:

        for query_entity in query_entities:

            records = session.run(
                """
                MATCH (seed:Entity)

                WHERE
                    toLower(seed.name)
                    CONTAINS
                    toLower($query_entity)

                    OR

                    toLower($query_entity)
                    CONTAINS
                    toLower(seed.name)

                MATCH
                    (seed)
                    -[:CO_OCCURS_WITH]-
                    (related:Entity)

                MATCH
                    (related)
                    -[:MENTIONED_IN]->
                    (evidence:Chunk)

                RETURN DISTINCT
                    seed.name AS seed_entity,
                    related.name AS related_entity,
                    evidence.chunk_id AS chunk_id,
                    evidence.text AS text,
                    evidence.document_id AS document_id,
                    evidence.source_type AS source_type

                LIMIT $limit
                """,
                query_entity=query_entity,
                limit=limit,
            )

            for record in records:

                related = record[
                    "related_entity"
                ]

                if related in NOISY_ENTITIES:
                    continue

                key = (
                    record["chunk_id"],
                    related,
                )

                if key in seen:
                    continue

                seen.add(key)

                all_results.append(
                    {
                        "seed_entity": record[
                            "seed_entity"
                        ],
                        "related_entity": related,
                        "chunk_id": record[
                            "chunk_id"
                        ],
                        "text": record[
                            "text"
                        ],
                        "document_id": record[
                            "document_id"
                        ],
                        "source_type": record[
                            "source_type"
                        ],
                    }
                )

    driver.close()

    return all_results


def main() -> None:

    query = (
        "Which accord was ultimately won "
        "by the faction of which "
        "Ederon Fellgard is a member?"
    )

    results = search_graph(
        query,
        limit=30,
    )

    print("\n" + "=" * 70)
    print("MULTI-HOP GRAPH RESULTS")
    print("=" * 70)

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\nRESULT {index}"
        )

        print(
            "Seed:",
            result["seed_entity"],
        )

        print(
            "Related:",
            result["related_entity"],
        )

        print(
            "Source:",
            result["source_type"],
        )

        print(
            "Chunk:",
            result["chunk_id"],
        )

        print(
            "Text:",
            result["text"][:600],
        )


if __name__ == "__main__":
    main()