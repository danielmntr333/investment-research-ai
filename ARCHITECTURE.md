# Architecture Documentation

## System Architecture

This document provides a detailed overview of the Investment Research AI platform architecture.

## High-Level Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ◄─────► │   Backend    │ ◄─────► │  Supabase   │
│  React +TS  │  HTTPS  │   FastAPI    │   SQL   │ PostgreSQL  │
│   Vercel    │         │    Modal     │         │  + pgvector │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   LLM APIs   │
                        │ OpenAI, etc. │
                        └──────────────┘
```

## Core Components

### 1. RAG Pipeline

**Flow**: Query → Transform → Retrieve → Rerank → Generate

**Components**:
- Query Transformer (HyDE, multi-query, decomposition)
- Hybrid Retriever (vector + keyword + RRF)
- Reranker (Cohere)
- LLM Generator (OpenAI GPT-4o)

### 2. Multi-Agent System

**Agents**:
1. **Supervisor**: Routes queries to appropriate agents
2. **Research**: RAG-based document Q&A
3. **Analysis**: Comparative analysis with tools
4. **Fact-Checker**: Validates claims
5. **Web Search**: Real-time data enrichment
6. **Synthesizer**: Combines multi-agent outputs

**Orchestration**: LangGraph state machine

### 3. Evaluation Framework

**Metrics**:
- RAGAS: faithfulness, relevancy, precision, recall
- Custom: numerical accuracy, citation quality
- LLM Judge: GPT-4 qualitative assessment

**Testing**:
- Golden dataset with 50+ test cases
- Automated regression testing
- Continuous evaluation pipeline

### 4. Data Flow

```
Document Upload
  ↓
Parse (PDF/Excel/HTML)
  ↓
Extract Metadata
  ↓
Chunk (smart, structure-aware)
  ↓
Embed (OpenAI text-embedding-3-large)
  ↓
Store (Supabase + pgvector)
```

```
User Query
  ↓
Validate Input
  ↓
Transform Query
  ↓
Hybrid Retrieval
  ↓
Rerank
  ↓
Agent Processing
  ↓
Generate Answer
  ↓
Extract Citations
  ↓
Stream to Frontend
```

## Technology Stack

See [plan.md](docs/plan.md) for complete tech stack details.

## Security Architecture

- API key authentication at the edge
- Input validation and sanitization
- Prompt injection defense
- Rate limiting per user
- PII detection (optional)

## Scalability

- Serverless backend (Modal) scales automatically
- Connection pooling for database
- Embedding cache reduces API calls
- Stateless design enables horizontal scaling

## Observability

- Structured logging (structlog)
- LLM tracing (LangSmith)
- Error tracking and alerting
- Performance metrics collection

## Cost Optimization

- Serverless architecture (pay-per-use)
- Aggressive caching (embeddings, queries)
- Efficient chunking (smaller context windows)
- Scales to zero when idle

---

For implementation details, see the specific documentation files in `docs/`.
