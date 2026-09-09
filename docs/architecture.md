# AshenGraph Architecture

## 1. Overview

AshenGraph is a Hybrid Graph Retrieval-Augmented Generation (Graph RAG) system developed for the SLIIT Codefest 2026 AI Competition, Sub-track 1B: **Connecting Facts Across Thousands of Pages**.

The main challenge addressed by AshenGraph is answering questions where the required facts are distributed across multiple documents.

A traditional RAG system normally retrieves passages that are semantically similar to a question. This can fail when no individual passage contains the complete answer.

AshenGraph combines:

- Multi-format document ingestion
- Provenance-aware text processing
- Local semantic embeddings
- ChromaDB vector retrieval
- Neo4j graph retrieval
- Graph-guided query expansion
- Cross-document evidence collection
- LLM-based grounded answer generation
- Evidence citations

The core design principle is:

> Use the graph to discover relationships and use vector retrieval to discover supporting evidence across the wider document corpus.

---

## 2. High-Level Architecture

```text
                 ASHEN ERA ARCHIVE
                        │
                        ▼
              ┌───────────────────┐
              │     INGESTION     │
              │ PDF / DOCX / MD   │
              │       TXT         │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ CLEANING +        │
              │ NORMALIZATION     │
              └─────────┬─────────┘
                        │
                        ▼
              ┌───────────────────┐
              │ PROVENANCE-AWARE  │
              │     CHUNKING      │
              └─────────┬─────────┘
                        │
              ┌─────────┴──────────┐
              │                    │
              ▼                    ▼
     ┌─────────────────┐   ┌─────────────────┐
     │ BGE EMBEDDINGS  │   │ ENTITY / GRAPH  │
     │  Local Model    │   │ CONSTRUCTION    │
     └────────┬────────┘   └────────┬────────┘
              │                     │
              ▼                     ▼
     ┌─────────────────┐   ┌─────────────────┐
     │    ChromaDB     │   │      Neo4j      │
     │  Vector Store   │   │ Knowledge Graph │
     └────────┬────────┘   └────────┬────────┘
              │                     │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  HYBRID RETRIEVAL   │
              │ Graph + Vector RAG  │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ CROSS-DOCUMENT      │
              │ EVIDENCE CONTEXT    │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   OPENROUTER LLM    │
              │ Grounded Generation │
              └──────────┬──────────┘
                         │
                         ▼
                ANSWER + CITATIONS
```

---

## 3. Document Ingestion Layer

The ingestion layer converts supported source files into a normalized internal representation.

Supported formats:

- PDF
- DOCX
- Markdown
- Plain text

Relevant modules:

```text
app/ingestion/
├── loader.py
├── pdf_loader.py
├── docx_loader.py
├── markdown_loader.py
└── text_loader.py
```

The central loader identifies the file type and delegates extraction to the appropriate format-specific loader.

During development, the ingestion pipeline processed:

```text
Documents loaded : 254
Failed           : 0
Skipped          : 0
Chunks generated : 31,393
```

The number of loaded documents is lower than the total archive size because the current pipeline focuses on supported text-readable document formats and does not independently process all standalone image/scan assets.

---

## 4. Cleaning and Chunking

After ingestion, extracted text is cleaned and divided into smaller retrieval units.

Relevant modules:

```text
app/processing/
├── cleaner.py
├── chunker.py
└── metadata.py
```

The chunking process is provenance-aware.

Each chunk retains metadata such as:

```text
chunk_id
document_id
file_name
file_path
source_type
page
section
chapter
chunk_index
start_char
end_char
extraction_method
extraction_confidence
```

This allows evidence returned by the retrieval system to remain traceable to its source.

---

## 5. Source Provenance

AshenGraph preserves different source categories, including:

```text
chronicle
wiki
official_codex
ephemera
unknown
```

This is important because the archive may contain conflicting accounts.

Rather than discarding contradictory information during ingestion, AshenGraph keeps source provenance available to the downstream retrieval and reasoning process.

Source authority can therefore be considered when interpreting conflicting evidence.

---

## 6. Embedding Layer

AshenGraph uses:

```text
BAAI/bge-small-en-v1.5
```

through Sentence Transformers.

The model runs locally.

The resulting embeddings are normalized and have 384 dimensions.

The local model was selected to reduce dependency on external embedding APIs and avoid embedding API rate limits during indexing and querying.

---

## 7. Vector Database

ChromaDB is used as the persistent vector store.

Its purpose is to provide semantic retrieval across the broader text corpus.

The vector index is built with:

```bash
python -m scripts.build_vectors
```

At query time:

```text
Question
   ↓
BGE Embedding
   ↓
ChromaDB
   ↓
Semantically Relevant Chunks
```

Vector retrieval is particularly useful when the exact wording used by the question differs from the wording used in the source documents.

---

## 8. Knowledge Graph

Neo4j is used as the graph database.

