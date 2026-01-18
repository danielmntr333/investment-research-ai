# Investment Research Intelligence Platform - Implementation Plan

## Project Overview

A production-grade AI platform for financial research that demonstrates enterprise-level AI engineering skills. This system combines advanced RAG (Retrieval-Augmented Generation), multi-agent orchestration, and comprehensive evaluation to create an intelligent financial document analysis tool.


**Core Value Proposition**: Upload financial documents (10-Ks, earnings reports, research PDFs) and get intelligent, well-cited answers with source attribution, comparative analysis, and real-time data enrichment.

---

## 📚 Documentation Structure

This is the **master plan document** that provides the high-level architecture and roadmap. For detailed implementation specifications, refer to these companion documents:

- **agents-implementation.md**: Complete multi-agent system implementation with LangGraph
- **rag-implementation.md**: Advanced RAG pipeline with hybrid retrieval and query transformation
- **evaluation-implementation.md**: Comprehensive evaluation framework with RAGAS and custom metrics
- **frontend-implementation.md**: Complete React application with all UI components
- **deployment-guide.md**: Step-by-step production deployment to Modal and Vercel
- **testing-guide.md**: Comprehensive testing strategies for all components

**Usage**: Reference this plan.md for overall structure, then dive into specific implementation docs for detailed code and patterns.

---

## Tech Stack (Locked & Loaded)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Package Manager**: pnpm 8+
- **UI Library**: shadcn/ui + Radix UI + Tailwind CSS
- **State Management**: Zustand
- **Charts/Viz**: Recharts + react-markdown
- **Hosting**: Vercel (free tier, auto-deploy)

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11
- **Hosting**: Modal (serverless, pay-per-use)
- **Async**: httpx, asyncio

### Database & Storage
- **Primary Database**: Supabase (PostgreSQL 15)
- **Vector Search**: pgvector extension (in Supabase)
- **File Storage**: Supabase Storage (1GB free)

### LLM Stack
- **Providers**: OpenAI (primary), Anthropic (fallback)
- **Orchestration**: LangGraph 0.0.50+
- **Framework**: LangChain 0.1+ (selective imports only)
- **Embeddings**: OpenAI text-embedding-3-large
- **Reranking**: Cohere rerank-english-v3.0
- **Interface**: LiteLLM (multi-provider support)

### Evaluation
- **Framework**: RAGAS 0.1+
- **LLM Judge**: GPT-4 for quality scoring
- **Metrics Storage**: Supabase
- **Testing**: pytest + custom eval suite

### Observability
- **LLM Tracing**: LangSmith (5K traces/month free)
- **Logging**: structlog
- **Monitoring**: Modal built-in + Supabase dashboard

### Development Tools
- **AI Assist**: Cursor + Claude Code
- **Linting**: ruff
- **Type Checking**: mypy
- **Testing**: pytest + pytest-asyncio
- **Formatting**: black

---

## Project Structure

```
investment-research-ai/
├── frontend/                      # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui components
│   │   │   ├── ChatInterface.tsx  # Main chat UI with streaming
│   │   │   ├── DocumentUpload.tsx # Drag-drop file upload
│   │   │   ├── SourceViewer.tsx   # Citation viewer with highlighting
│   │   │   ├── AgentTrace.tsx     # Visual agent execution flow
│   │   │   ├── MetricsDashboard.tsx # Evaluation metrics display
│   │   │   └── ComparisonView.tsx  # Multi-document analysis view
│   │   ├── lib/
│   │   │   ├── api.ts            # API client with fetch/websocket
│   │   │   ├── types.ts          # TypeScript interfaces
│   │   │   └── utils.ts          # Helper functions
│   │   ├── store/
│   │   │   └── useStore.ts       # Zustand global state
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── backend/                       # FastAPI Python application
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── documents.py  # Upload, list, delete endpoints
│   │   │   │   ├── chat.py       # Chat endpoints with streaming
│   │   │   │   ├── analyze.py    # Multi-doc analysis endpoints
│   │   │   │   └── evals.py      # Evaluation endpoints
│   │   │   ├── middleware.py     # Auth, CORS, logging
│   │   │   └── main.py           # FastAPI app initialization
│   │   │
│   │   ├── agents/
│   │   │   ├── graph.py          # LangGraph orchestrator
│   │   │   ├── nodes.py          # Agent node implementations
│   │   │   ├── tools.py          # Tool implementations (calculator, etc)
│   │   │   └── prompts.py        # System prompts (versioned)
│   │   │
│   │   ├── rag/
│   │   │   ├── pipeline.py       # Main RAG orchestration
│   │   │   ├── embeddings.py     # Embedding service with caching
│   │   │   ├── retrieval.py      # Hybrid retrieval (vector + keyword)
│   │   │   ├── reranking.py      # Cohere reranker integration
│   │   │   ├── chunking.py       # Smart document chunking
│   │   │   └── query_transform.py # HyDE, multi-query, decomposition
│   │   │
│   │   ├── document_processing/
│   │   │   ├── parser.py         # PDF, Excel, HTML parsing
│   │   │   ├── extractor.py      # Metadata extraction (NER)
│   │   │   ├── table_handler.py  # Table extraction/preservation
│   │   │   └── storage.py        # Supabase storage operations
│   │   │
│   │   ├── llm/
│   │   │   ├── provider.py       # LiteLLM wrapper with fallbacks
│   │   │   ├── streaming.py      # SSE streaming implementation
│   │   │   ├── structured.py     # Structured outputs (Pydantic)
│   │   │   └── fallback.py       # Fallback logic for provider failures
│   │   │
│   │   ├── evaluation/
│   │   │   ├── ragas_eval.py     # RAGAS metrics integration
│   │   │   ├── custom_metrics.py # Financial-specific metrics
│   │   │   ├── llm_judge.py      # GPT-4 as judge implementation
│   │   │   ├── golden_set.py     # Test dataset management
│   │   │   └── regression.py     # Regression testing suite
│   │   │
│   │   ├── security/
│   │   │   ├── auth.py           # API key validation
│   │   │   ├── input_validation.py # Prompt injection defense
│   │   │   └── pii_detection.py  # PII redaction (optional)
│   │   │
│   │   ├── db/
│   │   │   ├── supabase.py       # Supabase client singleton
│   │   │   ├── models.py         # Pydantic models for DB
│   │   │   ├── vector_store.py   # pgvector operations
│   │   │   └── migrations/       # SQL migrations
│   │   │
│   │   └── utils/
│   │       ├── logging.py        # Structured logging setup
│   │       ├── tracing.py        # LangSmith integration
│   │       └── config.py         # Settings (pydantic-settings)
│   │
│   ├── tests/
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── evals/                # Evaluation tests
│   │
│   ├── modal_app.py              # Modal deployment configuration
│   ├── pyproject.toml            # Poetry dependencies & config
│   ├── poetry.lock               # Dependency lock file
│   └── POETRY_GUIDE.md           # Poetry setup & usage guide
│
├── data/
│   ├── golden_dataset/           # Evaluation test cases
│   │   ├── questions.json        # Test questions with metadata
│   │   └── expected_answers.json # Ground truth answers
│   └── sample_docs/              # Demo documents for testing
│       ├── apple_10k_2023.pdf
│       └── msft_10k_2023.pdf
│
├── scripts/
│   ├── setup_supabase.sql        # Database schema + pgvector setup
│   ├── seed_data.py              # Load sample data for testing
│   └── run_evals.py              # Run full evaluation suite
│
├── .env.example                  # Environment variables template
├── .gitignore
├── README.md                     # Project documentation
└── ARCHITECTURE.md               # Detailed architecture docs
```

