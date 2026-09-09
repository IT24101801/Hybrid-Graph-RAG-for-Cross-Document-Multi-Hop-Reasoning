# AshenGraph

## Hybrid Graph RAG for Cross-Document Multi-Hop Reasoning

AshenGraph is a Hybrid Graph Retrieval-Augmented Generation (Graph RAG) system developed for the **SLIIT Codefest 2026 AI Competition – Sub-track 1B: Connecting Facts Across Thousands of Pages**.

The system is designed to answer questions whose evidence is distributed across multiple documents and cannot necessarily be answered from a single retrieved passage.

AshenGraph combines:

- Multi-format document ingestion
- Text cleaning and provenance-aware chunking
- Local semantic embeddings
- ChromaDB vector search
- Neo4j knowledge graph retrieval
- Graph-guided query expansion
- Multi-hop evidence retrieval
- Source-aware evidence handling
- LLM-based grounded answer generation
- Evidence citations
- FastAPI serving

The central idea is simple:

> **Vector retrieval finds relevant passages. Graph retrieval identifies relationships between entities. The two are combined to retrieve evidence across documents before an LLM generates the final grounded answer.**

---

# 1. Problem

Traditional RAG systems generally follow:

```text
Question
   ↓
Vector Search
   ↓
Top-K Similar Chunks
   ↓
LLM
   ↓
Answer
```

This works well when the answer exists directly inside one retrieved passage.

However, many questions require multiple reasoning steps.

For example:

```text
Which accord was ultimately won by the faction
of which Ederon Fellgard is a member?
```

One document establishes:

```text
Ederon Fellgard
    ↓ member of
The Iron-Ring Cartel
```

Another document establishes:

```text
The Iron-Ring Cartel
    ↓ victor of
The Leaden Accord
```

Neither fact alone fully answers the question.

AshenGraph therefore performs:

```text
Question
   ↓
Entity Detection
   ↓
Knowledge Graph
   ↓
Related Entity / Organization
   ↓
Graph-Guided Vector Retrieval
   ↓
Cross-Document Evidence
   ↓
LLM Reasoning
   ↓
Grounded Answer + Citations
```

---

# 2. Architecture

```text
                    ASHEN ERA ARCHIVE
                           │
                           ▼
                 ┌──────────────────┐
                 │    INGESTION     │
                 │ PDF / DOCX / MD  │
                 │       TXT        │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │     CLEANING     │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   PROVENANCE-    │
                 │  AWARE CHUNKING  │
                 └────────┬─────────┘
                          │
               ┌──────────┴───────────┐
               │                      │
               ▼                      ▼
      ┌─────────────────┐    ┌─────────────────┐
      │ LOCAL EMBEDDING │    │ ENTITY / GRAPH  │
      │ BGE-small-en-v1.5│   │ CONSTRUCTION    │
      └────────┬────────┘    └────────┬────────┘
               │                      │
               ▼                      ▼
      ┌─────────────────┐    ┌─────────────────┐
      │    ChromaDB     │    │      Neo4j      │
      │  Vector Store   │    │ Knowledge Graph │
      └────────┬────────┘    └────────┬────────┘
               │                      │
               └──────────┬───────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ HYBRID RETRIEVAL │
                 │ Graph + Vector   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ MULTI-HOP        │
                 │ EVIDENCE FUSION  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ OPENROUTER LLM   │
                 │ GROUNDED ANSWER  │
                 └────────┬─────────┘
                          │
                          ▼
                 ANSWER + CITATIONS
```

---

# 3. Core Technologies

| Component | Technology |
|---|---|
| Language | Python 3 |
| API | FastAPI |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Embedding runtime | Sentence Transformers |
| Vector Database | ChromaDB |
| Graph Database | Neo4j |
| LLM Gateway | OpenRouter |
| PDF Processing | pypdf |
| DOCX Processing | python-docx |
| Configuration | python-dotenv |
| HTTP | requests |
| Validation | Pydantic |
| API Server | Uvicorn |

---

# 4. Repository Structure

