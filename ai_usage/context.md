# AI Collaboration Context

## Project

AshenGraph — Hybrid Graph RAG for Cross-Document Multi-Hop Reasoning

## Competition

SLIIT Codefest 2026 AI Competition

## Selected Track

Sub-track 1B — Connecting Facts Across Thousands of Pages

---

## Purpose of This File

This file provides context for the AI conversation transcripts included in this directory.

The purpose is to make it easier for judges or reviewers to understand:

- how AI was used
- how conversations evolved
- how generated suggestions influenced development
- which decisions were made by the team
- how failures changed the implementation

The full conversation transcripts are provided separately as plain-text files.

---

# Development Context

The project was developed under a limited competition development window.

The goal was to create a working AI assistant capable of connecting facts distributed across multiple documents in the Ashen Era Archive.

The team chose to build a Hybrid Graph RAG architecture.

The final pipeline consists of:

```text
Document Corpus
      ↓
Ingestion
      ↓
Cleaning
      ↓
Provenance-Aware Chunking
      ↓
 ┌────┴─────┐
 ↓          ↓
BGE       Entity
Embedding Extraction
 ↓          ↓
ChromaDB   Neo4j
 └────┬─────┘
      ↓
Hybrid Retrieval
      ↓
Multi-Hop Evidence
      ↓
OpenRouter LLM
      ↓
Answer + Citations