---

## Database Schema (Supabase + pgvector)

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table (simple auth with API keys)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    usage_quota INTEGER DEFAULT 1000,
    usage_count INTEGER DEFAULT 0
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT
);

-- Document chunks table (with embeddings)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(3072),  -- text-embedding-3-large dimension
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    search_vector tsvector,  -- For full-text search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for fast retrieval
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);
CREATE INDEX idx_chunks_search ON document_chunks USING gin(search_vector);
CREATE INDEX idx_chunks_metadata ON document_chunks USING gin(metadata);

-- Trigger to auto-update search_vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,  -- tokens, cost, model used, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Citations table (tracks which chunks were used)
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Evaluations table
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    metrics JSONB NOT NULL,  -- RAGAS scores, custom metrics
    eval_type TEXT NOT NULL,  -- 'ragas', 'llm_judge', 'custom'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prompt versions table (track prompt changes)
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    template TEXT NOT NULL,
    version INTEGER NOT NULL,
    active BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, version)
);
```

---

## Core Components Implementation Details

### 1. Advanced RAG Pipeline

#### A. Smart Document Chunking

**Location**: `backend/src/rag/chunking.py`

**Goal**: Intelligent chunking that preserves document structure and context.

**Key Features**:
- Detect document structure (headers, sections, tables)
- Semantic chunking (group related content)
- Structure-aware splitting (respect boundaries)
- Context injection (include parent headers in chunks)
- Table preservation (keep tables intact)
- Adaptive chunk sizing based on content type

**Algorithm**:
1. Parse document and detect structure
2. Identify sections, headers, tables, lists
3. For each section:
   - Extract tables separately (preserve structure)
   - Chunk text with overlap (1000 chars, 200 overlap)
   - Add section header to each chunk for context
4. Store chunks with positional metadata

**Implementation Notes**:
- Use `RecursiveCharacterTextSplitter` from LangChain as base
- Custom logic for financial documents
- Preserve numerical data accuracy
- Handle multi-column layouts

---

#### B. Hybrid Retrieval with Reciprocal Rank Fusion

**Location**: `backend/src/rag/retrieval.py`

**Goal**: Combine vector search (semantic) + keyword search (lexical) for better recall.

**Key Features**:
- Vector search using pgvector (cosine similarity)
- Keyword search using PostgreSQL full-text search (tsvector)
- Reciprocal Rank Fusion to combine results
- Cohere reranker for final precision boost
- Metadata filtering (date ranges, document types)

**Algorithm**:
1. **Parallel Retrieval**: Run vector + keyword search simultaneously
2. **Reciprocal Rank Fusion (RRF)**:
   - Formula: `score(doc) = Σ 1/(k + rank(doc))` where k=60
   - Combines rankings from both retrievers
   - Documents appearing in both get higher scores
3. **Reranking**: Use Cohere to rerank top 20 → top 10
4. **Return**: Top K most relevant chunks with scores

**SQL Queries**:
```sql
-- Vector search
SELECT id, content, metadata, 
       1 - (embedding <=> $1::vector) as similarity
FROM document_chunks
WHERE metadata @> $2::jsonb  -- Filter by metadata
ORDER BY embedding <=> $1::vector
LIMIT 20;

