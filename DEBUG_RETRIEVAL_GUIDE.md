# Debug Guide: "Recent Accounting Pronouncements" Not Found

## Problem
Your query for "Recent Accounting Pronouncements" in the Apple 10-K is returning "no information available" even though the section exists in the uploaded document.

## Diagnosis Steps

### Step 1: Verify the Section Exists in Chunks

Run the chunk inspector to see if the section was properly chunked:

```bash
cd backend
poetry run python inspect_chunks.py --doc-name apple --search "accounting"
```

**What to look for:**
- ✅ Chunks containing "Recent Accounting Pronouncements" exist
- ✅ Chunks have proper `parent_section` metadata
- ✅ Content is complete and readable

**Common issues:**
- ❌ Section was split across too many chunks
- ❌ Section header wasn't detected properly
- ❌ Content is truncated or corrupted

### Step 2: Test Retrieval Strategies

Run the retrieval debugger to see if your query can find the chunks:

```bash
cd backend
poetry run python debug_retrieval.py "Recent Accounting Pronouncements" --doc-name apple
```

**What to look for:**
- ✅ Vector search finds relevant chunks
- ✅ Keyword search finds relevant chunks
- ✅ Hybrid search finds relevant chunks
- ✅ Top results have high similarity scores (>0.7)

**Common issues:**
- ❌ Keyword search fails → FTS not configured
- ❌ Vector search ranks irrelevant chunks higher → embedding issue
- ❌ No chunks retrieved at all → database/embedding issue

### Step 3: Check LLM Response

If retrieval works but LLM says "no information":

**Possible causes:**
1. **Context truncation**: Too many chunks, LLM loses track
2. **Poor context formatting**: LLM can't find relevant info in chunks
3. **Prompt issue**: System prompt is too restrictive
4. **LLM hallucination**: LLM incorrectly determines info isn't there

## Common Fixes

### Fix 1: Full-Text Search Not Configured

If keyword search fails, you need to set up FTS:

```bash
# In Supabase SQL Editor, run:
# backend/migrations/add_fts_support.sql
```

### Fix 2: Re-chunk Document with Better Settings

If chunks don't have section context, re-process with better chunking:

```python
# In backend/src/document_processing/storage.py
# Change chunking settings:

from src.rag.chunking import FinancialDocumentChunker

chunker = FinancialDocumentChunker(
    chunk_size=1500,      # Increase from 1000
    chunk_overlap=300,    # Increase from 200
    preserve_tables=True,
    add_context=True      # Ensure this is True
)
```

Then re-upload your document.

### Fix 3: Use Query Transformation

Try query transformation to generate better search queries:

```python
# In your query, add:
result = rag_pipeline.query(
    question="Recent Accounting Pronouncements in Apple 10-K",
    strategy='hybrid',
    use_query_transform=True,  # Add this
    use_reranking=True          # Add this if you have Cohere API key
)
```

### Fix 4: Improve System Prompt

The default prompt might be too restrictive. Try a custom prompt:

```python
custom_prompt = """You are a financial research assistant specialized in analyzing 10-K filings.

When answering questions:
1. Search carefully through ALL provided context
2. Look for section headers and subsections
3. If you find partial information, provide what you can find
4. Cite specific sources using [Source X] notation
5. Only say "no information" if you've thoroughly checked all context

Be thorough and detail-oriented."""

result = rag_pipeline.query(
    question="Summarize Recent Accounting Pronouncements",
    system_prompt=custom_prompt
)
```

### Fix 5: Test with Direct Section Query

Try a more specific query that includes context:

Instead of:
```
"Summarize the Recent Accounting Pronouncements"
```

Try:
```
"In the Apple 10-K report, what does the Recent Accounting Pronouncements section say? Look for information about new accounting standards, ASUs, or changes in accounting policies."
```

## Testing Your Fixes

After applying fixes, test with these queries:

```bash
# Test 1: Exact section name
poetry run python debug_retrieval.py "Recent Accounting Pronouncements" --doc-name apple

# Test 2: Related keywords
poetry run python debug_retrieval.py "accounting standards updates ASU" --doc-name apple

# Test 3: Broader query
poetry run python debug_retrieval.py "accounting policy changes" --doc-name apple
```

## Advanced Debugging

### Check Database Directly

```python
from src.db.supabase import get_supabase

db = get_supabase()

# Get document ID
docs = db.table('documents').select('id, filename').ilike('filename', '%apple%').execute()
doc_id = docs.data[0]['id']

# Count chunks
chunks = db.table('document_chunks').select('id', count='exact').eq('document_id', doc_id).execute()
print(f"Total chunks: {chunks.count}")

# Search for specific text
result = db.table('document_chunks').select('content, metadata').eq('document_id', doc_id).execute()
for chunk in result.data:
    if 'accounting' in chunk['content'].lower():
        print(f"Found in chunk: {chunk['content'][:200]}...")
```

### Check Embeddings

```python
from src.rag.embeddings import EmbeddingService

embedding_service = EmbeddingService()

# Test query embedding
query_embedding = embedding_service.embed_query("Recent Accounting Pronouncements")
print(f"Query embedding dimension: {len(query_embedding)}")
print(f"First 5 values: {query_embedding[:5]}")

# Verify embeddings exist in DB
from src.db.supabase import get_supabase
db = get_supabase()

result = db.table('document_chunks').select('id, embedding').limit(1).execute()
if result.data and result.data[0].get('embedding'):
    print("✅ Chunks have embeddings")
else:
    print("❌ Chunks missing embeddings!")
```

## Still Not Working?

If none of the above works, the issue might be:

1. **Document upload failed**: Re-upload the Apple 10-K
2. **Chunking completely failed**: Check backend logs during upload
3. **Section doesn't exist**: Verify the actual PDF has this section
4. **Database issues**: Check Supabase for errors

### Get Help

Run the full diagnostic and share the output:

```bash
cd backend
poetry run python debug_retrieval.py "Recent Accounting Pronouncements" --doc-name apple > debug_output.txt
```

Then review `debug_output.txt` to see exactly where the pipeline fails.

## Prevention

To prevent similar issues in the future:

1. **Test uploads**: After uploading, test a few queries immediately
2. **Monitor chunking**: Check chunk count matches document size
3. **Review chunks**: Periodically inspect chunks for important documents
4. **Use metrics**: Track retrieval success rates in the Metrics dashboard
5. **Enable logging**: Set up proper logging to catch issues early

```python
# In backend/.env, add:
LOG_LEVEL=DEBUG
LANGSMITH_API_KEY=your_key  # For tracing
```