```text
Hybrid-Graph-RAG-for-Cross-Document-Multi-Hop-Reasoning/
│
├── app/
│   │
│   ├── ingestion/
│   │   ├── loader.py
│   │   ├── pdf_loader.py
│   │   ├── docx_loader.py
│   │   ├── markdown_loader.py
│   │   └── text_loader.py
│   │
│   ├── processing/
│   │   ├── cleaner.py
│   │   ├── chunker.py
│   │   └── metadata.py
│   │
│   ├── embeddings/
│   │   └── embedder.py
│   │
│   ├── vector_store/
│   │   ├── chroma_client.py
│   │   └── vector_repository.py
│   │
│   ├── extraction/
│   │   ├── entity_extractor.py
│   │   ├── relation_extractor.py
│   │   ├── claim_extractor.py
│   │   └── entity_resolver.py
│   │
│   ├── graph/
│   │   ├── neo4j_client.py
│   │   ├── graph_builder.py
│   │   ├── graph_repository.py
│   │   └── graph_queries.py
│   │
│   ├── retrieval/
│   │   ├── query_analyzer.py
│   │   ├── vector_retriever.py
│   │   ├── graph_retriever.py
│   │   ├── evidence_ranker.py
│   │   └── hybrid_retriever.py
│   │
│   ├── reasoning/
│   │   ├── multi_hop.py
│   │   ├── conflict_detector.py
│   │   └── context_builder.py
│   │
│   ├── generation/
│   │   ├── llm_client.py
│   │   ├── prompt_builder.py
│   │   ├── answer_generator.py
│   │   └── citation_builder.py
│   │
│   ├── evaluation/
│   │   ├── retrieval_metrics.py
│   │   ├── answer_metrics.py
│   │   └── evaluator.py
│   │
│   └── main.py
│
├── scripts/
│   ├── ingest.py
│   ├── build_vectors.py
│   ├── select_graph_candidates.py
│   ├── extract_graph_candidates.py
│   ├── build_fast_graph.py
│   ├── test_graph_retrieval.py
│   ├── test_hybrid_multihop.py
│   ├── ask_hybrid.py
│   └── test_sample_questions.py
│
├── data/
│   ├── raw/
│   └── processed/
│       ├── documents/
│       ├── chunks/
│       ├── reports/
│       └── evaluation/
│
├── chroma_db/
├── docs/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

Some experimental modules are retained in the repository to document the evolution of the architecture. The final MVP execution path uses the lightweight graph construction and hybrid retrieval scripts described below.

---

# 5. Document Ingestion

AshenGraph currently supports:

```text
.pdf
.docx
.md
.markdown
.txt
```

The ingestion layer normalizes different file types into a common internal document representation.

Run:

```bash
python -m scripts.ingest
```

A completed development ingestion produced:

```text
Documents loaded : 254
Failed           : 0
Skipped          : 0
Chunks generated : 31,393
```

Processed data is written to:

```text
data/processed/documents/documents.json
data/processed/chunks/chunks.json
data/processed/reports/ingestion_report.json
```

---

# 6. Provenance-Aware Chunking

Every chunk retains provenance information so retrieved evidence can be traced back to its origin.

Metadata may include:

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

This information is carried through retrieval and supplied to the answer-generation layer.

Example:

```text
Chunk:
doc_1a4e757bd605_chunk_0001_d18e35

Document:
doc_1a4e757bd605

Source:
wiki
```

---

# 7. Source Types

AshenGraph distinguishes between several source categories:

```text
chronicle
wiki
official_codex
ephemera
unknown
```

Source provenance is retained during retrieval.

Source authority can be used when ranking conflicting evidence rather than automatically treating every retrieved passage as equally authoritative.

This is particularly useful for archive questions containing conflicting historical accounts.

---

# 8. Local Embeddings

The final system uses:

```text
BAAI/bge-small-en-v1.5
```

through Sentence Transformers.

Embeddings are generated locally and normalized before storage.

This approach was selected because it:

- avoids embedding API rate limits
- removes per-request embedding cost
- provides reproducible embeddings
- works efficiently for the competition corpus
- allows local semantic retrieval

The embedding dimension is:

```text
384
```

---

# 9. ChromaDB Vector Store

Embeddings are stored in a persistent local ChromaDB collection.

Example environment configuration:

```env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=ashen_era_chunks_bge
```

Build the vector index:

```bash
python -m scripts.build_vectors
```

The vector database provides semantic retrieval over the full text corpus.

---

# 10. Knowledge Graph

Neo4j is used to represent relationships between entities and evidence chunks.

The lightweight graph contains:

```text
(:Entity)
(:Chunk)
```

with relationships including:

```text
(:Entity)-[:MENTIONED_IN]->(:Chunk)

