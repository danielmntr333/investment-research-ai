# Investment Research AI Platform

> A production-grade AI system demonstrating advanced RAG techniques, multi-agent orchestration, and comprehensive evaluation frameworks for financial document analysis.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Database Schema](#-database-schema)
- [Getting Started](#-getting-started)
- [Advanced RAG Pipeline](#-advanced-rag-pipeline)
- [Multi-Agent System](#-multi-agent-system)
- [Evaluation Framework](#-evaluation-framework)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Performance Metrics](#-performance-metrics)

---

## 🎯 Overview

This platform showcases enterprise-level AI engineering practices through a sophisticated financial research system. Built to demonstrate advanced techniques in retrieval-augmented generation, agent orchestration, and production ML systems.

**What makes this special:**
- **Advanced RAG**: Goes beyond basic vector search with hybrid retrieval, query transformation, and reranking
- **Multi-Agent Orchestration**: LangGraph-powered agent system with supervisor pattern and specialized agents
- **Comprehensive Evaluation**: RAGAS metrics, custom financial evaluators, LLM-as-judge, and regression testing
- **Production-Ready**: Full observability, security, streaming, error handling, and deployment configurations

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React 18)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Chat UI      │  │ Doc Upload   │  │ Metrics      │  │ Agent      │ │
│  │ (Streaming)  │  │              │  │ Dashboard    │  │ Trace      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ REST API + SSE
┌────────────────────────────────┴────────────────────────────────────────┐
│                        BACKEND (FastAPI)                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      API Layer                                    │  │
│  │  /chat  /documents  /analyze  /evals  /search                    │  │
│  │  (Streaming, Auth, Validation, Error Handling)                   │  │
│  └────────────┬────────────────────────┬─────────────────────────────┘  │
│               │                        │                                │
│  ┌────────────▼────────────┐  ┌────────▼──────────────────────────┐   │
│  │   MULTI-AGENT SYSTEM    │  │     ADVANCED RAG PIPELINE         │   │
│  │   (LangGraph)           │  │                                   │   │
│  │                         │  │  ┌─────────────────────────────┐  │   │
│  │  ┌──────────────────┐   │  │  │ 1. Query Transformation     │  │   │
│  │  │   Supervisor     │   │  │  │    • HyDE                   │  │   │
│  │  │   (Routing)      │   │  │  │    • Multi-query            │  │   │
│  │  └────────┬─────────┘   │  │  │    • Decomposition          │  │   │
│  │           │              │  │  └─────────────────────────────┘  │   │
│  │  ┌────────┴─────────┐   │  │                ↓                  │   │
│  │  │                  │   │  │  ┌─────────────────────────────┐  │   │
│  │  │  Specialized     │   │  │  │ 2. Hybrid Retrieval         │  │   │
│  │  │  Agents:         │   │  │  │    • Vector Search (cosine) │  │   │
│  │  │                  │   │  │  │    • Keyword (FTS)          │  │   │
│  │  │  • Research      │◄──┼──┼──┤    • RRF Fusion             │  │   │
│  │  │  • Analysis      │   │  │  └─────────────────────────────┘  │   │
│  │  │  • Fact Checker  │   │  │                ↓                  │   │
│  │  │  • Web Search    │   │  │  ┌─────────────────────────────┐  │   │
│  │  │  • Synthesizer   │   │  │  │ 3. Reranking                │  │   │
│  │  │                  │   │  │  │    • Cohere Rerank v3       │  │   │
│  │  └──────────────────┘   │  │  └─────────────────────────────┘  │   │
│  └─────────────────────────┘  │                ↓                  │   │
│                                │  ┌─────────────────────────────┐  │   │
│  ┌─────────────────────────┐  │  │ 4. LLM Generation           │  │   │
│  │  EVALUATION FRAMEWORK   │  │  │    • Context injection      │  │   │
│  │                         │  │  │    • Streaming              │  │   │
│  │  • RAGAS Metrics        │  │  │    • Citation tracking      │  │   │
│  │  • Custom Financial     │  │  └─────────────────────────────┘  │   │
│  │  • LLM-as-Judge         │  └───────────────────────────────────┘   │
│  │  • Regression Testing   │                                          │
│  └─────────────────────────┘                                          │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
┌────────────────────────────────┴───────────────────────────────────────┐
│                   DATABASE (PostgreSQL + pgvector)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ documents    │  │ doc_chunks   │  │ conversations│  │ messages  │ │
│  │              │  │ + embeddings │  │              │  │ + sources │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘ │
│                                                                         │
│  ┌──────────────────────────────┐  ┌────────────────────────────────┐ │
│  │ evaluation_runs              │  │ Indexes:                       │ │
│  │ (Regression test results)    │  │ • IVFFlat (vector_cosine_ops)  │ │
│  │                              │  │ • GIN (full-text search)       │ │
│  └──────────────────────────────┘  │ • GIN (JSONB metadata)         │ │
│                                     └────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

                                 ↕
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                               │
│  OpenAI/Anthropic (LLM)  •  Cohere (Rerank)  •  Tavily (Web Search)   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Complex Query Example

```
User: "Compare Apple and Microsoft's Q4 revenue growth"
  ↓
Supervisor → Analyzes query → Routes to MULTI_AGENT
  ↓
Research Agent → Retrieves Apple docs via RAG
  ↓ (parallel)
Research Agent → Retrieves Microsoft docs via RAG
  ↓
Analysis Agent → Calculates growth rates, comparisons
  ↓
Fact Checker → Validates numerical accuracy
  ↓
Synthesizer → Generates final answer with citations
  ↓
Response: "Apple's Q4 revenue grew 12.3% to $119.6B [1], while Microsoft..."
```

---

## ✨ Key Features

### 🔍 Advanced RAG Pipeline

**Query Transformation**
- **HyDE** (Hypothetical Document Embeddings): Generates hypothetical answers for better semantic matching
- **Multi-Query**: Expands user query into multiple perspectives
- **Decomposition**: Breaks complex questions into sub-queries

**Hybrid Retrieval**
- **Vector Search**: Semantic similarity using `text-embedding-3-small` (1536d)
- **Keyword Search**: PostgreSQL full-text search with tsvector
- **RRF** (Reciprocal Rank Fusion): Intelligent combination of both methods
- **IVFFlat Indexing**: Optimized for fast approximate nearest neighbor search

**Reranking**
- Cohere Rerank v3 for precision boost on top candidates
- Improves relevance by 20-30% compared to retrieval alone

### 🤖 Multi-Agent System (LangGraph)

**Architecture Pattern**: Supervisor + Specialized Agents

**Agent Types**:
1. **Supervisor**: Query analysis and routing
   - Classifies query type (factual, analytical, real-time)
   - Routes to appropriate agent(s)
   - Supports multi-agent workflows

2. **Research Agent**: Document retrieval specialist
   - Integrates with RAG pipeline
   - Optimizes retrieval strategy per query

3. **Analysis Agent**: Quantitative analysis
   - Financial calculations (growth rates, ratios)
   - Comparative analysis
   - Tool-augmented reasoning

4. **Fact Checker**: Verification layer
   - Cross-references claims with sources
   - Validates numerical accuracy
   - Confidence scoring

5. **Web Search Agent**: Real-time data
   - Tavily API integration
   - Filters and ranks results
   - Combines with internal knowledge

6. **Synthesizer**: Final answer generation
   - Combines multi-agent outputs
   - Structured responses with citations
   - Coherent narrative generation

**Benefits**:
- Complex query handling
- Specialized reasoning per task
- Transparent execution trace
- Error isolation and recovery

### 📊 Comprehensive Evaluation Framework

**1. RAGAS Metrics** (Research-standard)
- **Faithfulness**: Answer grounded in retrieved context (target: >0.85)
- **Answer Relevancy**: Response addresses user question (target: >0.90)
- **Context Precision**: Retrieved chunks are relevant (target: >0.80)
- **Context Recall**: All necessary information retrieved

**2. Custom Financial Metrics**
- **Numerical Accuracy**: Exact match for figures (target: >95%)
- **Entity Recognition**: Correct company/financial term identification
- **Temporal Accuracy**: Correct time periods and dates
- **Financial Comprehension**: Domain-specific understanding

**3. LLM-as-Judge**
- GPT-4o-mini evaluates answer quality (1-5 scale)
- Aspects: accuracy, completeness, clarity, citation quality
- Cost-effective at $0.15/$0.60 per 1M tokens

**4. Regression Testing**
- Golden dataset with expected answers
- Automated test suites
- Performance tracking over time
- Regression/improvement detection
- Stored in `evaluation_runs` table

**Evaluation Pipeline**:
```python
result = await eval_pipeline.run_full_evaluation()
# Returns: metrics, pass_rate, regressions, improvements
# Automatically stored in database for tracking
```

### 🔐 Production Engineering

**Security**
- API key authentication with Supabase
- Input validation (Pydantic models)
- Prompt injection detection
- PII detection support
- Rate limiting

**Observability**
- Structured logging (structlog)
- LangSmith tracing integration
- Agent execution traces
- Performance metrics tracking
- Error monitoring

**Performance**
- Streaming responses (SSE)
- Async/await throughout
- Connection pooling (asyncpg)
- Efficient chunking strategies
- Query result caching

**Error Handling**
- LLM fallbacks (OpenAI → Anthropic)
- Retry logic with exponential backoff (tenacity)
- Graceful degradation
- Detailed error messages

### 📄 Document Processing

**Supported Formats**
- PDF
- Excel
- Text

**Processing Pipeline**
1. File upload and validation
2. Text extraction with layout preservation
3. Table detection and structured extraction
4. Intelligent chunking (semantic, sliding window)
5. Embedding generation
6. Vector + full-text indexing

### 🎨 Modern Frontend

**UI Components**
- Real-time streaming chat interface
- Agent trace visualization with timeline
- Source viewer with highlighting
- Document upload with progress
- Metrics dashboard with charts
- Dark/light theme support

**Tech**
- React 18 + TypeScript
- Vite for fast dev/build
- shadcn/ui components
- Tailwind CSS
- Zustand state management
- Recharts for visualizations

---

## 🛠️ Tech Stack

### Backend

| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI 0.128+, Python 3.11+ |
| **Dependency Management** | Poetry 2.2.1 |
| **Database** | PostgreSQL (Supabase 2.11+), pgvector extension |
| **LLM Orchestration** | LangChain 0.3.15+, LangGraph 0.2.62+, LangSmith 0.2.10+ |
| **LLM Providers** | OpenAI 1.59+, Anthropic 0.44+, LiteLLM 1.56+ |
| **Embeddings** | OpenAI `text-embedding-3-small` (1536d) |
| **Reranking** | Cohere 5.13+ (Rerank v3) |
| **Web Search** | Tavily 0.5+ |
| **Evaluation** | RAGAS 0.2.8+, custom metrics, spaCy 3.7+ |
| **Document Processing** | PyMuPDF 1.25+, pdfplumber 0.11+, python-docx 1.1+, pandas 2.2+ |
| **Async** | asyncio, asyncpg 0.30+, httpx 0.28+ |
| **Observability** | structlog 25.1+, LangSmith |
| **Testing** | pytest 8.3+, pytest-asyncio 0.25+, pytest-cov 6.0+ |
| **Code Quality** | ruff 0.9+, black 25.1+, mypy 1.14+ |

### Frontend

| Category | Technologies |
|----------|-------------|
| **Framework** | React 18 |
| **Language** | TypeScript 5.3 |
| **Build Tool** | Vite 5 |
| **UI Library** | shadcn/ui (Radix UI primitives) |
| **Styling** | Tailwind CSS 3 |
| **State Management** | Zustand |
| **Charts** | Recharts |
| **Markdown** | react-markdown |
| **Icons** | lucide-react |

### Infrastructure

| Category | Technologies |
|----------|-------------|
| **Database** | Supabase (managed PostgreSQL) |
| **Backend Hosting** | Modal (serverless) |
| **Frontend Hosting** | Vercel |
| **Package Management** | pnpm (workspace monorepo) |

---

## 🗄️ Database Schema

### Core Tables

**`documents`**
- Stores uploaded financial documents
- Tracks processing status
- JSONB metadata for flexibility

**`document_chunks`**
- Text chunks with embeddings (vector[1536])
- Full-text search vector (tsvector)
- JSONB metadata (page, section, table info)

**`conversations` & `messages`**
- Chat history with role-based messages
- JSONB metadata for agent traces

**`citations`**
- Links messages to source chunks
- Tracks relevance scores

### Evaluation Tables

**`evaluation_runs`**
- Batch evaluation results from regression tests
- JSONB metrics storage
- Regression/improvement tracking
- Time-series performance data

**`prompt_versions`**
- Prompt management and A/B testing
- Version control for prompts

### Indexes (Optimized for Performance)

```sql
-- Vector similarity (IVFFlat)
CREATE INDEX idx_chunks_embedding ON document_chunks 
  USING ivfflat (embedding vector_cosine_ops) 
  WITH (lists = 100);

-- Full-text search
CREATE INDEX idx_chunks_search ON document_chunks 
  USING gin(search_vector);

-- JSONB metadata queries
CREATE INDEX idx_chunks_metadata ON document_chunks 
  USING gin(metadata);
```

**Why these choices?**
- **IVFFlat**: Fast approximate NN search, good for 1536d embeddings
- **GIN**: Optimal for full-text and JSONB queries
- **JSONB**: Flexible schema for evolving metadata needs

---

## 🚀 Getting Started

### Prerequisites

```bash
# Required
- Python 3.11+
- Node.js 18+
- pnpm 8+
- Supabase account

# Install Poetry (Python dependency manager)
curl -sSL https://install.python-poetry.org | python3 -

# Install pnpm (if not already)
npm install -g pnpm
```

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd investment-research-ai
```

### 2. Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run the schema:
   ```bash
   # Copy the SQL from backend/scripts/setup_supabase.sql
   # Execute in Supabase SQL Editor
   ```
3. Note your credentials:
   - Project URL
   - Anon (public) key
   - Service role (private) key

### 3. Environment Configuration

```bash
# Create .env file in backend/
cat > backend/.env << EOF
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJh...
SUPABASE_SERVICE_KEY=eyJh...

# Web Search
TAVILY_API_KEY=tvly-...

# Observability (optional)
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=investment-research-ai
EOF
```

### 4. Backend Setup

```bash
cd backend

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run development server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

**API Docs**: `http://localhost:8000/docs` (Swagger UI)

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Run development server
pnpm dev
```

Frontend will be available at `http://localhost:5173`

### 6. Seed Sample Data (Optional)

```bash
cd backend
poetry run python scripts/seed_data.py
```

This uploads sample financial documents for testing.

### 7. Run Evaluations

```bash
cd backend
poetry run python scripts/run_evals.py
```

Runs the full evaluation suite and stores results in the database.

---

## 🔬 Advanced RAG Pipeline

### Usage Examples

**Basic Query**
```python
from src.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()
result = pipeline.query(
    "What was Tesla's Q4 2023 revenue?"
)
print(result['answer'])
print(f"Sources: {len(result['sources'])}")
```

**Advanced Query with All Features**
```python
result = pipeline.query(
    question="Compare revenue growth rates",
    strategy='hybrid',           # Vector + keyword + RRF
    use_query_transform=True,    # HyDE/multi-query
    use_reranking=True,          # Cohere rerank
    top_k=10
)
```

**Streaming Query**
```python
async for event in pipeline.query_stream(
    "What was Tesla's Q4 2023 revenue?",
    strategy='hybrid',
    use_reranking=True
):
    if event['type'] == 'token':
        print(event['content'], end='', flush=True)
    elif event['type'] == 'sources':
        print(f"\nSources: {len(event['sources'])}")
```

### Retrieval Strategies

| Strategy | Description | Best For | Speed |
|----------|-------------|----------|-------|
| `vector` | Semantic similarity only | Conceptual queries | Fast |
| `keyword` | Full-text search only | Exact term matching | Fastest |
| `hybrid` | Vector + keyword combined | Most queries | Medium |
| `rrf` | Reciprocal Rank Fusion | Best precision | Medium |

### Query Transformation Strategies

- **`hyde`**: Best for vague questions
- **`multi_query`**: Best for comprehensive coverage
- **`decomposition`**: Best for complex multi-part questions
- **`auto`**: Automatic selection based on query

---

## 🤖 Multi-Agent System

### Usage

```python
from src.agents.graph import ResearchAgentGraph
from src.db.supabase import get_supabase_client
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline

# Initialize
supabase = get_supabase_client()
llm = LLMProvider()
rag = RAGPipeline()

graph = ResearchAgentGraph(
    supabase_client=supabase,
    llm_provider=llm,
    rag_pipeline=rag
)

# Run
result = await graph.arun(
    query="Compare Apple and Microsoft's profitability",
    user_id=user_id,
    document_ids=None  # Search all docs
)

print(result['final_answer'])
print(f"Confidence: {result['confidence_score']}")
print(f"Agent trace: {result['agent_trace']}")
```

### Agent Trace Example

```json
[
  {
    "agent": "supervisor",
    "action": "analyzing query",
    "decision": "multi_agent",
    "reasoning": "Requires comparative analysis across multiple companies"
  },
  {
    "agent": "research",
    "action": "searching documents",
    "results": 12,
    "duration": 0.8
  },
  {
    "agent": "analysis",
    "action": "calculating metrics",
    "metrics": ["profit_margin", "ROE"],
    "duration": 0.5
  },
  {
    "agent": "fact_checker",
    "action": "verifying facts",
    "verified": true,
    "confidence": 0.92
  },
  {
    "agent": "synthesizer",
    "action": "generating answer",
    "duration": 1.2
  }
]
```

---

## 📊 Evaluation Framework

### Running Evaluations

**Full Suite**
```bash
cd backend
poetry run python scripts/run_evals.py
```

**Debug Mode** (detailed per-question results)
```bash
poetry run python scripts/debug_evals.py
```

**Via API**
```bash
curl -X POST http://localhost:8000/api/evals/run \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Evaluation Results

Results are stored in `evaluation_runs` table and saved to:
- `backend/data/eval_debug/summary_results_TIMESTAMP.csv`
- `backend/data/eval_debug/detailed_results_TIMESTAMP.json`
- `backend/data/eval_debug/report_TIMESTAMP.md`

### Metrics Thresholds

| Metric | Target | Excellent |
|--------|--------|-----------|
| Faithfulness | >0.85 | >0.90 |
| Answer Relevancy | >0.90 | >0.95 |
| Context Precision | >0.80 | >0.85 |
| Numerical Accuracy | >0.95 | >0.98 |
| LLM Judge (1-5) | >4.0 | >4.5 |

### Custom Evaluation

```python
from src.evaluation.pipeline import EvaluationPipeline

eval_pipeline = EvaluationPipeline(rag_pipeline, supabase, llm)

# Single query evaluation
result = await eval_pipeline.evaluate_single_query(
    question="What was revenue?",
    answer="Revenue was $100M in Q4",
    ground_truth="Q4 revenue was $100 million",
    sources=[...]
)

print(result['ragas'])   # RAGAS metrics
print(result['custom'])  # Custom metrics
print(result['judge'])   # LLM judge scores
```

---

## 📡 API Documentation

### Endpoints

**Chat**
```bash
POST /api/chat
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "message": "What was Tesla's revenue?",
  "conversation_id": "optional-uuid",
  "use_agents": true,
  "stream": false
}
```

**Document Upload**
```bash
POST /api/documents/upload
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY

file=@document.pdf
```

**Evaluations**
```bash
GET /api/evals/history?limit=10
POST /api/evals/run
GET /api/evals/metrics/dashboard
```

**Analysis** (RAG only, no agents)
```bash
POST /api/analyze
{
  "question": "What was revenue?",
  "strategy": "hybrid",
  "use_reranking": true
}
```

### Authentication

Include API key in header:
```bash
Authorization: Bearer YOUR_API_KEY
```

Or query parameter:
```bash
?api_key=YOUR_API_KEY
```

---

## 🚢 Deployment

### Backend (Modal)

```bash
cd backend

# Install Modal CLI
pip install modal

# Setup Modal token
modal token new

# Deploy
modal deploy modal_app.py
```

Your API will be available at: `https://your-workspace--investment-research-api.modal.run`

**Environment Variables**: Set in Modal dashboard or via secrets

### Frontend (Vercel)

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel deploy

# Production
vercel --prod
```

**Environment Variables**:
```bash
VITE_API_URL=https://your-api-url
```

### Cost Estimates

**Development** (~2-4 weeks active development)
- OpenAI embeddings + completions: $10-15
- Cohere reranking: $2-3
- Supabase: Free tier
- **Total: ~$15-20**

**Production** (light usage: 1000 queries/month)
- OpenAI: ~$2-3
- Cohere: ~$0.50
- Supabase: Free tier
- Modal: Free tier (60,000 CPU-seconds/month)
- Vercel: Free tier
- **Total: ~$2-5/month**

**Scales to zero** when idle!

---



---

## 🧪 Testing

### Run All Tests

```bash
cd backend
poetry run pytest
```

### With Coverage

```bash
poetry run pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```

### Specific Test Categories

```bash
# Unit tests
poetry run pytest tests/unit/

# Integration tests
poetry run pytest tests/integration/

# Agent tests
poetry run pytest tests/test_agents.py

# RAG tests
poetry run pytest tests/test_rag_advanced.py
```

### Test RAG Pipeline

```bash
poetry run python test_rag_pipeline.py
```

### Test Agent System

```bash
poetry run python test_agents_integration.py
```

---

## 📚 Documentation

Detailed implementation guides in `docs/`:

- **[plan.md](docs/plan.md)**: Master architecture and plan
- **[agents_implementation_guide.md](docs/agents_implementation_guide.md)**: Multi-agent system deep dive
- **[rag_implementation_guide.md](docs/rag_implementation_guide.md)**: RAG pipeline details
- **[evaluation_implementation_guide.md](docs/evaluation_implementation_guide.md)**: Evaluation framework
- **[deployment_guide.md](docs/deployment_guide.md)**: Production deployment
- **[testing_guide.md](docs/testing_guide.md)**: Testing strategies
- **[frontend_implementation_guide.md](docs/frontend_implementation_guide.md)**: UI/UX details

Additional docs:
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture
- **[AGENT_ROUTING_EXPLAINED.md](AGENT_ROUTING_EXPLAINED.md)**: Agent routing logic
- **[backend/DATABASE_TABLES.md](backend/DATABASE_TABLES.md)**: Database schema
- **[backend/EVALUATION_SYSTEM.md](backend/EVALUATION_SYSTEM.md)**: Evaluation details

---
## 🤝 Contributing

This is a portfolio project demonstrating production AI engineering skills. Feel free to:
- Fork for your own use
- Open issues for bugs
- Suggest improvements

**Not actively seeking contributions**, but feedback is welcome!

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file