The lightweight MVP graph represents:

```text
(:Entity)
(:Chunk)
```

with relationships such as:

```text
(:Entity)-[:MENTIONED_IN]->(:Chunk)

(:Entity)-[:CO_OCCURS_WITH]->(:Entity)

(:Entity)-[:SUPPORTED_BY]->(:Chunk)
```

The graph provides a way to discover entities related to an entity found in the user's question.

For example:

```text
Ederon Fellgard
       │
       ▼
The Iron-Ring Cartel
```

This intermediate entity can then be used to guide another semantic search.

---

## 9. Graph Construction

An LLM-based entity, relation, and claim extraction pipeline was implemented and prototyped.

However, performing LLM extraction over all 31,393 chunks was impractical within the available development constraints due to API latency and rate limiting.

The final MVP therefore uses targeted graph materialization.

The process is:

```text
Development Questions
        │
        ▼
Semantic Retrieval
        │
        ▼
High-Value Candidate Chunks
        │
        ▼
Lightweight Entity Extraction
        │
        ▼
Neo4j Graph
```

Candidate selection produced:

```text
107 unique candidate chunks
```

The lightweight graph build produced approximately:

```text
Candidate chunks : 107
Entity mentions  : 673
Connections      : 2793
```

The graph is therefore intentionally described as a lightweight entity/co-occurrence graph rather than a complete semantic knowledge graph.

---

## 10. Hybrid Retrieval

Hybrid retrieval is the central component of AshenGraph.

It combines:

```text
Neo4j graph retrieval
        +
ChromaDB semantic retrieval
```

The runtime process is:

```text
Question
   │
   ▼
Seed Entity Detection
   │
   ▼
Graph Neighbor Retrieval
   │
   ▼
Candidate Intermediate Entities
   │
   ▼
Graph-Guided Query Expansion
   │
   ▼
Vector Retrieval
   │
   ▼
Evidence Deduplication
   │
   ▼
Evidence Context
```

If useful graph relationships are unavailable, the original question can still be sent through semantic vector retrieval.

This provides a vector-only fallback path.

---

## 11. Multi-Hop Example

Consider:

```text
Which accord was ultimately won by the faction
of which Ederon Fellgard is a member?
```

### Hop 1

The system identifies:

```text
Ederon Fellgard
```

Graph retrieval discovers:

```text
The Iron-Ring Cartel
```

Supporting evidence establishes:

```text
Ederon Fellgard
    ↓ member of
The Iron-Ring Cartel
```

### Hop 2

AshenGraph uses the intermediate entity to perform graph-guided semantic retrieval.

Another document provides:

```text
The Iron-Ring Cartel
    ↓ victor of
The Leaden Accord
```

The final reasoning chain becomes:

```text
Ederon Fellgard
        │
        │ member of
        ▼
The Iron-Ring Cartel
        │
        │ victor of
        ▼
The Leaden Accord
```

Final answer:

```text
The Leaden Accord
```

This demonstrates cross-document multi-hop reasoning where the complete answer is not dependent on a single source passage.

---

## 12. LLM Generation

After retrieval, evidence is formatted into numbered evidence blocks.

The final LLM is accessed through OpenRouter.

The LLM receives:

- the user question
- detected entity information
- retrieved evidence
- source/provenance information
- grounding instructions

The model is instructed to:

- answer using retrieved evidence
- avoid unsupported claims
- provide concise reasoning
- cite evidence
- state when evidence is insufficient

Example:

```text
Answer:
The Leaden Accord

Reasoning:
Ederon Fellgard is a member of The Iron-Ring Cartel.
The Iron-Ring Cartel is recorded as having won
The Leaden Accord.

Citations:
[Evidence 3], [Evidence 13]
```

---

## 13. API Layer

FastAPI exposes the working system through an HTTP API.

Main endpoints:

```text
GET /health
POST /ask
```

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

The `/ask` endpoint executes the hybrid retrieval and generation pipeline for a supplied question.

---

## 14. Architectural Strengths

The architecture provides several benefits:

### Separation of Concerns

Ingestion, processing, embeddings, graph operations, retrieval, reasoning, generation, and API serving are separated into modules.

### Provenance Preservation

Retrieved evidence can be traced back to its source.

### Hybrid Retrieval

Graph and vector search provide complementary retrieval capabilities.

### Reduced External Dependency

Embeddings run locally.

### Graceful Fallback

Semantic vector retrieval remains available when graph coverage is insufficient.

### Inspectable Reasoning

Intermediate graph entities and retrieved evidence can be inspected during development and demonstration.

---

## 15. Architecture Summary

AshenGraph uses:

```text
Graph retrieval
     ↓
Relationship discovery

Vector retrieval
     ↓
Evidence discovery

LLM
     ↓
Grounded synthesis
```

The final architecture is therefore:

> **Graph for relationships + vectors for semantic evidence + LLM for grounded synthesis.**