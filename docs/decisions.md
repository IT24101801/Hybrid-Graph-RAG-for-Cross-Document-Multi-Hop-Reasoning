# AshenGraph — Technical Decisions

## 1. Purpose

This document records the major technical decisions made while developing AshenGraph.

The final architecture was not selected in a single step. Several approaches were tested and changed after observing practical limitations such as rate limits, latency, graph quality, and retrieval behavior.

---

## 2. Decision: Hybrid Graph RAG Instead of Vector-Only RAG

### Problem

The selected challenge requires answering questions where information may be distributed across multiple documents.

A vector-only RAG pipeline can retrieve semantically relevant passages, but it does not explicitly model relationships between entities.

### Decision

Use a hybrid architecture combining:

```text
Neo4j graph retrieval
+
ChromaDB vector retrieval
```

### Reason

Graph retrieval helps discover intermediate entities while vector retrieval provides broader semantic evidence discovery.

Example:

```text
Ederon Fellgard
        ↓
The Iron-Ring Cartel
        ↓
The Leaden Accord
```

The graph helps identify the organization, while vector retrieval finds evidence about the organization's historical victory.

### Trade-off

The hybrid architecture introduces additional complexity compared with a simple vector RAG pipeline, but provides a more appropriate mechanism for multi-hop questions.

---

## 3. Decision: Local BGE Embeddings

### Initial Approach

An external embedding API was initially explored.

### Problem Observed

During development, external embedding requests encountered rate limiting.

Large-scale indexing became slower and less predictable.

### Decision

Switch to:

```text
BAAI/bge-small-en-v1.5
```

using Sentence Transformers locally.

### Benefits

- No embedding API request cost
- No embedding API rate-limit dependency
- Fast repeated queries after model loading
- Reproducible vector generation
- Local processing
- Suitable embedding size for the development corpus

### Result

The local model generates normalized 384-dimensional embeddings that are stored in ChromaDB.

---

## 4. Decision: ChromaDB for Vector Storage

### Alternatives

Possible alternatives included hosted vector databases and other local vector stores.

### Decision

Use ChromaDB.

### Reason

ChromaDB provides:

- simple Python integration
- persistent local storage
- metadata storage
- semantic similarity search
- minimal infrastructure requirements

It was suitable for rapidly building a reproducible competition MVP.

---

## 5. Decision: Neo4j for Graph Storage

### Decision

Use Neo4j as the graph database.

### Reason

The challenge involves relationships between:

```text
people
factions
places
events
artifacts
documents
```

Neo4j naturally represents these relationships and supports graph traversal.

It also provides an inspectable graph model that is useful for debugging and demonstration.

---

## 6. Decision: Do Not Perform Full-Corpus LLM Graph Extraction

### Initial Design

The initial graph architecture included LLM-based extraction of:

- entities
- relations
- claims

Components were implemented for this richer extraction strategy.

### Test Result

The approach worked on small samples.

However, the processed corpus contained:

```text
31,393 chunks
```

Running multiple external LLM calls over every chunk would introduce substantial:

- latency
- API usage
- rate-limit exposure
- failure risk

Small extraction experiments were already noticeably slow.

### Decision

Do not perform full-corpus LLM extraction for the competition MVP.

Instead, use targeted graph construction.

### Final Strategy

```text
Question Set
    ↓
Vector Retrieval
    ↓
Candidate Chunks
    ↓
Lightweight Entity Extraction
    ↓
Neo4j
```

During development:

```text
107 unique candidate chunks
```

were selected for graph construction.

### Trade-off

This substantially reduces graph construction cost and latency but results in incomplete graph coverage.

The vector store remains available as a broader retrieval mechanism.

---

## 7. Decision: Lightweight Co-Occurrence Graph

### Problem

Rich semantic relationship extraction through an LLM was too expensive to apply at full scale during the available development period.

### Decision

Build a lightweight graph using heuristic entity extraction and co-occurrence.

The graph uses structures such as:

```text
Entity
Chunk
MENTIONED_IN
CO_OCCURS_WITH
SUPPORTED_BY
```

### Result

The graph build produced approximately:

```text
107 candidate chunks
673 entity mentions
2793 connections
```

### Limitation