-- Keyword search
SELECT id, content, metadata,
       ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
FROM document_chunks
WHERE search_vector @@ plainto_tsquery('english', $1)
  AND metadata @> $2::jsonb
ORDER BY rank DESC
LIMIT 20;
```

---

#### C. Query Transformation

**Location**: `backend/src/rag/query_transform.py`

**Goal**: Transform user queries for better retrieval performance.

**Strategies**:

1. **HyDE (Hypothetical Document Embeddings)**:
   - Generate a hypothetical answer to the question
   - Embed the hypothetical answer
   - Retrieve documents similar to hypothetical answer
   - Works well for conceptual questions
   - Example: "What is revenue recognition?" → Generate paragraph about revenue recognition → Embed → Find similar docs

2. **Multi-Query Generation**:
   - Generate 3-5 variations of the same question
   - Use different phrasings, synonyms
   - Retrieve for each variation
   - Combine results
   - Better recall for ambiguous queries

3. **Query Decomposition**:
   - Break complex questions into sub-questions
   - Answer each sub-question independently
   - Synthesize final answer
   - Example: "Compare X and Y" → "What is X?" + "What is Y?" + "How do they differ?"

**When to Use Each**:
- Simple factual: No transformation
- Conceptual: HyDE
- Ambiguous: Multi-query
- Complex/multi-part: Decomposition

---

### 2. Multi-Agent System with LangGraph

**Location**: `backend/src/agents/graph.py`

**Goal**: Orchestrate multiple specialized agents to handle complex queries.

**Architecture**:
```
User Query → Supervisor → Route to Agent(s) → Execute → Synthesize → Response
```

**Agents**:

1. **Supervisor Agent**:
   - Analyzes query intent and complexity
   - Routes to appropriate agent(s)
   - Manages conversation flow
   - Synthesizes multi-agent outputs

2. **Research Agent**:
   - RAG-based Q&A over documents
   - Retrieves relevant chunks
   - Generates answers with citations
   - Primary agent for factual questions

3. **Analysis Agent**:
   - Comparative analysis (Company A vs B)
   - Quantitative calculations
   - Has access to tools:
     - Calculator (for math)
     - Table extractor
     - Chart generator
   - Used for "compare", "calculate", "analyze" queries

4. **Fact-Checker Agent**:
   - Validates claims against sources
   - Extracts claims from answers
   - Verifies each claim
   - Flags unsupported statements
   - Runs after other agents

5. **Web Search Agent**:
   - Fetches real-time external data
   - Uses Tavily or Serper API
   - Enriches internal knowledge
   - Used when current info needed

**LangGraph Flow**:
```python
# Simplified flow
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("research", research_node)
workflow.add_node("analysis", analysis_node)
workflow.add_node("fact_checker", fact_checker_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("synthesizer", synthesizer_node)

# Routing
workflow.set_entry_point("supervisor")
workflow.add_conditional_edges("supervisor", route_query)
workflow.add_edge("research", "fact_checker")
workflow.add_edge("fact_checker", "synthesizer")
workflow.add_edge("synthesizer", END)
```

**State Management**:
```python
class AgentState(TypedDict):
    query: str
    chat_history: List[Dict]
    retrieved_docs: List[Dict]
    analysis_results: Dict
    web_search_results: List[Dict]
    final_answer: str
    citations: List[Dict]
    agent_trace: List[Dict]  # For UI visualization
    errors: List[str]
```

**Tools Available**:
- RAG query tool
- Web search
- Calculator (Python eval in sandbox)
- Table extractor (from documents)
- Chart generator (matplotlib → base64)
- Financial metrics calculator

---

### 3. Evaluation Framework

**Location**: `backend/src/evaluation/`

**Goal**: Prove system quality with measurable metrics.

**Components**:

#### A. RAGAS Metrics

**File**: `ragas_eval.py`

**Metrics**:
1. **Faithfulness**: Does answer align with retrieved context? (no hallucination)
2. **Answer Relevancy**: Does answer address the question?
3. **Context Precision**: Are top-ranked chunks relevant?
4. **Context Recall**: Did we retrieve all necessary context?
5. **Answer Correctness**: Semantic + factual correctness

**Usage**:
```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, ...]
)
```

#### B. Custom Financial Metrics

**File**: `custom_metrics.py`

**Metrics**:
1. **Numerical Accuracy**:
   - Extract numbers from answer and ground truth
   - Compare with tolerance (±0.01 for percentages)
   - Score: % of numbers that match

2. **Citation Quality**:
   - % of answers with citations
   - Average citations per answer
   - Citation diversity (using different sources)

3. **Temporal Accuracy**:
   - Correct date/period references
   - No anachronisms
   - Proper tense usage

4. **Entity Accuracy**:
   - Correct company names, people, locations
   - Use NER to extract entities
   - Compare against ground truth

#### C. LLM-as-Judge

**File**: `llm_judge.py`

**Goal**: Use GPT-4 to evaluate answer quality.

**Prompt Template**:
```
Evaluate this answer on a scale of 1-5:

Question: {question}
Generated Answer: {answer}
Reference Answer: {ground_truth}

Rate on:
1. Correctness (1-5)
2. Completeness (1-5)
3. Clarity (1-5)
4. Citation quality (1-5)

