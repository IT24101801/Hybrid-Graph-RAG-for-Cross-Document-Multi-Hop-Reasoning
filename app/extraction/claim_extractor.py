from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from app.extraction.entity_extractor import EntityExtractor
from app.extraction.relation_extractor import RelationExtractor


@dataclass
class Claim:
    subject: str
    predicate: str
    object: str
    evidence: str
    chunk_id: str
    document_id: str | None = None
    source_type: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ClaimExtractor:
    def __init__(
        self,
        entity_extractor: EntityExtractor | None = None,
        relation_extractor: RelationExtractor | None = None,
    ) -> None:
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.relation_extractor = relation_extractor or RelationExtractor()

    def extract_from_chunk(self, chunk: Any) -> Dict[str, Any]:
        text = getattr(chunk, "text", None) or getattr(chunk, "content", "")
        metadata = getattr(chunk, "metadata", None)

        chunk_id = getattr(chunk, "chunk_id", None) or getattr(metadata, "chunk_id", None)
        document_id = getattr(metadata, "document_id", None)
        source_type = getattr(metadata, "source_type", None)

        entities = self.entity_extractor.extract(text)
        relations = self.relation_extractor.extract(text)

        claims = [
            Claim(
                subject=r["subject"],
                predicate=r["predicate"],
                object=r["object"],
                evidence=r.get("evidence", ""),
                chunk_id=chunk_id,
                document_id=document_id,
                source_type=source_type,
            ).to_dict()
            for r in relations
        ]

        return {"entities": entities, "claims": claims}
