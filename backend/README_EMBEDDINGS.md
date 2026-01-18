# Embedding Pipeline Setup

## What We Built

The embedding pipeline converts document chunks into vector embeddings and stores them in Supabase for semantic search.

### Components

1. **EmbeddingService** (`src/rag/embeddings.py`)
   - Uses OpenAI's `text-embedding-3-small` model
   - 1536 dimensions (matches database schema)
   - Cost: $0.02 per 1M tokens
   - Supports batch embedding for efficiency

2. **VectorStore** (`src/db/vector_store.py`)
   - Stores chunks with embeddings in Supabase
   - Performs similarity search using pgvector
   - Supports filtering by document IDs
   - Returns results sorted by relevance

### How It Works

```
Document Text
    ↓
Chunking (SimpleChunker)
    ↓
Text Chunks
    ↓
Embeddings (OpenAI API)
    ↓
Vector Embeddings [1536 dimensions]
    ↓
Storage (Supabase + pgvector)
    ↓
Similarity Search (cosine distance)
    ↓
Relevant Chunks
```

## Prerequisites

Make sure your `.env` file has:

```bash
# Supabase (already configured ✓)
SUPABASE_URL=your-url
SUPABASE_SERVICE_KEY=your-key

# OpenAI (required for embeddings)
OPENAI_API_KEY=sk-...your-openai-api-key...
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

## Testing the Pipeline

Run the comprehensive test script:

```bash
cd backend
python test_embeddings.py
```

This test will:
1. ✅ Create document chunks
2. ✅ Generate embeddings using OpenAI
3. ✅ Store chunks with embeddings in Supabase
4. ✅ Perform similarity search
5. ✅ Test embedding quality
6. 🧹 Clean up test data

### Expected Output

```
🧪 Testing Embedding Pipeline
======================================================================

📝 STEP 1: Chunking Document
----------------------------------------------------------------------
✓ Created 4 chunks
✓ Chunk size: 300 chars
✓ Overlap: 50 chars

🔮 STEP 2: Generating Embeddings
----------------------------------------------------------------------
✓ Using model: text-embedding-3-small
✓ Dimensions: 1536
✓ Generated 4 embeddings
✓ Embedding dimensions: 1536

💾 STEP 3: Storing in Vector Database
----------------------------------------------------------------------
✓ Created test document: abc123...
✓ Stored 4 chunks in database

🔍 STEP 4: Testing Similarity Search
----------------------------------------------------------------------
Query: "What was Tesla's revenue in Q4?"
✓ Generated query embedding (1536 dims)
✓ Found 3 similar chunks

📊 Top Results:
----------------------------------------------------------------------
[Result 1] Similarity: 0.8234
Content: Tesla announced record financial results for Q4 2023...
  → Highly relevant! ✨

🎉 Embedding Pipeline Test Complete!
```

## Cost Estimation

### OpenAI Embeddings
- Model: `text-embedding-3-small`
- Cost: **$0.02 per 1M tokens**
- Typical 10-page PDF ≈ 5,000 words ≈ 7,000 tokens
- **Cost per document: ~$0.00014** (basically free!)

Example: Processing 1,000 documents (10 pages each)
- Tokens: 7M tokens
- Cost: **$0.14 total**

### Comparison with text-embedding-3-large
| Model | Dimensions | Cost per 1M tokens | Use Case |
|-------|------------|-------------------|----------|
| text-embedding-3-small | 1536 | $0.02 | General purpose (recommended) |
| text-embedding-3-large | 3072 | $0.13 | High precision needed |

We use **text-embedding-3-small** because:
- 6.5x cheaper
- Faster to compute
- Excellent quality for financial documents
- Works with ivfflat index (1536 dims)

## Next Steps

Now that embeddings are working, the next phase is:

1. **Document Upload API** (`api/routes/documents.py`)
   - Upload PDF/TXT files
   - Trigger processing pipeline
   - Return document metadata

2. **Retrieval Pipeline** (`src/rag/retrieval.py`)
   - Combine vector search + reranking
   - Filter by metadata (date, company, etc.)
   - Return top-k relevant chunks

3. **Answer Generation** (`src/agents/nodes.py`)
   - Use retrieved chunks as context
   - Generate answers with LLM
   - Track citations

4. **Query Transformations** (`src/rag/query_transform.py`)
   - Query expansion
   - Multi-query retrieval
   - Hypothetical document embeddings (HyDE)

## Troubleshooting

### "OpenAI API key not found"
Add `OPENAI_API_KEY` to your `.env` file:
```bash
OPENAI_API_KEY=sk-proj-...your-key-here...
```

### "Failed to insert chunks"
Make sure you ran `setup_supabase.sql` to create the schema:
1. Go to Supabase SQL Editor
2. Paste contents of `scripts/setup_supabase.sql`
3. Run the script

### "Similarity search failed"
Check that pgvector extension is enabled:
```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
```

### Rate Limits
OpenAI has rate limits:
- Free tier: 3 requests/min, 200 requests/day
- Paid tier: Much higher limits

If you hit rate limits, implement retry logic or batch processing.

## Performance Tips

1. **Batch Embeddings**
   - Embed multiple chunks at once (up to 2048 per request)
   - More efficient than individual calls

2. **Cache Embeddings**
   - Store embeddings to avoid regenerating
   - Hash content to detect changes

3. **Optimize Chunk Size**
   - Default: 1000 chars (≈250 tokens)
   - Smaller chunks = more precise retrieval
   - Larger chunks = more context per chunk

4. **Use Filters**
   - Filter by document_id before similarity search
   - Reduces search space and improves speed

5. **Monitor Costs**
   - Track token usage in your OpenAI dashboard
   - Set spending limits to avoid surprises

## Architecture Decisions

### Why text-embedding-3-small?
- Balances cost, speed, and quality
- 1536 dimensions work with ivfflat index
- Proven performance on financial documents

### Why pgvector over Pinecone/Weaviate?
- No additional service to manage
- Same database as structured data
- Lower latency (no network calls)
- Free (included with Supabase)

### Why cosine similarity?
- Standard for text embeddings
- Range-normalized (0-1)
- Captures semantic similarity well

### Why overlapping chunks?
- Preserves context across boundaries
- Important for sentences spanning chunks
- Improves retrieval quality
