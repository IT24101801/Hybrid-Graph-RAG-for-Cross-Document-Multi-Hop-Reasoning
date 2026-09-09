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


def extract_query_entities(
    query: str,
) -> list[str]:
    """
    Lightweight query entity extraction.
    """

    pattern = (
        r"\b(?:"
        r"[A-Z][A-Za-z'\-]+"
        r"(?:\s+(?:of|the|and))?"
        r"\s*){1,6}"
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

        if len(entity) >= 3:
            entities.append(entity)

    return entities


def search_graph(
    query: str,
    limit: int = 10,
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

    results = []

    with driver.session(
        database=NEO4J_DATABASE,
    ) as session:

        for query_entity in query_entities:

            records = session.run(
                """
                MATCH (e:Entity)
                WHERE
                    toLower(e.name)
                    CONTAINS
                    toLower($query_entity)

                    OR

                    toLower($query_entity)
                    CONTAINS
                    toLower(e.name)

                MATCH (e)-[:MENTIONED_IN]->(c:Chunk)

                OPTIONAL MATCH
                    (e)-[:CO_OCCURS_WITH]-
                    (related:Entity)

                RETURN DISTINCT
                    e.name AS entity,
                    related.name AS related_entity,
                    c.chunk_id AS chunk_id,
                    c.text AS text,
                    c.document_id AS document_id,
                    c.source_type AS source_type

                LIMIT $limit
                """,
                query_entity=query_entity,
                limit=limit,
            )

            for record in records:

                results.append(
                    {
                        "entity": record[
                            "entity"
                        ],
                        "related_entity": record[
                            "related_entity"
                        ],
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

    return results


def main() -> None:

    query = (
        "Which accord was ultimately won "
        "by the faction of which "
        "Ederon Fellgard is a member?"
    )

    results = search_graph(
        query,
        limit=10,
    )

    print("\n" + "=" * 70)
    print("GRAPH RESULTS")
    print("=" * 70)

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\nRESULT {index}"
        )

        print(
            "Entity:",
            result["entity"],
        )

        print(
            "Related:",
            result[
                "related_entity"
            ],
        )

        print(
            "Chunk:",
            result[
                "chunk_id"
            ],
        )

        print(
            "Source:",
            result[
                "source_type"
            ],
        )

        print(
            "Text:",
            result["text"][:500],
        )


if __name__ == "__main__":
    main()