Return JSON with scores and reasoning.
```

#### D. Golden Dataset

**File**: `data/golden_dataset/questions.json`

**Structure**:
```json
{
  "id": "unique_id",
  "question": "The test question",
  "documents_needed": ["doc1.pdf", "doc2.pdf"],
  "expected_answer": "Ground truth answer",
  "difficulty": "easy|medium|hard",
  "required_capabilities": ["multi_doc", "calculation", "comparison"],
  "ground_truth_numbers": {
    "key1": 123.45,
    "key2": 67.89
  }
}
```

**Size**: 50-100 test cases covering:
- Simple factual lookup (easy)
- Multi-document comparison (medium)
- Multi-hop reasoning (hard)
- Calculations and analysis (medium-hard)
- Temporal queries (medium)
- Edge cases (missing data, contradictions)

#### E. Regression Testing

**File**: `regression.py`

**Goal**: Detect quality degradation on changes.

**Process**:
1. Run golden dataset through system
2. Calculate all metrics
3. Compare to baseline
4. Flag regressions (>5% drop in key metrics)
5. Store results in DB for tracking

**Automated**:
- Run on every deploy (Modal scheduled function)
- Alert if metrics drop
- Track metrics over time

---

### 4. LLM Provider Abstraction

**Location**: `backend/src/llm/provider.py`

**Goal**: Unified interface for multiple LLM providers with fallbacks.

**Features**:
- Multi-provider support (OpenAI, Anthropic, Azure OpenAI)
- Automatic fallback on failure
- Token tracking and cost calculation
- Streaming support
- Structured outputs (Pydantic models)
- Prompt versioning

**Implementation**:
```python
from litellm import completion, acompletion

class LLMProvider:
    def __init__(self):
        self.primary_model = "gpt-4o"
        self.fallback_model = "claude-3-5-sonnet-20241022"
    
    async def generate(
        self, 
        prompt: str, 
        model: str = None,
        stream: bool = False,
        format: str = None  # 'json' for structured output
    ):
        model = model or self.primary_model
        
        try:
            response = await acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
                response_format={"type": format} if format else None
            )
            
            # Track usage
            self._track_usage(response)
            
            return response
            
        except Exception as e:
            # Fallback to secondary model
            if model == self.primary_model:
                return await self.generate(
                    prompt, 
                    model=self.fallback_model,
                    stream=stream,
                    format=format
                )
            raise
```

---

### 5. Security Implementation

**Location**: `backend/src/security/`

#### A. Authentication

**File**: `auth.py`

**Simple API Key Auth**:
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    # Check against database
    user = await db.get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check rate limits
    if user.usage_count >= user.usage_quota:
        raise HTTPException(status_code=429, detail="Quota exceeded")
    
    return user
```

#### B. Input Validation & Prompt Injection Defense

**File**: `input_validation.py`

**Techniques**:
1. **Input Sanitization**:
   - Max length enforcement (10K chars)
   - Character whitelist
   - Remove suspicious patterns

2. **Prompt Structure**:
   - Use XML tags to separate system/user content
   - Clear delimiters
   - Explicit instruction hierarchy

3. **Detection**:
   - Pattern matching for common injections
   - LLM-based classifier (optional)

**Example**:
```python
def validate_input(user_input: str) -> str:
    # Check length
    if len(user_input) > 10000:
        raise ValueError("Input too long")
    
    # Check for injection patterns
    injection_patterns = [
        r"ignore previous instructions",
        r"system prompt",
        r"you are now",
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            raise ValueError("Suspicious input detected")
    
    return user_input
```

---

## API Endpoints

**Base URL**: `https://your-modal-url.modal.run` (or custom domain)

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List user's documents
- `GET /api/documents/{doc_id}` - Get document metadata
- `DELETE /api/documents/{doc_id}` - Delete document

### Chat
- `POST /api/chat` - Send message (non-streaming)
- `POST /api/chat/stream` - Send message (SSE streaming)
- `GET /api/conversations` - List conversations
- `GET /api/conversations/{conv_id}` - Get conversation history

### Analysis
- `POST /api/analyze/compare` - Multi-document comparison
- `POST /api/analyze/summarize` - Document summarization

### Evaluation
- `GET /api/evals/metrics` - Get evaluation metrics
- `POST /api/evals/run` - Run evaluation on test set
- `GET /api/evals/history` - Get evaluation history

### Health
- `GET /health` - Health check
- `GET /api/stats` - System statistics

---

## Implementation Phases

### PHASE 1: Foundation (Days 1-7)
**Goal: Basic end-to-end working**

**Tasks**:
1. ✅ Setup Supabase
   - Create account at supabase.com
   - Create new project
   - Run `scripts/setup_supabase.sql`
   - Enable pgvector extension
   - Get credentials (URL, anon key, service role key)

2. ✅ Backend skeleton
   - Initialize FastAPI project
   - Setup project structure
   - Install dependencies with Poetry (`pyproject.toml`)
   - Configure Supabase client
   - Setup LiteLLM with OpenAI
   - Create basic health endpoint

3. ✅ Frontend skeleton
   - Initialize React + TypeScript + Vite
   - Install shadcn/ui components
   - Setup Zustand store
   - Create basic layout
   - Setup API client

4. ✅ Simple RAG pipeline
   - PDF parsing (PyMuPDF)
   - Basic chunking (RecursiveCharacterTextSplitter, 1000 chars)
   - Generate embeddings (text-embedding-3-large)
   - Store in pgvector
   - Simple vector search
   - Generate answer with OpenAI