(:Entity)-[:CO_OCCURS_WITH]->(:Entity)

(:Entity)-[:SUPPORTED_BY]->(:Chunk)
```

This allows the system to start with an entity in a question and discover entities that appear in related evidence.

---

# 11. Graph Construction Strategy

An LLM-based entity/relation/claim extraction pipeline was implemented and prototyped.

However, performing LLM extraction over all 31,393 chunks was not practical within the competition development constraints because of API latency and rate limits.

The final MVP therefore uses a lightweight graph materialization strategy.

First, high-value candidate chunks are selected using semantic retrieval:

```bash
python -m scripts.select_graph_candidates
```

During development this produced:

```text
Questions evaluated : 20
Unique candidates   : 107
```

The candidate graph can then be built without additional LLM API calls:

```bash
python -m scripts.build_fast_graph
```

A completed graph build produced:

```text
Candidate chunks : 107
Entity mentions  : 673
Connections      : 2793
```

The lightweight graph uses heuristic entity extraction and entity co-occurrence relationships.

This is intentionally described as a **lightweight/co-occurrence knowledge graph**, rather than claiming every edge is a fully semantically extracted relation.

---

# 12. Why Targeted Graph Materialization?

Building a graph from every chunk using an external LLM would have created unnecessary latency, cost, and rate-limit risk.

AshenGraph instead follows:

```text
Full Corpus
    ↓
Vector Retrieval
    ↓
High-Value Candidate Evidence
    ↓
Graph Materialization
```

The vector database still indexes the broader text corpus.

Therefore, when graph coverage is incomplete, semantic vector retrieval can continue to provide evidence.

This provides a practical balance between:

```text
Graph precision
Retrieval coverage
API cost
Latency
Development time
```

---

# 13. Hybrid Multi-Hop Retrieval

The core AshenGraph retrieval strategy combines Neo4j and ChromaDB.

Consider:

```text
Which accord was ultimately won by the faction
of which Ederon Fellgard is a member?
```

## Hop 1 — Graph Retrieval

The graph identifies:

```text
Ederon Fellgard
       │
       └── The Iron-Ring Cartel
```

The supporting archive evidence states that Ederon Fellgard is a member of The Iron-Ring Cartel.

## Hop 2 — Graph-Guided Vector Retrieval

The discovered organization is inserted into an expanded semantic query.

Conceptually:

```text
The Iron-Ring Cartel
+ accord
+ conflict
+ victory
+ won
```

Vector retrieval then discovers another passage stating that the Cartel was a victor of:

```text
The Winter Reckoning
The Leaden Accord
```

Because the question specifically asks for an **accord**, the final grounded answer is:

```text
The Leaden Accord
```

This demonstrates the primary objective of AshenGraph:

> Connect evidence distributed across documents through graph relationships and semantic retrieval.

---

# 14. Query Pipeline

At runtime:

```text
User Question
     │
     ▼
Seed Entity Detection
     │
     ▼
Neo4j Graph Retrieval
     │
     ▼
Related Entities
     │
     ▼
Query Expansion
     │
     ▼
BGE Embedding
     │
     ▼
ChromaDB Search
     │
     ▼
Evidence Deduplication
     │
     ▼
Provenance Context
     │
     ▼
OpenRouter LLM
     │
     ▼
Answer + Reasoning + Citations
```

---

# 15. Grounded Generation

Retrieved evidence is supplied to the LLM as numbered evidence blocks.

Example:

```text
[Evidence 3]

Chunk ID:
doc_1a4e757bd605_chunk_0001_d18e35

Source Type:
wiki

