from __future__ import annotations

from typing import Dict, List

from app.graph.neo4j_client import Neo4jClient


class GraphRepository:
    def __init__(self, client: Neo4jClient | None = None) -> None:
        self.client = client or Neo4jClient()

    def search_entities(self, names: List[str], limit: int = 20) -> List[Dict]:
        if not names:
            return []
        query = """
        MATCH (e:Entity)
        WHERE any(name IN $names WHERE toLower(e.name) CONTAINS toLower(name)
                                 OR toLower(name) CONTAINS toLower(e.name))
        RETURN e.name AS name
        LIMIT $limit
        """
        return self.client.execute_read(query, names=names, limit=limit)

    def multi_hop_paths(
        self,
        entity_names: List[str],
        max_hops: int = 3,
        limit: int = 50,
    ) -> List[Dict]:
        # Relationship length cannot be parameterized in Cypher, so validate/cast first.
        max_hops = max(1, min(int(max_hops), 5))
        query = f"""
        MATCH p=(a:Entity)-[:CLAIM*1..{max_hops}]-(b:Entity)
        WHERE a.name IN $entity_names
        RETURN
            [n IN nodes(p) | n.name] AS nodes,
            [r IN relationships(p) | {{
                predicate: r.predicate,
                evidence: r.evidence,
                chunk_id: r.chunk_id,
                document_id: r.document_id,
                source_type: r.source_type
            }}] AS relationships,
            length(p) AS hops
        LIMIT $limit
        """
        return self.client.execute_read(
            query,
            entity_names=entity_names,
            limit=limit,
        )
