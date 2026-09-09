# AshenGraph — Limitations

## 1. Overview

AshenGraph is a working competition MVP for cross-document textual multi-hop reasoning.

The system has known limitations that are documented here to make the scope and current behavior clear.

---

## 2. Image and Figure Understanding

### Current Limitation

The ingestion pipeline primarily extracts textual content.

It currently does not provide full:

- image understanding
- visual question answering
- figure interpretation
- diagram interpretation
- OCR for all simulated scans

### Impact

Questions whose answers exist only inside visual content may not be answerable.

Development examples included questions about:

- a central emblem on a banner
- an object held in a portrait
- a numerical value on a threat-classification plate
- artifact attunement values shown only on figure plates

### Current Behavior

Instead of inventing a value, the system attempts to report that the available evidence is insufficient.

### Future Improvement

Introduce a multimodal ingestion pipeline using:

```text
PDF image extraction
        ↓
OCR / Vision Model
        ↓
Figure Metadata
        ↓
Multimodal Embeddings
        ↓
Hybrid Retrieval
```

---

## 3. Partial Corpus Coverage in Text Ingestion

The competition archive contains mixed document and visual formats.

The current ingestion run loaded:

```text
254 documents
```

and generated:

```text
31,393 chunks
```

The system does not claim that all archive assets were independently processed.

Unsupported standalone images and some scan-based information remain outside the current textual retrieval pipeline.

---

## 4. Targeted Graph Coverage

### Current Design

The vector store covers the broader processed text corpus, while the lightweight Neo4j graph is constructed from a smaller candidate set.

During development:

```text
107 unique candidate chunks
```

were selected for graph materialization.

### Impact

An entity that exists in the corpus may not exist in the graph.

### Mitigation

AshenGraph preserves vector retrieval using the original question.

Therefore:

```text
Graph match available
    ↓
Graph + vector retrieval

No useful graph match
    ↓
Vector retrieval fallback
```

### Future Improvement

Build the graph incrementally over the full corpus using batched local NER and relation extraction.

---

## 5. Heuristic Entity Extraction

### Current Limitation

The lightweight graph uses heuristic extraction based partly on capitalization patterns.

This can create noisy graph entities.

Examples observed during development included generic terms and incomplete phrases.

### Impact

Noisy entities can:

- reduce graph precision
- produce irrelevant graph neighbors
- generate weak query expansions

### Mitigation

Expansion logic filters some obviously irrelevant entities and semantic retrieval still evaluates the resulting queries.

### Future Improvement

Replace heuristic extraction with:

- trained named-entity recognition
- domain-specific entity dictionaries
- alias resolution
- entity normalization
- batched LLM extraction where practical

---

## 6. Co-Occurrence Is Not a Semantic Relation

The lightweight graph includes:

```text
CO_OCCURS_WITH
```

relationships.

Two entities appearing in the same chunk does not guarantee a meaningful factual relationship.

For this reason, AshenGraph does not assume every co-occurrence edge is a verified fact.

Instead, graph neighbors are primarily used to guide further evidence retrieval.

A richer future graph should use typed relationships such as:

```text
MEMBER_OF
WON
LOCATED_AT
WIELDS
FOUNDED_IN
PARTICIPATED_IN
```

with direct evidence attached to every relationship.

---

## 7. Entity Resolution

Aliases and alternative entity names are not fully normalized.

For example, a character or organization may appear under:

- full name
- shortened name
- title
- epithet
- possessive form

These variants may become separate graph entities.

Future work should introduce canonical entity IDs and alias mappings.

---

## 8. Seed Entity Detection

The current query analyzer uses lightweight rules to identify important entities from questions.

This works well for many proper names but can fail on more complex question structures.

For example, a full sentence or incomplete name fragment can occasionally be interpreted as the seed entity.

### Future Improvement

Use structured query analysis to extract:

```text
target entity
relation requested
intermediate entity type
answer type
```

before retrieval begins.

---

## 9. LLM Generation Variability

The final generation stage uses an external LLM through OpenRouter.

Depending on model availability and routing, this can introduce:

- response latency
- rate limits
- formatting variability
- occasional malformed responses

One development test produced an invalid generation response even though retrieval completed.

### Mitigation

The LLM client implements retry behavior for request failures.

### Future Improvement

Add:

- strict JSON output schemas
- automatic response validation
- regeneration on malformed output
- caching
- deterministic fallback formatting

---

## 10. Evidence Ranking

The current retrieval pipeline can return many evidence chunks.

The most important second-hop evidence is not always ranked first.

This means the final LLM may need to inspect a larger context window to find the decisive evidence.

### Future Improvement

Introduce:

- cross-encoder reranking
- source-authority scoring
- relation-aware ranking
- graph-distance scoring
- question keyword scoring

---

## 11. Conflict Resolution

AshenGraph preserves source type and can reason about source authority, but conflict resolution is not yet a complete formal subsystem.

A stronger future implementation would assign explicit authority scores and detect contradictory claims before answer generation.

Example:

```text
Claim A
    ↓
Source Authority

Claim B
    ↓
Source Authority

Conflict Detector
    ↓
Ranked Resolution
```

---

## 12. Development-Set Evaluation

A manual smoke test was performed on nine textual questions.

The recorded classification was:

```text
Questions tested   : 9
Clear successes    : 5
Generation failure : 1
Needs review       : 3
```

This is not presented as a formal accuracy benchmark.

The purpose of the test was to identify working paths and failure modes before submission.

The final judging questions are unpublished, so development-set success does not guarantee equivalent performance on unseen questions.

---

## 13. Candidate Selection and Generalization

The lightweight graph was constructed using candidate chunks retrieved around the development question set.

This improves development-time efficiency but creates a risk that graph coverage is biased toward development questions.

The full vector index reduces this risk because vector retrieval remains available outside graph coverage.

A production system should construct or incrementally expand its graph independently of known evaluation questions.

---

## 14. No Production-Scale Performance Optimization

The current system is a competition prototype.

It has not been optimized for:

- high concurrent request volume
- distributed execution
- horizontal scaling
- large multi-user workloads
- production monitoring

The architecture could be extended with caching, asynchronous jobs, model serving, and distributed storage if required.

---

## 15. Summary

The major current limitations are:

1. No full multimodal/image understanding.
2. Partial coverage of visual and scan-based archive content.
3. Targeted rather than exhaustive graph materialization.
4. Noisy heuristic entity extraction.
5. Co-occurrence edges are not verified semantic relations.
6. Limited alias/entity resolution.
7. Lightweight seed entity detection.
8. External LLM variability.
9. Basic evidence ranking.
10. Incomplete formal conflict resolution.

Despite these limitations, the MVP demonstrates the core objective:

> retrieving and connecting textual evidence distributed across documents using a combination of graph relationships, semantic retrieval, and grounded LLM generation.