5. ✅ Document upload flow
   - Upload UI component
   - Upload API endpoint
   - Store file in Supabase Storage
   - Process document (parse → chunk → embed)
   - Show processing status

6. ✅ Chat interface
   - Chat UI component
   - Send message API
   - Display answer with loading state
   - Show sources (basic list)

7. ✅ Deploy
   - Modal: `modal deploy modal_app.py`
   - Vercel: Connect GitHub repo, deploy

**Deliverable**: Working demo - upload PDF, ask question, get answer with sources

---

### PHASE 2: Advanced RAG (Days 8-14)
**Goal: Production-quality retrieval**

**Tasks**:
1. ✅ Implement smart chunking
   - Create `FinancialDocumentChunker` class
   - Add structure detection
   - Preserve tables
   - Context injection (headers in chunks)
   - Test with financial documents

2. ✅ Implement hybrid retrieval
   - Add full-text search (tsvector)
   - Implement RRF algorithm
   - Test both retrievers separately
   - Compare fused results

3. ✅ Add reranking
   - Integrate Cohere rerank API
   - Rerank top 20 → top 10
   - Measure improvement in relevance

4. ✅ Query transformation
   - Implement HyDE
   - Implement multi-query
   - Add strategy selection logic
   - Test on different query types

5. ✅ Citation system
   - Extract citations from LLM response
   - Link citations to chunks
   - Store in citations table
   - UI: Show sources with highlighting

6. ✅ Source viewer
   - Create SourceViewer component
   - Show original document excerpt
   - Highlight relevant passage
   - Display metadata (page, section)

**Deliverable**: Noticeably better retrieval with proper citations

---

### PHASE 3: Multi-Agent System (Days 15-21)
**Goal: Impressive agent orchestration**

**Tasks**:
1. ✅ Setup LangGraph
   - Install langgraph
   - Create basic graph structure
   - Define AgentState
   - Test simple flow

2. ✅ Implement supervisor
   - Query analysis logic
   - Routing decisions
   - Store in agent_trace

3. ✅ Implement agents
   - Research agent (RAG-based)
   - Analysis agent (with tools)
   - Fact-checker
   - Web search agent (Tavily)
   - Synthesizer

4. ✅ Implement tools
   - Calculator (safe eval)
   - Table extractor
   - Chart generator (matplotlib)
   - Web search

5. ✅ Agent trace visualization
   - Capture execution steps
   - Create AgentTrace component
   - Show flowchart or timeline
   - Display tool calls and results

6. ✅ Streaming responses
   - Implement SSE endpoint
   - Stream agent thinking
   - Update UI in real-time
   - Show "Agent X is working..."

**Deliverable**: Multi-agent system with visual trace

---

### PHASE 4: Evaluation & Polish (Days 22-28)
**Goal: Prove quality, polish UI**

**Tasks**:
1. ✅ Create golden dataset
   - Write 50-100 test questions (JSON)
   - Include expected answers
   - Cover all difficulty levels
   - Add ground truth numbers for validation
   - Store in `data/golden_dataset/`

2. ✅ Integrate RAGAS
   - Install RAGAS library
   - Implement evaluation pipeline
   - Run on golden dataset
   - Store results in DB
   - Calculate baseline metrics

3. ✅ Custom financial metrics
   - Implement numerical accuracy checker
   - Implement citation quality metrics
   - Implement temporal accuracy
   - Implement entity accuracy
   - Add to evaluation pipeline

4. ✅ LLM-as-judge
   - Create judge prompt template
   - Implement GPT-4 evaluation
   - Store judgments in DB
   - Add to evaluation dashboard

5. ✅ Regression testing
   - Create automated test runner
   - Setup Modal scheduled function (daily)
   - Alert on metric degradation
   - Track metrics over time

6. ✅ Metrics dashboard
   - Create MetricsDashboard component
   - Display RAGAS scores
   - Display custom metrics
   - Show trends over time
   - Beautiful charts with Recharts

7. ✅ UI polish
   - Responsive design (mobile-friendly)
   - Dark mode toggle
   - Loading states (skeletons)
   - Error handling (toasts)
   - Empty states
   - Smooth animations
   - Accessibility (ARIA labels)

8. ✅ Documentation
   - Complete README.md
   - Architecture diagram
   - Setup instructions
   - API documentation
   - Demo video (Loom)
   - Screenshots

**Deliverable**: Production-ready system with proven quality metrics

---

## Key Implementation Details

### 1. Document Processing Pipeline

**Flow**: Upload → Parse → Extract Metadata → Chunk → Embed → Store

**Code Structure** (`backend/src/document_processing/`):

```python
# parser.py
class DocumentParser:
    """Parse different file types."""
    
    def parse(self, file_path: str, file_type: str) -> ParsedDocument:
        if file_type == 'pdf':
            return self._parse_pdf(file_path)
        elif file_type == 'xlsx':
            return self._parse_excel(file_path)
        elif file_type == 'html':
            return self._parse_html(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _parse_pdf(self, path: str) -> ParsedDocument:
        """Parse PDF with PyMuPDF."""
        import fitz
        doc = fitz.open(path)
        
        pages = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            tables = self._extract_tables(page)
            
            pages.append({
                'page_num': page_num,
                'text': text,
                'tables': tables
            })
        
        return ParsedDocument(pages=pages)

# extractor.py
class MetadataExtractor:
    """Extract metadata from documents."""
    
    async def extract(self, text: str) -> Dict:
        """Extract entities, dates, companies, etc."""
        
        # Use NER for entity extraction
        entities = await self._extract_entities(text)
        
        # Extract dates
        dates = self._extract_dates(text)
        
        # Identify document type
        doc_type = self._classify_document(text)
        
        return {
            'entities': entities,
            'dates': dates,
            'document_type': doc_type,
            'companies': [e for e in entities if e['type'] == 'ORG'],
            'people': [e for e in entities if e['type'] == 'PERSON']
        }
```