Text:
Ederon Fellgard ... is a member of The Iron-Ring Cartel.
```

The generation prompt instructs the model to:

- use only supplied evidence
- avoid inventing missing information
- explain multi-hop connections briefly
- return a concise final answer
- cite evidence using `[Evidence N]`
- report insufficient evidence when appropriate

Example output:

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

# 16. Conflict Handling

The archive can contain conflicting claims.

AshenGraph retains:

```text
document identity
source type
chunk provenance
retrieved evidence
```

rather than discarding conflicting information during ingestion.

This allows downstream reasoning to consider source authority.

One development example concerned the founding year of Gloamreach. Retrieved passages contained conflicting dates, while the official codex provided an authoritative date.

The system answered:

```text
246 AS
```

while noting the conflicting retrieved accounts.

---

# 17. API

AshenGraph exposes a FastAPI service.

Start it with:

```bash
python -m uvicorn app.main:app --reload
```

The API runs locally at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "service": "AshenGraph"
}
```

## Ask

```http
POST /ask
```

Request:

```json
{
  "question": "Which accord was ultimately won by the faction of which Ederon Fellgard is a member?"
}
```

Example response structure:

```json
{
  "question": "Which accord was ultimately won by the faction of which Ederon Fellgard is a member?",
  "seed_entity": "Ederon Fellgard",
  "answer": "Answer:\nThe Leaden Accord\n\nReasoning:\n...",
  "evidence_count": 15
}
```

---

# 18. CLI Demo

The easiest way to demonstrate the complete system is:

```bash
python -m scripts.ask_hybrid
```

Then enter:

```text
Which accord was ultimately won by the faction of which Ederon Fellgard is a member?
```

The system will show:

```text
Detected seed entity
        ↓
Graph neighbors
        ↓
Expansion entities
        ↓
Retrieved evidence
        ↓
Generated answer
        ↓
Evidence citations
```

This is the recommended live demonstration path because every stage of the reasoning pipeline is visible.

---

# 19. Development-Set Smoke Testing

A manual smoke test was performed over textual multi-hop questions from the provided development question set.

Run:

```bash
python -m scripts.test_sample_questions
```

Recorded summary:

| Category | Count |
|---|---:|
| Questions tested | 9 |
| Clear successes | 5 |
| Generation failure | 1 |
| Needs manual review | 3 |

This should **not** be interpreted as a formal benchmark accuracy score.

It is a development-set smoke test used to identify successful paths and remaining failure modes.

Examples of successful outputs included:

| Task | System Output |
|---|---|
| Ederon Fellgard → faction → accord | The Leaden Accord |
| Ravena Stormwell → faction → war | The War of Drowned Light |
| Cerys Sablewood → relic → location | Cindermere Hold |
| Gloamreach founding year | 246 AS |
| Gauntlet of Sorrowfell forged year | 391 AS |

Evaluation notes can be stored under:

```text
data/processed/evaluation/
```

---

# 20. Failure Handling

AshenGraph is instructed not to fabricate answers when retrieved evidence is insufficient.

For example, when asked for information contained only in an unavailable figure plate, the system can respond:

```text
The available evidence is insufficient to determine
the numerical rating from the official threat-classification plate.
```

This is preferable to hallucinating a value unsupported by retrieved evidence.

---

# 21. Current Limitations

The current competition MVP has several known limitations.

### Image and Figure Understanding

The ingestion pipeline currently extracts textual content from supported document formats.

It does **not** currently perform:

```text
OCR
image understanding
figure interpretation
visual question answering
```

Therefore, questions whose answers exist only inside images, portraits, banners, or numbered figure plates may not be answerable.

This was observed during development testing of questions involving:

- banner emblems
- portrait objects
- threat-classification plates
- artifact figure plates
- visual attunement values

### Heuristic Graph Extraction

The fast graph uses regex/heuristic entity detection.

Consequently, some noisy entities may appear, such as generic capitalized words or partially extracted phrases.

The retrieval layer filters some of this noise.

### Targeted Graph Coverage

The final lightweight graph is materialized from high-value candidate chunks rather than every chunk in the corpus.

This means graph coverage is not exhaustive.

ChromaDB vector retrieval over the broader text corpus provides a fallback when graph evidence is unavailable.

### LLM Variability

The generation layer relies on an external LLM through OpenRouter.

Responses may therefore vary, and free/shared model routing can introduce:

```text
latency
rate limits
formatting variability
occasional generation failures
```

### Entity Resolution

Entity normalization in the lightweight graph is intentionally simple.

Future versions should improve alias resolution and canonicalization.

---

# 22. Design Decisions

## Why BGE Instead of an Embedding API?

External embedding APIs introduced rate-limit constraints during development.

The final implementation uses:

```text
BAAI/bge-small-en-v1.5
```

locally.

This provides:

```text
No embedding API dependency
No embedding request cost
Fast repeated queries
Reproducibility
Offline vector generation
```

## Why Neo4j?

Neo4j provides a natural representation for:

```text
Entity → Entity relationships
Entity → Evidence relationships
Multi-hop traversal
Graph exploration
```

It also makes the reasoning process easier to inspect during development and demonstration.

## Why ChromaDB?

ChromaDB provides lightweight persistent vector storage with simple local development.

It is well suited to an MVP where semantic retrieval must operate over thousands of chunks without requiring an external hosted vector database.

## Why Hybrid Retrieval?

Vector search and graph search solve different problems.

Vector retrieval is strong at:

```text
semantic similarity
fuzzy matching
passage discovery
```

Graph retrieval is strong at:

```text
explicit relationships
entity connectivity
multi-hop navigation
```

AshenGraph combines both rather than relying exclusively on either.

---

# 23. Installation

Clone the repository:

```bash
git clone <repository-url>
```

Enter the project:

```bash
cd Hybrid-Graph-RAG-for-Cross-Document-Multi-Hop-Reasoning
```

Create a virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

---

# 24. Environment Configuration

Create:

```text
.env
```

Example:

```env
APP_NAME=AshenGraph
APP_ENV=development
DEBUG=true

OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=YOUR_OPENROUTER_MODEL

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=ashen_era_chunks_bge

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=YOUR_NEO4J_PASSWORD
NEO4J_DATABASE=neo4j

RAW_DATA_DIR=./data/raw
PROCESSED_DATA_DIR=./data/processed

VECTOR_TOP_K=10
GRAPH_MAX_HOPS=3
FINAL_EVIDENCE_TOP_K=15
```

Never commit `.env`.

---

# 25. Recommended `.gitignore`

```gitignore
# Environment
.env
.venv/
venv/

# Python
__pycache__/
*.py[cod]
*.pyo

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Local databases
chroma_db/

# Logs
*.log

# Temporary files
tmp/
temp/
```

Do not ignore submission artifacts that are explicitly required to be present in the final repository.

---

# 26. Running the Complete Pipeline

The typical setup sequence is:

### 1. Place corpus files

```text
data/raw/
```

### 2. Ingest

```bash
python -m scripts.ingest
```

### 3. Build vector database

```bash
python -m scripts.build_vectors
```

### 4. Select graph candidates

```bash
python -m scripts.select_graph_candidates
```

### 5. Start Neo4j

Ensure the configured Neo4j instance is running.

### 6. Build lightweight graph

```bash
python -m scripts.build_fast_graph
```

### 7. Test hybrid retrieval

```bash
python -m scripts.test_hybrid_multihop
```

### 8. Ask a question

```bash
python -m scripts.ask_hybrid
```

### 9. Run API

```bash
python -m uvicorn app.main:app --reload
```

---

# 27. Reproducible Demo

Recommended demo question:

```text
Which accord was ultimately won by the faction
of which Ederon Fellgard is a member?
```

Expected reasoning path:

```text
Question
   │
   ▼
Ederon Fellgard
   │
   │ Graph relationship
   ▼
The Iron-Ring Cartel
   │
   │ Graph-guided semantic retrieval
   ▼
Historical victory evidence
   │
   ▼
The Leaden Accord
```

Expected final answer:

```text
The Leaden Accord
```

This question clearly demonstrates cross-document multi-hop reasoning.

---

# 28. Engineering Practices

The project follows a modular architecture separating:

```text
ingestion
processing
embeddings
vector storage
knowledge extraction
graph storage
retrieval
reasoning
generation
evaluation
API serving
```

Other engineering practices include:

- environment-based configuration
- secret separation through `.env`
- persistent vector storage
- persistent graph storage
- provenance-preserving data structures
- modular loaders
- explicit failure handling
- API error handling
- incremental Git feature development
- reproducible CLI scripts
- development-set smoke testing
- documented limitations

---

# 29. Reliability and Technical Judgment

Several engineering decisions were changed during development based on observed system behavior.

### Embedding Strategy

An external embedding service was initially explored.

Rate limiting made large-scale indexing unreliable within the development window.

The embedding layer was therefore migrated to local BGE embeddings.

### Knowledge Extraction Strategy

LLM-based entity and relation extraction was implemented and tested.

Although functional, applying it to tens of thousands of chunks introduced unacceptable latency and API dependency.

The final MVP therefore uses:

```text
semantic candidate selection
        +
lightweight graph materialization
```

while retaining the richer extraction components as an experimental path.

### Retrieval Strategy

Pure graph traversal did not always expose sufficient second-hop evidence.

Instead of forcing all reasoning into Neo4j, the final system uses the graph to identify useful intermediate entities and then performs semantic retrieval over the broader corpus.

This became the final hybrid strategy:

```text
Graph for relationships
+
Vector search for evidence discovery
+
LLM for grounded synthesis
```

---

# 30. Future Improvements

Given additional development time, the following improvements would be prioritized:

1. Multimodal ingestion for figures, portraits, maps, banners, and plates.
2. OCR support for simulated scans.
3. Batched full-corpus graph construction.
4. Stronger named-entity recognition.
5. Canonical entity resolution and alias handling.
6. Typed semantic graph relationships.
7. Improved source-authority scoring.
8. Cross-encoder evidence reranking.
9. Automated multi-hop query decomposition.
10. Formal evaluation against labeled answers.
11. Retrieval precision/recall measurements.
12. Better contradiction detection.
13. LLM response schema validation.
14. Caching for repeated queries.
15. Graph visualization for the user interface.

---

# 31. AI Usage Disclosure

AI-assisted development tools were used during this project.

AI assistance contributed to areas including:

```text
architecture exploration
code scaffolding
debugging
Git workflow guidance
retrieval design
Neo4j query development
prompt design
documentation
evaluation planning
```

All generated or suggested code was integrated, executed, tested, debugged, and adapted as part of the development process.

Important architectural decisions were also revised based on observed runtime behavior rather than accepting generated suggestions unchanged.

Examples include:

```text
External embeddings
    ↓
Observed rate limits
    ↓
Local BGE embeddings
```

and:

```text
Full-corpus LLM graph extraction
    ↓
Observed latency/rate limits
    ↓
Targeted lightweight graph construction
```

Full AI conversation logs should be included with the final competition submission where required.

---

# 32. Security

Secrets must be stored only in:

```text
.env
```

Do not commit:

```text
OPENROUTER_API_KEY
NEO4J_PASSWORD
other credentials
```

Before submission, verify:

```bash
git status
```

and inspect repository history to ensure credentials were not accidentally committed.

---

# 33. Submission Notes

Before producing the final Git repository archive:

```bash
git status
```

should report a clean working tree.

Ensure the final repository contains the required project documentation and submission artifacts.

Because Git history is part of the engineering record, preserve the `.git` directory when preparing any submission archive that explicitly requires repository history.

---

# 34. Summary

AshenGraph demonstrates a practical Hybrid Graph RAG architecture for connecting facts distributed across a large fictional archive.

The final MVP combines:

```text
Multi-format ingestion
        +
Provenance-aware chunking
        +
Local BGE embeddings
        +
ChromaDB semantic retrieval
        +
Neo4j entity graph
        +
Graph-guided query expansion
        +
Cross-document evidence retrieval
        +
OpenRouter grounded generation
        +
Evidence citations
```

The key contribution is not simply retrieving passages that resemble a question.

Instead, AshenGraph uses relationships discovered in one piece of evidence to guide retrieval toward another piece of evidence:

```text
Find the entity
      ↓
Discover the relationship
      ↓
Follow the intermediate entity
      ↓
Retrieve supporting evidence elsewhere
      ↓
Generate a grounded answer
```

That is the core principle behind **AshenGraph: Hybrid Graph RAG for Cross-Document Multi-Hop Reasoning**.
