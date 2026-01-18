# RAG Pipeline Implementation

## What We Built

A complete end-to-end Retrieval-Augmented Generation (RAG) system for answering questions from financial documents using semantic search and LLM generation.

## Architecture

```
User Question
    ↓
Query Embedding (OpenAI text-embedding-3-small)
    ↓
Vector Similarity Search (pgvector)
    ↓
Retrieved Chunks (Top-K most relevant)
    ↓
LLM Generation (OpenAI GPT-4o-mini with context)
    ↓
Answer + Citations
```

## Components

### 1. **LLM Provider** (`src/llm/provider.py`)

OpenAI-based text generation for creating answers from retrieved context.

**Features:**
- Uses GPT-4o-mini by default (fast, cheap, high quality)
- Temperature 0.0 for deterministic financial answers
- Automatic citation formatting
- Token usage tracking and cost estimation
- Streaming support (for real-time UI)

**Key Methods:**
- `generate()` - Basic text completion
- `generate_with_context()` - RAG answer generation with sources
- `get_usage_stats()` - Token usage and cost tracking

**Model Options:**
- `gpt-4o-mini` - $0.150/1M input, $0.600/1M output (default)
- `gpt-4o` - $2.50/1M input, $10.00/1M output (higher quality)

### 2. **Retriever** (`src/rag/retrieval.py`)

Retrieves relevant document chunks using semantic similarity.

**Features:**
- Vector similarity search
- Configurable top-k and similarity threshold
- Document filtering (search specific documents)
- Multi-query support (query expansion)

**Key Methods:**
- `retrieve()` - Main retrieval method
- `retrieve_with_context()` - Conversation-aware retrieval
- `retrieve_multi_query()` - Multiple query variations

### 3. **RAG Pipeline** (`src/rag/pipeline.py`)

Orchestrates the complete RAG process.

**Features:**
- End-to-end query processing
- Automatic fallback for no results
- Source attribution with similarity scores
- Conversation support (future)
- Batch query processing

**Key Methods:**
- `query()` - Single question RAG
- `query_with_conversation()` - Multi-turn conversations
- `batch_query()` - Process multiple questions
- `get_usage_stats()` - Usage tracking

## Usage

### Basic RAG Query

```python
from src.rag.pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline(
    top_k=5,           # Retrieve 5 chunks
    temperature=0.0    # Deterministic answers
)

# Ask a question
result = pipeline.query("What was Tesla's revenue in Q4 2023?")

print(result["answer"])
# Output: "Tesla's revenue in Q4 2023 was $25.2 billion..."

print(result["sources"])
# Output: [{"source_number": 1, "content": "...", "similarity": 0.87}, ...]
```

### Document-Specific Query

```python
# Search only specific documents
result = pipeline.query(
    question="What were the vehicle deliveries?",
    document_ids=["abc-123", "def-456"]  # Only search these docs
)
```

### Adjust Retrieval Parameters

```python
# More chunks, higher quality threshold
result = pipeline.query(
    question="Compare Apple and Tesla margins",
    top_k=10,               # Retrieve more chunks
    min_similarity=0.5      # Higher similarity threshold
)
```

### Custom System Prompt

```python
custom_prompt = """You are a financial analyst. Provide detailed 
quantitative analysis with specific numbers and percentages."""

result = pipeline.query(
    question="Analyze NVIDIA's growth",
    system_prompt=custom_prompt
)
```

## Testing

Run the comprehensive test suite:

```bash
cd backend
python test_rag_pipeline.py
```

This test will:
1. ✅ Create 3 sample financial documents (Tesla, Apple, NVIDIA)
2. ✅ Process, chunk, embed, and store them
3. ✅ Execute 4 different types of queries:
   - Simple factual questions
   - Cross-document comparisons
   - Complex analytical queries
   - Segment-specific questions
4. ✅ Test document filtering
5. ✅ Show usage statistics and costs
6. 🧹 Clean up test data

### Expected Output

```
🚀 RAG Pipeline Integration Test
======================================================================

📚 Setting Up Test Documents
======================================================================

Processing: tesla_q4_2023.txt
  ✓ Created 4 chunks
  ✓ Generated embeddings
  ✓ Stored 4 chunks in database

Processing: apple_q4_2023.txt
  ✓ Created 5 chunks
  ✓ Generated embeddings
  ✓ Stored 5 chunks in database

Processing: nvidia_q3_2024.txt
  ✓ Created 4 chunks
  ✓ Generated embeddings
  ✓ Stored 4 chunks in database

✅ Successfully processed 3 documents

======================================================================
🤖 Testing RAG Pipeline
======================================================================

Query 1: What was Tesla's revenue in Q4 2023?
Type: Simple factual query
----------------------------------------------------------------------

📊 Retrieval Stats:
  • Retrieved chunks: 3
  • Avg similarity: 0.842
  • Top similarity: 0.891

💬 Answer:
Tesla's revenue in Q4 2023 was $25.2 billion, which represented a 3% 
increase year-over-year. [Source 1] The automotive revenue specifically 
was $21.6 billion, while energy generation and storage revenue grew 10% 
to $1.4 billion. [Source 2]

📚 Sources (3 chunks used):
  [Source 1] Similarity: 0.891
  Tesla announced financial results for Q4 2023. Total revenue reached...

🎉 RAG Pipeline Test Complete!
```