---

### 2. Embedding Service with Caching

**Location**: `backend/src/rag/embeddings.py`

**Goal**: Generate embeddings efficiently with caching to reduce API costs.

```python
class EmbeddingService:
    """Generate and cache embeddings."""
    
    def __init__(self):
        self.model = "text-embedding-3-large"
        self.dimension = 3072
        self.cache = {}  # In-memory cache
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts with caching."""
        
        # Check cache
        uncached_texts = []
        cached_embeddings = {}
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                cached_embeddings[i] = self.cache[cache_key]
            else:
                uncached_texts.append((i, text))
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            indices, texts_to_embed = zip(*uncached_texts)
            
            # Call OpenAI API (batch)
            response = await openai.Embeddings.acreate(
                model=self.model,
                input=texts_to_embed
            )
            
            # Cache and store
            for idx, embedding_obj in zip(indices, response.data):
                embedding = embedding_obj.embedding
                cache_key = self._get_cache_key(texts[idx])
                self.cache[cache_key] = embedding
                cached_embeddings[idx] = embedding
        
        # Return in original order
        return [cached_embeddings[i] for i in range(len(texts))]
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
```

---

### 3. Streaming Response Implementation

**Location**: `backend/src/llm/streaming.py`

**Goal**: Stream LLM responses to frontend for better UX.

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