Co-occurrence does not necessarily imply a meaningful semantic relationship.

The system therefore uses graph neighbors primarily for retrieval expansion rather than treating every graph edge as a verified factual relationship.

---

## 8. Decision: Graph-Guided Vector Expansion

### Initial Attempt

Pure second-hop graph traversal was tested.

### Problem

The lightweight graph did not always contain a sufficiently clean semantic path to the final answer.

### Observation

For the Ederon Fellgard example, graph retrieval successfully discovered:

```text
The Iron-Ring Cartel
```

but semantic retrieval was better at discovering passages describing the Cartel's historical victories.

### Decision

Use graph output to expand vector retrieval.

Final strategy:

```text
Question
    ↓
Graph
    ↓
Intermediate Entity
    ↓
Expanded Vector Query
    ↓
Additional Evidence
```

### Reason

This allows each retrieval technology to perform the task it handles best.

Neo4j:

```text
relationship discovery
```

ChromaDB:

```text
semantic passage discovery
```

---

## 9. Decision: Preserve Vector-Only Fallback

### Problem

The graph is targeted and therefore does not contain every possible entity.

### Decision

Always retain semantic retrieval using the original user question.

If graph expansion produces no useful entities, vector retrieval can still return evidence.

### Benefit

This prevents complete system failure when graph coverage is missing.

---

## 10. Decision: Preserve Provenance

### Problem

The Ashen Era Archive contains sources with different levels of reliability and potentially conflicting claims.

### Decision

Keep provenance metadata throughout the pipeline.

This includes information such as:

```text
document_id
chunk_id
source_type
file information
page information
```

### Reason

The answer-generation layer needs to know where evidence originated.

This also makes debugging and citation generation easier.

---

## 11. Decision: Source Authority Should Influence Ranking, Not Automatically Define Truth

### Problem

Different archive sources can disagree.

A naive system could either ignore conflicts or assume the first retrieved source is correct.

### Decision

Preserve conflicting evidence and use source authority as a signal during interpretation.

For example:

```text
official_codex
```

may carry greater authority for an exact recorded value than an informal account.

### Benefit

This better reflects realistic enterprise document environments where sources may conflict.

---

## 12. Decision: Use OpenRouter Only Where LLM Reasoning Is Most Valuable

### Decision

Use the external LLM primarily for final grounded synthesis rather than for every stage of the production pipeline.

### Reason

Local deterministic components are used where practical:

```text
Ingestion       → local
Cleaning        → local
Chunking        → local
Embeddings      → local
Vector search   → local
Graph database  → local
Final synthesis → external LLM
```

This reduces external API dependency and limits rate-limit exposure.

---

## 13. Decision: Explicitly Report Insufficient Evidence

### Problem

Some development questions depend on visual information contained in images or figure plates.

The current text ingestion pipeline cannot recover those values.

### Decision

Instruct the answer generator to report insufficient evidence rather than invent an answer.

Example:

```text
The available evidence is insufficient to determine
the numerical rating from the official threat-classification plate.
```

### Reason

A grounded failure is preferable to a hallucinated answer.

---

## 14. Decision: FastAPI for Demonstration and Integration

### Decision

Expose AshenGraph through FastAPI.

### Reason

FastAPI provides:

- simple request/response models
- automatic Swagger UI
- easy local testing
- a clean integration boundary for future interfaces

The Swagger UI also provides a convenient way to demonstrate the prototype end-to-end.

---

## 15. Key Technical Judgment Summary

The most important changes made during development were:

```text
External embeddings
        ↓
Observed API rate limits
        ↓
Local BGE embeddings
```

```text
Full-corpus LLM graph extraction
        ↓
Observed latency and API constraints
        ↓
Targeted lightweight graph construction
```

```text
Pure graph multi-hop retrieval
        ↓
Incomplete/noisy graph paths
        ↓
Graph-guided vector retrieval
```

These changes reflect a deliberate focus on building a working, reproducible end-to-end system rather than preserving an architecture that was theoretically richer but operationally unreliable.

---

## 16. Final Design Principle

The final design can be summarized as:

> Use deterministic/local components where possible, use graph retrieval to discover relationships, use semantic retrieval for broad evidence discovery, and use the LLM only after relevant evidence has been collected.