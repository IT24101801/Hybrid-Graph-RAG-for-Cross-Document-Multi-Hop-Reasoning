# AI Usage Disclosure

## Project

**AshenGraph — Hybrid Graph RAG for Cross-Document Multi-Hop Reasoning**

Developed for:

**SLIIT Codefest 2026 AI Competition**

Chosen track:

**Sub-track 1B — Connecting Facts Across Thousands of Pages**

---

## 1. AI Tools Used

The primary AI assistant used during the development of AshenGraph was:

### OpenAI ChatGPT

ChatGPT was used as an engineering assistant throughout the project.

It supported the team in:

- understanding the competition challenge
- exploring possible architectures
- designing the Hybrid Graph RAG pipeline
- generating initial code scaffolding
- reviewing code organization
- debugging runtime problems
- diagnosing API rate limits
- designing ingestion and chunking components
- designing vector retrieval
- designing knowledge graph construction
- designing hybrid retrieval
- writing Neo4j retrieval logic
- designing multi-hop reasoning flows
- creating FastAPI integration
- evaluating development questions
- improving Git workflow
- preparing README and technical documentation
- identifying system limitations
- preparing submission documentation

AI-generated suggestions were not accepted blindly.

The team executed the generated code, observed its behavior, reported failures back to the AI assistant, and changed the architecture based on actual results.

---

# 2. How AI Was Used

AI was used as a collaborative software engineering assistant rather than as a one-shot solution generator.

The development process followed an iterative pattern:

```text
Team identifies requirement
        ↓
Discusses approach with ChatGPT
        ↓
ChatGPT proposes architecture/code
        ↓
Team implements and executes it
        ↓
Runtime behavior is observed
        ↓
Errors / limitations are reported
        ↓
Architecture or implementation is revised
        ↓
System is tested again