## Performance & Costs

### Typical Query Costs

For a single RAG query with 5 retrieved chunks:

**Embeddings (Query):**
- Tokens: ~20 tokens
- Cost: $0.000004 (negligible)

**LLM Generation:**
- Input: ~2,000 tokens (context + question)
- Output: ~200 tokens (answer)
- Cost: $0.00042 per query

**Total per query: ~$0.0005** (half a cent)

### 1,000 Queries
- Total cost: **~$0.50**
- Processing time: ~30 seconds (concurrent)

### 10,000 Queries
- Total cost: **~$5.00**
- Reasonable for production workload

## Configuration

Add to your `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-proj-...your-key-here...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Optional - for LangSmith tracing
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=investment-research-ai
```

## Response Format

The pipeline returns a standardized response:

```python
{
    "answer": "The generated answer text with [Source X] citations...",
    
    "sources": [
        {
            "source_number": 1,
            "chunk_id": "abc-123",
            "document_id": "doc-456",
            "content": "Chunk content preview...",
            "metadata": {"document_name": "tesla_q4_2023.txt"},
            "similarity": 0.87
        },
        # ... more sources
    ],
    
    "metadata": {
        "retrieved_chunks": 5,
        "avg_similarity": 0.82,
        "top_similarity": 0.91,
        "model": "gpt-4o-mini",
        "usage": {
            "prompt_tokens": 2143,
            "completion_tokens": 187,
            "total_tokens": 2330
        },
        "status": "success"
    }
}
```

## Advanced Features (Future Roadmap)

### Query Transformations
- **HyDE** (Hypothetical Document Embeddings) - Generate hypothetical answer, embed it, search
- **Query Expansion** - Generate multiple query variations, retrieve from each
- **Query Reformulation** - Rewrite query for better retrieval

### Hybrid Retrieval
- Combine vector search (semantic) with keyword search (BM25)
- Reciprocal Rank Fusion (RRF) to merge results
- Better handling of exact matches + semantic similarity

### Reranking
- Cross-encoder reranking for better relevance
- Rerank top 20 → return top 5
- Improves precision significantly

### Conversation Memory
- Multi-turn conversation support
- Query reformulation using conversation history
- Maintain context across questions

### Advanced Filtering
- Filter by date ranges
- Filter by document type
- Filter by metadata tags

## Optimization Tips

### 1. Chunk Size Tuning
```python
# Smaller chunks = more precise retrieval
chunker = SimpleChunker(chunk_size=500, chunk_overlap=100)

# Larger chunks = more context per retrieval
chunker = SimpleChunker(chunk_size=1500, chunk_overlap=300)
```

### 2. Retrieval Parameters
```python
# Retrieve more, higher threshold
pipeline = RAGPipeline(top_k=10)
result = pipeline.query(question, min_similarity=0.6)

# Retrieve less, lower threshold (broader search)
pipeline = RAGPipeline(top_k=3)
result = pipeline.query(question, min_similarity=0.3)
```

### 3. Model Selection
```python
# Fast and cheap (default)
pipeline = RAGPipeline(
    llm_provider=LLMProvider(model="gpt-4o-mini")
)

# Higher quality, slower, more expensive
pipeline = RAGPipeline(
    llm_provider=LLMProvider(model="gpt-4o")
)
```

### 4. Temperature Tuning
```python
# Deterministic (factual queries)
pipeline = RAGPipeline(temperature=0.0)

# More creative (analysis, summaries)
pipeline = RAGPipeline(temperature=0.3)
```

## Troubleshooting

### "No relevant information found"

**Cause:** Query doesn't match document content semantically

**Solutions:**
- Rephrase the question
- Lower `min_similarity` threshold
- Increase `top_k` to retrieve more chunks
- Check if documents were processed correctly

### "Answer is incomplete"

**Cause:** Not enough context retrieved

**Solutions:**
- Increase `top_k` (more chunks)
- Increase chunk size (more context per chunk)
- Check if relevant information was split across chunks

### "Answer doesn't cite sources"

**Cause:** LLM not following citation instructions

**Solutions:**
- Adjust system prompt to emphasize citations
- Use GPT-4o instead of GPT-4o-mini
- Post-process answer to add citations

### High costs

**Cause:** Too many tokens per query

**Solutions:**
- Reduce `top_k` (fewer chunks)
- Reduce chunk size
- Use GPT-4o-mini instead of GPT-4o
- Implement caching for repeated queries

## Next Steps

Now that RAG pipeline is working:

1. **Build API Endpoints** (`api/routes/`)
   - `/documents/upload` - Upload and process documents
   - `/chat/query` - Answer questions
   - `/chat/conversation` - Multi-turn conversations

2. **Add Document Management**
   - List documents
   - Delete documents
   - View document chunks

3. **Enhance Retrieval**
   - Implement hybrid search (vector + keyword)
   - Add reranking with cross-encoder
   - Query transformations (HyDE, expansion)

4. **Production Features**
   - Rate limiting
   - Authentication
   - Caching
   - Monitoring/logging
   - Error handling

5. **Evaluation**
   - Build golden dataset
   - Implement RAGAS evaluation
   - A/B testing different configurations

6. **Frontend Integration**
   - Connect to API endpoints
   - Real-time streaming responses
   - Source highlighting
   - Conversation history UI