class StreamingLLM:
    """Handle streaming LLM responses."""
    
    async def stream_response(
        self, 
        prompt: str, 
        model: str = "gpt-4o"
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response as SSE."""
        
        response = await acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                # Format as SSE
                yield f"data: {json.dumps({'content': content})}\n\n"
        
        # Send done signal
        yield f"data: {json.dumps({'done': True})}\n\n"

# FastAPI endpoint
@app.post("/api/chat/stream")
async def chat_stream(query: str):
    """Streaming chat endpoint."""
    
    async def generate():
        async for chunk in streaming_llm.stream_response(query):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

**Frontend (React)**:
```typescript
// Handle SSE in React
const streamChat = async (message: string) => {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    body: JSON.stringify({ query: message }),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.content) {
          setResponse((prev) => prev + data.content);
        }
      }
    }
  }
};
```

---

### 4. Modal Deployment Configuration (Complete)

**Location**: `backend/modal_app.py`

```python
import modal
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Create Modal stub
stub = modal.Stub("investment-research-ai")

# Define Docker image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "supabase==2.0.3",
        "openai==1.3.5",
        "anthropic==0.7.1",
        "langchain==0.1.0",
        "langgraph==0.0.50",
        "langsmith==0.0.70",
        "litellm==1.11.1",
        "cohere==4.37",
        "ragas==0.1.0",
        "pymupdf==1.23.8",
        "pandas==2.1.3",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "structlog==23.2.0",
        "httpx==0.25.2",
    )
)

# Define secrets (set in Modal dashboard)
secrets = [
    modal.Secret.from_name("openai-secret"),
    modal.Secret.from_name("anthropic-secret"),
    modal.Secret.from_name("supabase-secret"),
    modal.Secret.from_name("cohere-secret"),
    modal.Secret.from_name("langsmith-secret"),
]

# Create FastAPI app
def create_app() -> FastAPI:
    from src.api.main import app
    return app

# Deploy ASGI app
@stub.function(
    image=image,
    secrets=secrets,
    cpu=2.0,
    memory=4096,  # 4GB
    timeout=300,  # 5 minutes
    keep_warm=1,  # Keep 1 container warm
    allow_concurrent_inputs=10,
    container_idle_timeout=300,
)
@modal.asgi_app()
def fastapi_app():
    return create_app()

# Background job: Daily evaluations
@stub.function(
    image=image,
    secrets=secrets,
    schedule=modal.Period(days=1),
)
def run_daily_evaluations():
    """Run evaluation suite daily."""
    import asyncio
    from src.evaluation.regression import run_regression_suite
    
    results = asyncio.run(run_regression_suite())
    print(f"Daily eval results: {results}")
    
    # Alert if performance drops
    if results['overall_score'] < 0.85:
        print(f"⚠️ WARNING: Performance dropped to {results['overall_score']}")

# CLI commands
@stub.local_entrypoint()
def main():
    """Local entrypoint for testing."""
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Deploy Commands**:
```bash
# Deploy to Modal
modal deploy modal_app.py

# Run locally
modal run modal_app.py

# View logs
modal app logs investment-research-ai

# Check status
modal app list
```

---

### 5. Environment Variables

**File**: `.env.example`

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Cohere
COHERE_API_KEY=...

# LangSmith
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=investment-research-ai

# Tavily (Web Search)
TAVILY_API_KEY=...

# App Config
ENVIRONMENT=development
LOG_LEVEL=INFO
API_RATE_LIMIT=100
```

---

### 6. Poetry Dependencies (pyproject.toml)

**File**: `backend/pyproject.toml`

This project uses **Poetry** for dependency management with TOML configuration. See `backend/POETRY_GUIDE.md` for complete setup instructions.

**Quick Start**:
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
cd backend
poetry install

# Run commands
poetry run uvicorn src.api.main:app --reload
poetry run pytest
```

**Dependencies** are organized into groups:
- **Main**: Production dependencies (fastapi, langchain, openai, etc.)
- **Dev**: Development tools (black, ruff, mypy)
- **Test**: Testing frameworks (pytest, pytest-asyncio, pytest-cov)

All dependencies with versions are defined in `pyproject.toml` and locked in `poetry.lock`

---

### 7. Frontend Package.json

**File**: `frontend/package.json`

```json
{
  "name": "investment-research-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.7",
    "react-markdown": "^9.0.1",
    "recharts": "^2.10.3",
    "lucide-react": "^0.294.0",
    "date-fns": "^2.30.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.13.2",
    "@typescript-eslint/parser": "^6.13.2",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "postcss": "^8.4.32",
    "prettier": "^3.1.0",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.3",
    "vite": "^5.0.7"
  }
}
```

---

## Cost Breakdown (Detailed)

### Development Costs (4 weeks)

**LLM API Costs**:
```
Embedding Generation:
- 1000 documents × 1000 tokens avg = 1M tokens
- text-embedding-3-large: $0.13 / 1M tokens
- Cost: $0.13

Development Queries (100 queries):
- Input: 100 × 2K tokens = 200K tokens
- Output: 100 × 1K tokens = 100K tokens
- GPT-4o: $2.50/1M input, $10/1M output
- Cost: $0.50 + $1.00 = $1.50

Testing & Evaluation:
- RAGAS eval on 50 test cases
- ~50 queries × 3K tokens avg = 150K tokens
- Cost: ~$2.00

Reranking (Cohere):
- 100 queries × 20 docs = 2000 rerank calls
- $2.00 / 1000 calls
- Cost: $4.00

TOTAL LLM: ~$8.00
```

**Infrastructure Costs**:
```
Supabase: $0 (free tier - 500MB DB, 1GB storage)
Modal: $5-10 (only when running)
Vercel: $0 (free tier)
LangSmith: $0 (free tier - 5K traces)

TOTAL INFRA: $5-10
```

**TOTAL DEVELOPMENT: $13-18**

### Monthly Running Costs (After Launch)

**Light Usage (5 demos/month)**:
```
LLM API:
- 50 queries × $0.05 per query = $2.50

Infrastructure:
- Modal: $0 (scales to zero when idle)
- Supabase: $0 (within free tier)
- Vercel: $0

TOTAL: $2.50/month
```

**Moderate Usage (100 queries/month)**:
```
LLM API: ~$5.00
Infrastructure: $0
TOTAL: $5.00/month
```

**When Completely Idle**: $0.00/month

---

## Success Metrics (What Makes This Impressive)

### Technical Metrics to Showcase

1. **RAG Quality**:
   - Faithfulness: >0.85
   - Answer Relevancy: >0.90
   - Context Precision: >0.80
   - Numerical Accuracy: >95%
   - Citation Rate: 100%

2. **Performance**:
   - P50 Latency: <3 seconds
   - P95 Latency: <7 seconds
   - Embedding Cache Hit Rate: >60%
   - Successful Retrieval Rate: >95%

3. **System Reliability**:
   - API Uptime: 99%+
   - Error Rate: <1%
   - Fallback Success Rate: 100%

4. **Code Quality**:
   - Test Coverage: >80%
   - Type Coverage: 100%
   - Zero security vulnerabilities
   - Clean architecture

### Demo Scenarios to Prepare

**Scenario 1: Simple Q&A**
```
Upload: Tesla Q3 2024 Earnings Report
Query: "What was Tesla's revenue in Q3 2024?"
Expected: Quick answer with exact number and source citation
Show: Fast retrieval, accurate extraction, proper citation
```

**Scenario 2: Comparative Analysis**
```
Upload: Apple 10-K 2023, Microsoft 10-K 2023
Query: "Compare R&D spending as % of revenue between Apple and Microsoft"
Expected: Agent uses calculator, generates comparison table
Show: Multi-agent orchestration, tool usage, structured output
```

**Scenario 3: Multi-hop Reasoning**
```
Upload: Amazon 10-K 2023
Query: "How profitable is AWS compared to Amazon's overall business?"
Expected: Multi-step reasoning with calculations
Show: Complex reasoning, fact-checking, synthesis
```

**Scenario 4: Real-time Enrichment**
```
Upload: NVIDIA Q3 report
Query: "How is NVIDIA stock performing today relative to their earnings?"
Expected: Web search for current price, RAG for earnings, synthesis
Show: Web search integration, multi-source synthesis
```

**Scenario 5: Evaluation Dashboard**
```
Show: Live metrics dashboard
- RAGAS scores
- Custom metrics
- Query latency
- Cost per query
- Regression test results
Show: Commitment to quality and measurement
```

---

## Interview Talking Points

### When Discussing This Project

**Architecture Decisions**:
- "I chose Modal for serverless deployment because it scales to zero when idle, reducing costs while maintaining production-grade infrastructure"
- "pgvector in Supabase gives me vector search without managing a separate service, simplifying the stack while maintaining performance"
- "LangGraph provides better control than LangChain agents for complex multi-agent scenarios"

**RAG Pipeline**:
- "I implemented hybrid retrieval combining vector and keyword search with Reciprocal Rank Fusion, which improved recall by 20%"
- "Smart chunking preserves document structure - keeping tables intact and injecting section headers for context"
- "Query transformation with HyDE works great for conceptual questions, while multi-query helps with ambiguous queries"

**Evaluation**:
- "I use RAGAS for standard metrics but also built custom financial metrics like numerical accuracy"
- "LLM-as-judge with GPT-4 provides qualitative assessment that correlates well with human evaluation"
- "Golden dataset with 50+ test cases covers different complexity levels and query types"

**Multi-Agent System**:
- "Supervisor agent analyzes query complexity and routes to specialized agents"
- "Fact-checker validates claims against sources, flagging unsupported statements"
- "Agent trace visualization shows the reasoning process, making the system transparent"

**Production Readiness**:
- "Full observability with LangSmith for tracing every LLM call"
- "Automated regression testing runs daily to catch quality degradation"
- "Prompt injection defense with structured prompts and input validation"

**Cost Optimization**:
- "Embedding cache reduces API costs by 60%"
- "Modal's pay-per-use means $0 when idle"
- "Efficient chunking and retrieval keeps context window small"

---

## Next Steps After Completion

### Enhancements to Consider (Post-MVP)

1. **Advanced Features**:
   - Multi-modal support (analyze charts/graphs in documents)
   - Conversational memory (remember context across sessions)
   - Document comparison view (side-by-side)
   - Export to PDF/Word
   - Collaborative features (share conversations)

2. **Performance Optimizations**:
   - Response caching
   - Parallel agent execution
   - Speculative retrieval
   - Model quantization for embeddings

3. **Enterprise Features**:
   - Multi-tenancy
   - SSO integration
   - Audit logs
   - Usage analytics
   - Custom model fine-tuning

4. **Evaluation Improvements**:
   - Human feedback loop
   - A/B testing framework
   - Continuous evaluation pipeline
   - Benchmark against other systems

---

## Troubleshooting Guide

### Common Issues

**Issue**: Supabase connection timeout
**Solution**: Check if IP is whitelisted, verify credentials, use service role key for server-side

**Issue**: Modal cold start too slow
**Solution**: Increase `keep_warm` parameter, optimize image size, cache dependencies

**Issue**: pgvector queries slow
**Solution**: Ensure index is created (`ivfflat`), tune `lists` parameter, check table stats

**Issue**: LLM rate limits
**Solution**: Implement exponential backoff, use multiple API keys, add request queuing

**Issue**: Embedding API costs too high
**Solution**: Implement aggressive caching, use smaller embedding model, batch requests

**Issue**: Poor retrieval quality
**Solution**: Tune chunk size/overlap, adjust reranking threshold, improve query transformation

**Issue**: Agent execution too slow
**Solution**: Parallelize agent calls where possible, optimize tool implementations, cache results

---

## Resources & References

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Supabase Docs](https://supabase.com/docs)
- [pgvector Guide](https://github.com/pgvector/pgvector)
- [LangGraph Tutorial](https://python.langchain.com/docs/langgraph)
- [RAGAS Docs](https://docs.ragas.io/)
- [Modal Docs](https://modal.com/docs)

### Papers & Articles
- "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (RAG paper)
- "Lost in the Middle: How Language Models Use Long Contexts"
- "HyDE: Precise Zero-Shot Dense Retrieval"
- "Self-RAG: Learning to Retrieve, Generate, and Critique"

### Example Projects
- Look at LangChain cookbook for agent examples
- Study RAGAS example notebooks
- Check Modal examples for deployment patterns

---

## Final Checklist Before Demo

### Code Quality
- [ ] All code is type-hinted
- [ ] Tests pass (>80% coverage)
- [ ] No linting errors
- [ ] Code is formatted (black)
- [ ] No security vulnerabilities
- [ ] Environment variables documented

### Documentation
- [ ] README.md complete
- [ ] Architecture diagram created
- [ ] API endpoints documented
- [ ] Setup instructions tested
- [ ] Comments on complex logic

### Deployment
- [ ] Modal deployment works
- [ ] Vercel deployment works
- [ ] Environment variables set
- [ ] Health check passes
- [ ] CORS configured correctly

### Demo Readiness
- [ ] Sample documents uploaded
- [ ] Test queries prepared
- [ ] Metrics dashboard populated
- [ ] Agent trace visualization works
- [ ] Screenshots captured
- [ ] Demo video recorded (optional)

### Interview Prep
- [ ] Architecture diagram printed
- [ ] Talking points memorized
- [ ] Demo scenarios practiced
- [ ] Code walkthrough prepared
- [ ] Metrics can be explained

---

## Contact & Support

**For This Project**:
- GitHub: [your-repo-url]
- Demo: [your-demo-url]
- Video: [your-demo-video]

**External Resources**:
- Modal Community: https://modal.com/slack
- LangChain Discord: https://discord.gg/langchain
- Supabase Discord: https://discord.supabase.com

---

## Conclusion

This project demonstrates:
- ✅ Advanced AI engineering (RAG, agents, evals)
- ✅ Full-stack development (React + FastAPI)
- ✅ Modern cloud architecture (Modal + Supabase)
- ✅ Production-grade practices (testing, observability, security)
- ✅ Cost-conscious engineering (serverless, caching)
- ✅ Quality focus (comprehensive evaluation)

   