from __future__ import annotations

from typing import Dict, Iterable

from app.graph.neo4j_client import Neo4jClient


class GraphBuilder:
    def __init__(self, client: Neo4jClient | None = None) -> None:
        self.client = client or Neo4jClient()

    def ensure_constraints(self) -> None:
        queries = [
            "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
        ]
        for query in queries:
            self.client.execute_write(query)

    def add_claim(self, claim: Dict) -> None:
        query = """
        MERGE (s:Entity {name: $subject})
        MERGE (o:Entity {name: $object})
        MERGE (c:Chunk {chunk_id: $chunk_id})
        SET c.document_id = $document_id,
            c.source_type = $source_type

        MERGE (s)-[r:CLAIM {
            predicate: $predicate,
            object_name: $object,
            chunk_id: $chunk_id
        }]->(o)
        SET r.evidence = $evidence,
            r.document_id = $document_id,
            r.source_type = $source_type

        MERGE (c)-[:SUPPORTS]->(s)
        MERGE (c)-[:SUPPORTS]->(o)
        """
        self.client.execute_write(query, **claim)

    def add_claims(self, claims: Iterable[Dict]) -> None:
        for claim in claims:
            self.add_claim(claim)
