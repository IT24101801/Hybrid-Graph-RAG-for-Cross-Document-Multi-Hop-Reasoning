from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Set

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os


load_dotenv()


INPUT_PATH = Path(
    "data/processed/graph_candidates.json"
)


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


# Words that frequently look like entities
# but are not useful graph concepts.
STOPWORDS = {
    "The",
    "A",
    "An",
    "According",
    "Volume",
    "Chapter",
    "Figure",
    "Plate",
    "Official",
    "Age",
    "What",
    "Which",
    "Whose",
    "In",
    "On",
    "To",
    "From",
    "Its",
}


def extract_entities(text: str) -> List[str]:
    """
    Fast heuristic entity extraction.

    Finds sequences of capitalized words such as:

        House Morvain
        Ashen Vanguard
        Ravena Stormwell
        War of Drowned Light
        Greyfell Citadel

    No LLM/API calls are required.
    """

    pattern = (
        r"\b(?:"
        r"[A-Z][A-Za-z'\-]+"
        r"(?:\s+(?:of|the|and|de|von|van))?"
        r"\s*){1,6}"
    )

    matches = re.findall(
        pattern,
        text,
    )

    entities: Set[str] = set()

    for match in matches:

        entity = " ".join(
            match.split()
        ).strip()

        if len(entity) < 3:
            continue

        if entity in STOPWORDS:
            continue

        # Remove trailing connector words.
        entity = re.sub(
            r"\s+(of|the|and)$",
            "",
            entity,
        )

        if not entity:
            continue

        entities.add(entity)

    return sorted(entities)


def build_graph() -> None:

    if not NEO4J_PASSWORD:
        raise RuntimeError(
            "NEO4J_PASSWORD is not configured."
        )

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        candidates = json.load(f)

    print(
        f"Loaded {len(candidates)} candidates."
    )

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(
            NEO4J_USERNAME,
            NEO4J_PASSWORD,
        ),
    )

    driver.verify_connectivity()

    print(
        "Connected to Neo4j successfully."
    )

    total_entities = 0
    total_connections = 0

    with driver.session(
        database=NEO4J_DATABASE,
    ) as session:

        # Helpful constraints / indexes.
        session.run(
            """
            CREATE CONSTRAINT chunk_id_unique
            IF NOT EXISTS
            FOR (c:Chunk)
            REQUIRE c.chunk_id IS UNIQUE
            """
        )

        session.run(
            """
            CREATE CONSTRAINT entity_name_unique
            IF NOT EXISTS
            FOR (e:Entity)
            REQUIRE e.name IS UNIQUE
            """
        )

        for index, item in enumerate(
            candidates,
            start=1,
        ):

            chunk_id = item.get(
                "chunk_id"
            )

            text = (
                item.get("text")
                or item.get("content")
                or ""
            )

            metadata = (
                item.get("metadata")
                or {}
            )

            document_id = (
                metadata.get("document_id")
            )

            source_type = (
                metadata.get("source_type")
            )

            entities = extract_entities(
                text
            )

            print(
                f"[{index}/{len(candidates)}] "
                f"{len(entities)} entities"
            )

            # Create chunk node.
            session.run(
                """
                MERGE (c:Chunk {
                    chunk_id: $chunk_id
                })

                SET
                    c.text = $text,
                    c.document_id = $document_id,
                    c.source_type = $source_type
                """,
                chunk_id=chunk_id,
                text=text,
                document_id=document_id,
                source_type=source_type,
            )

            # Create entities and connect them
            # to their source chunk.
            for entity in entities:

                session.run(
                    """
                    MATCH (c:Chunk {
                        chunk_id: $chunk_id
                    })

                    MERGE (e:Entity {
                        name: $entity
                    })

                    MERGE (e)-[
                        :MENTIONED_IN
                    ]->(c)
                    """,
                    chunk_id=chunk_id,
                    entity=entity,
                )

                total_entities += 1

            # Connect entities occurring in
            # the same evidence chunk.
            for i in range(
                len(entities)
            ):

                for j in range(
                    i + 1,
                    len(entities),
                ):

                    entity_a = entities[i]
                    entity_b = entities[j]

                    session.run(
                        """
                        MATCH
                            (a:Entity {
                                name: $entity_a
                            }),
                            (b:Entity {
                                name: $entity_b
                            }),
                            (c:Chunk {
                                chunk_id: $chunk_id
                            })

                        MERGE (a)-[
                            r:CO_OCCURS_WITH
                        ]->(b)

                        ON CREATE SET
                            r.count = 1

                        ON MATCH SET
                            r.count =
                                coalesce(
                                    r.count,
                                    0
                                ) + 1

                        MERGE (a)-[
                            :SUPPORTED_BY
                        ]->(c)

                        MERGE (b)-[
                            :SUPPORTED_BY
                        ]->(c)
                        """,
                        entity_a=entity_a,
                        entity_b=entity_b,
                        chunk_id=chunk_id,
                    )

                    total_connections += 1

    driver.close()

    print()
    print("=" * 70)
    print("FAST KNOWLEDGE GRAPH COMPLETE")
    print("=" * 70)

    print(
        f"Candidate chunks : "
        f"{len(candidates)}"
    )

    print(
        f"Entity mentions  : "
        f"{total_entities}"
    )

    print(
        f"Connections      : "
        f"{total_connections}"
    )

    print("=" * 70)


if __name__ == "__main__":
    build_graph()