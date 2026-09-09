ENTITY_NEIGHBORS = """
MATCH (e:Entity {name: $name})-[r:CLAIM]-(other:Entity)
RETURN e.name AS entity,
       other.name AS neighbor,
       r.predicate AS predicate,
       r.evidence AS evidence,
       r.chunk_id AS chunk_id,
       r.document_id AS document_id,
       r.source_type AS source_type
LIMIT $limit
"""
