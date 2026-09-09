from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.extraction.claim_extractor import ClaimExtractor
from app.graph.graph_builder import GraphBuilder


def _as_chunk(item):
    metadata = SimpleNamespace(**item.get("metadata", {}))
    return SimpleNamespace(
        text=item.get("text") or item.get("content", ""),
        chunk_id=item.get("chunk_id") or item.get("metadata", {}).get("chunk_id"),
        metadata=metadata,
    )


def main() -> None:
    chunks_path = Path("data/processed/chunks/chunks.json")
    claims_path = Path("data/processed/extracted_claims/claims.json")
    claims_path.parent.mkdir(parents=True, exist_ok=True)

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

    extractor = ClaimExtractor()
    builder = GraphBuilder()
    builder.ensure_constraints()

    all_claims = []
    for i, item in enumerate(chunks, start=1):
        result = extractor.extract_from_chunk(_as_chunk(item))
        claims = result["claims"]
        builder.add_claims(claims)
        all_claims.extend(claims)
        print(f"[{i}/{len(chunks)}] extracted {len(claims)} claims")

    claims_path.write_text(
        json.dumps(all_claims, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {len(all_claims)} claims to {claims_path}")


if __name__ == "__main__":
    main()
