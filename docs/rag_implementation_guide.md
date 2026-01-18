# Advanced RAG Pipeline Implementation Guide

## Overview

This document provides detailed implementation specifications for the production-grade RAG (Retrieval-Augmented Generation) pipeline. Use this alongside `plan.md` and `agents-implementation.md`.

**Location**: `backend/src/rag/`

**Files**:
- `pipeline.py` - Main RAG orchestration
- `chunking.py` - Smart document chunking
- `embeddings.py` - Embedding generation with caching
- `retrieval.py` - Hybrid retrieval (vector + keyword)
- `reranking.py` - Cohere reranking
- `query_transform.py` - Query transformation (HyDE, multi-query, decomposition)

---

## 1. Document Chunking Strategy

**File**: `backend/src/rag/chunking.py`

### The Problem
- PDFs have complex layouts (headers, sections, tables, multi-column)
- Naive chunking breaks context
- Tables must stay intact
- Financial documents have specific structures (10-Ks, earnings reports)

### The Solution
Structure-aware chunking that preserves document semantics.

```python
from typing import List, Dict, Tuple
import re
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter

@dataclass
class Chunk:
    """Represents a document chunk with metadata."""
    content: str
    chunk_type: str  # 'text', 'table', 'list'
    metadata: Dict
    position: int
    parent_section: str
    document_id: str

class FinancialDocumentChunker:
    """
    Intelligent chunking optimized for financial documents.
    
    Key features:
    - Detects document structure (headers, sections, tables)
    - Preserves tables intact
    - Adds context (parent headers) to chunks
    - Adaptive chunk sizing based on content type
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        preserve_tables: bool = True
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_tables = preserve_tables
        
        # Text splitter for regular content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_document(
        self, 
        text: str, 
        document_id: str,
        metadata: Dict = None
    ) -> List[Chunk]:
        """
        Main chunking method.
        
        Process:
        1. Detect document structure
        2. Extract tables separately
        3. Chunk text sections with context
        4. Combine all chunks with metadata
        """
        
        metadata = metadata or {}
        
        # Step 1: Detect structure
        sections = self._detect_sections(text)
        
        # Step 2: Extract tables
        tables = self._extract_tables(text) if self.preserve_tables else []
        
        # Step 3: Chunk each section
        all_chunks = []
        position = 0
        
        for section in sections:
            if section['type'] == 'table':
                # Keep tables intact
                chunk = Chunk(
                    content=section['content'],
                    chunk_type='table',
                    metadata={**metadata, 'section': section['header']},
                    position=position,
                    parent_section=section['header'],
                    document_id=document_id
                )
                all_chunks.append(chunk)
                position += 1
            
            elif section['type'] == 'text':
                # Chunk text with context injection
                text_chunks = self._chunk_with_context(
                    section['content'],
                    section['header']
                )
                
                for i, text_chunk in enumerate(text_chunks):
                    chunk = Chunk(
                        content=text_chunk,
                        chunk_type='text',
                        metadata={
                            **metadata,
                            'section': section['header'],
                            'chunk_index': i,
                            'total_chunks': len(text_chunks)
                        },
                        position=position,
                        parent_section=section['header'],
                        document_id=document_id
                    )
                    all_chunks.append(chunk)
                    position += 1
        
        return all_chunks
    
    def _detect_sections(self, text: str) -> List[Dict]:
        """
        Detect document sections based on headers and structure.
        
        Patterns to detect:
        - ALL CAPS HEADERS
        - Numbered sections (1., 1.1, etc.)
        - Financial statement headers
        - Item N (for 10-Ks)
        """
        
        sections = []
        lines = text.split('\n')
        current_section = {'header': 'Introduction', 'content': '', 'type': 'text'}
        
        # Common financial document headers
        header_patterns = [
            r'^[A-Z][A-Z\s]{10,}$',  # ALL CAPS (min 10 chars)
            r'^Item\s+\d+[A-Za-z]?\.',  # Item 1., Item 1A., etc.
            r'^\d+\.\s+[A-Z]',  # 1. Header, 2. Header
            r'^[A-Z][a-z]+\s+Statement',  # Income Statement, Balance Sheet
        ]
        
        for line in lines:
            line = line.strip()
            
            # Check if line is a header
            is_header = any(re.match(pattern, line) for pattern in header_patterns)
            
            if is_header and len(line) < 100:  # Headers shouldn't be too long
                # Save previous section
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'header': line,
                    'content': '',
                    'type': 'text'
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _extract_tables(self, text: str) -> List[Dict]:
        """
        Extract tables from text.
        
        Heuristics:
        - Multiple lines with consistent column separators
        - Numeric data in columns
        - Table-like keywords (Total, Amount, etc.)
        """
        
        tables = []
        lines = text.split('\n')
        
        # Look for table patterns
        table_start_keywords = ['total', 'amount', 'balance', 'revenue', 'income']
        in_table = False
        current_table = []
        
        for i, line in enumerate(lines):
            # Check if line looks like a table row
            # (has multiple numbers or consistent separators)
            number_count = len(re.findall(r'\d+[\d,\.]*', line))
            has_separator = '|' in line or '\t' in line
            
            if number_count >= 2 or has_separator:
                if not in_table:
                    in_table = True
                    # Include previous line as potential header
                    if i > 0:
                        current_table.append(lines[i-1])
                current_table.append(line)
            else:
                if in_table and len(current_table) >= 3:
                    # End of table
                    tables.append({
                        'content': '\n'.join(current_table),
                        'type': 'table'
                    })
                in_table = False
                current_table = []
        
        return tables
    
    def _chunk_with_context(self, text: str, section_header: str) -> List[str]:
        """
        Chunk text while preserving context by prepending section header.
        
        Example:
        Original chunk: "Revenue increased by 20%..."
        With context: "Financial Performance\nRevenue increased by 20%..."
        """
        
        # Split into base chunks
        base_chunks = self.text_splitter.split_text(text)
        
        # Add context to each chunk
        contextualized_chunks = []
        for chunk in base_chunks:
            # Prepend section header for context
            contextualized = f"## {section_header}\n\n{chunk}"
            contextualized_chunks.append(contextualized)
        
        return contextualized_chunks
    
    def _is_table_line(self, line: str) -> bool:
        """Check if a line is part of a table."""
        # Count numbers
        numbers = re.findall(r'\d+[\d,\.]*', line)
        # Check for separators
        separators = line.count('|') + line.count('\t')
        
        return len(numbers) >= 2 or separators >= 2


# Additional: Semantic Chunking (Advanced)
class SemanticChunker:
    """
    Chunk based on semantic similarity rather than character count.
    Groups sentences with similar embeddings together.
    """
    
    def __init__(self, embedding_service, similarity_threshold: float = 0.75):
        self.embeddings = embedding_service
        self.threshold = similarity_threshold
    
    async def _hyde(self, query: str) -> List[str]:
        """
        HyDE (Hypothetical Document Embeddings).
        
        Generate a hypothetical answer, then retrieve documents similar to it.
        Works well for conceptual questions.
        """
        
        prompt = f"""Given this question: "{query}"

Write a detailed hypothetical paragraph that would answer this question,
as it might appear in a financial document. Include:
- Specific details and context
- Relevant numbers and metrics
- Technical/financial terminology
- The style of a professional financial document

Write ONLY the hypothetical answer paragraph, nothing else.

Hypothetical answer:"""
        
        hypothetical_doc = await self.llm.generate(prompt, model="gpt-4o")
        
        # Return both original query and hypothetical doc
        return [query, hypothetical_doc.strip()]
    
    async def _multi_query(self, query: str) -> List[str]:
        """
        Generate multiple query variations.
        
        Improves recall by capturing different phrasings.
        """
        
        prompt = f"""Generate 3 alternative phrasings of this query that preserve 
the intent but use different words or perspectives:

Original query: "{query}"

Focus on financial/business terminology variations.

Return as JSON array: ["query1", "query2", "query3"]

Alternative queries:"""
        
        response = await self.llm.structured_output(
            prompt,
            schema={"type": "array", "items": {"type": "string"}},
            model="gpt-4o"
        )
        
        # Return original + variations
        return [query] + response
    
    async def _decompose(self, query: str) -> List[str]:
        """
        Decompose complex query into simpler sub-queries.
        
        Works well for multi-part or comparative questions.
        """
        
        prompt = f"""Break this complex question into 2-4 simpler, independent sub-questions:

Complex query: "{query}"

Each sub-question should:
- Be answerable independently
- Cover one aspect of the original question
- Be specific and clear

Return as JSON array: ["sub_q1", "sub_q2", "sub_q3"]

Sub-questions:"""
        
        sub_queries = await self.llm.structured_output(
            prompt,
            schema={"type": "array", "items": {"type": "string"}},
            model="gpt-4o"
        )
        
        return sub_queries
    
    def auto_select_strategy(self, query: str) -> QueryStrategy:
        """
        Automatically select best transformation strategy based on query.
        
        Heuristics:
        - "What is...", "Explain..." → HyDE
        - Comparative ("compare", "vs") → Decomposition
        - Ambiguous terms → Multi-query
        - Simple factual → None
        """
        
        query_lower = query.lower()
        
        # Decomposition for complex/comparative queries
        if any(word in query_lower for word in ['compare', 'vs', 'versus', 'difference between']):
            return QueryStrategy.DECOMPOSITION
        
        # HyDE for conceptual questions
        if any(query_lower.startswith(phrase) for phrase in ['what is', 'explain', 'describe', 'how does']):
            return QueryStrategy.HYDE
        
        # Multi-query for potentially ambiguous queries
        if len(query_lower.split()) <= 5:
            return QueryStrategy.MULTI_QUERY
        
        # Default: no transformation
        return QueryStrategy.NONE
```

---

## 6. Complete RAG Pipeline

**File**: `backend/src/rag/pipeline.py`

```python
from typing import List, Dict, Optional
import asyncio
from dataclasses import dataclass
import time

from .chunking import FinancialDocumentChunker
from .embeddings import EmbeddingService
from .retrieval import HybridRetriever
from .reranking import CohereReranker
from .query_transform import QueryTransformer, QueryStrategy

@dataclass
class RAGResult:
    """Result from RAG pipeline."""
    answer: str
    sources: List[Dict]
    metadata: Dict

class RAGPipeline:
    """
    Complete RAG pipeline orchestrating all components.
    """
    
    def __init__(
        self,
        db_client,
        llm_provider,
        embedding_service: Optional[EmbeddingService] = None,
        reranker: Optional[CohereReranker] = None
    ):
        self.db = db_client
        self.llm = llm_provider
        
        # Initialize components
        self.embeddings = embedding_service or EmbeddingService()
        self.chunker = FinancialDocumentChunker()
        self.retriever = HybridRetriever(
            self.db,
            self.embeddings,
            reranker
        )
        self.query_transformer = QueryTransformer(llm_provider)
    
    async def process_document(
        self,
        document_id: str,
        text: str,
        metadata: Dict
    ) -> Dict:
        """
        Process a document: chunk, embed, store.
        
        This is called after document upload.
        """
        
        start_time = time.time()
        
        # Step 1: Chunk document
        chunks = self.chunker.chunk_document(text, document_id, metadata)
        
        # Step 2: Extract text from chunks
        chunk_texts = [chunk.content for chunk in chunks]
        
        # Step 3: Generate embeddings (batched)
        embeddings = await self.embeddings.embed_texts(chunk_texts)
        
        # Step 4: Store chunks with embeddings
        stored_count = 0
        for chunk, embedding in zip(chunks, embeddings):
            await self.db.store_chunk(
                document_id=document_id,
                content=chunk.content,
                embedding=embedding,
                metadata={
                    **chunk.metadata,
                    'chunk_type': chunk.chunk_type,
                    'position': chunk.position,
                    'parent_section': chunk.parent_section
                }
            )
            stored_count += 1
        
        processing_time = time.time() - start_time
        
        return {
            'document_id': document_id,
            'chunks_created': stored_count,
            'processing_time': processing_time,
            'success': True
        }
    
    async def query(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        use_query_transform: bool = True,
        retrieval_strategy: str = 'hybrid'
    ) -> RAGResult:
        """
        Main query method.
        
        Process:
        1. Transform query (if enabled)
        2. Retrieve relevant chunks
        3. Generate answer with LLM
        4. Extract citations
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            filters: Metadata filters
            use_query_transform: Whether to use query transformation
            retrieval_strategy: 'vector', 'keyword', or 'hybrid'
        
        Returns:
            RAGResult with answer and sources
        """
        
        start_time = time.time()
        
        # Step 1: Query transformation (optional)
        if use_query_transform:
            strategy = self.query_transformer.auto_select_strategy(query)
            transformed_queries = await self.query_transformer.transform(query, strategy)
        else:
            transformed_queries = [query]
        
        # Step 2: Retrieve for all transformed queries
        all_results = []
        for tq in transformed_queries:
            results = await self.retriever.retrieve(
                query=tq,
                top_k=top_k,
                filters=filters,
                retrieval_strategy=retrieval_strategy
            )
            all_results.extend(results)
        
        # Deduplicate by chunk_id
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.chunk_id not in seen_ids:
                seen_ids.add(result.chunk_id)
                unique_results.append(result)
        
        # Take top_k
        unique_results = sorted(unique_results, key=lambda x: x.score, reverse=True)[:top_k]
        
        # Step 3: Format context for LLM
        context = self._format_context(unique_results)
        
        # Step 4: Generate answer
        answer_prompt = f"""Answer this question using ONLY the provided documents.

Question: {query}

Documents:
{context}

Instructions:
- Cite every claim with [doc_X] where X is the document number
- If information is not in the documents, explicitly state that
- Be precise with numbers, dates, and facts
- Quote directly when important for accuracy

Answer:"""
        
        answer = await self.llm.generate(answer_prompt, model="gpt-4o")
        
        # Step 5: Extract citations
        citations = self._extract_citations(answer, unique_results)
        
        # Step 6: Prepare metadata
        metadata = {
            'query': query,
            'transformed_queries': transformed_queries,
            'num_sources': len(unique_results),
            'retrieval_strategy': retrieval_strategy,
            'processing_time': time.time() - start_time
        }
        
        return RAGResult(
            answer=answer,
            sources=[self._result_to_dict(r) for r in unique_results],
            metadata=metadata
        )
    
    def _format_context(self, results: List) -> str:
        """Format retrieved chunks for LLM context."""
        formatted = []
        for i, result in enumerate(results):
            formatted.append(f"[doc_{i}]\n{result.content}\n")
        return "\n".join(formatted)
    
    def _extract_citations(self, answer: str, results: List) -> List[Dict]:
        """Extract citation markers from answer."""
        import re
        
        citations = []
        pattern = r'\[doc_(\d+)\]'
        
        for match in re.finditer(pattern, answer):
            doc_idx = int(match.group(1))
            if doc_idx < len(results):
                citations.append({
                    'chunk_id': results[doc_idx].chunk_id,
                    'content': results[doc_idx].content[:200] + '...',
                    'metadata': results[doc_idx].metadata
                })
        
        return citations
    
    def _result_to_dict(self, result) -> Dict:
        """Convert RetrievalResult to dict."""
        return {
            'chunk_id': result.chunk_id,
            'content': result.content,
            'score': result.score,
            'metadata': result.metadata,
            'retrieval_method': result.retrieval_method
        }
    
    async def get_relevant_context(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Lightweight method to just get relevant context without generating answer.
        Useful for agents that need context.
        """
        
        results = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            retrieval_strategy='hybrid'
        )
        
        return [self._result_to_dict(r) for r in results]
```

---

## 7. Testing the RAG Pipeline

**File**: `backend/tests/test_rag.py`

```python
import pytest
from src.rag.pipeline import RAGPipeline
from src.rag.chunking import FinancialDocumentChunker
from src.rag.embeddings import EmbeddingService

# Sample financial document text
SAMPLE_10K = """
Item 1. Business

Apple Inc. designs, manufactures, and markets smartphones, personal computers, 
tablets, wearables, and accessories worldwide.

Revenue
For fiscal year 2023, total revenue was $383.9 billion, an increase of 2% 
compared to fiscal year 2022.

Research and Development
R&D expenses were $29.9 billion in 2023, representing 7.8% of total revenue.
"""

@pytest.mark.asyncio
async def test_document_chunking():
    """Test smart chunking preserves structure."""
    
    chunker = FinancialDocumentChunker(chunk_size=500, chunk_overlap=50)
    chunks = chunker.chunk_document(SAMPLE_10K, "doc_1")
    
    # Should create multiple chunks
    assert len(chunks) > 1
    
    # Should detect sections
    sections = set(chunk.parent_section for chunk in chunks)
    assert 'Item 1. Business' in sections or 'Business' in sections
    
    # Should preserve numbers
    revenue_chunk = next(c for c in chunks if '383.9' in c.content)
    assert revenue_chunk is not None


@pytest.mark.asyncio
async def test_embedding_caching():
    """Test embedding cache reduces API calls."""
    
    embeddings = EmbeddingService(cache_backend='memory')
    
    texts = ["Apple revenue increased", "Microsoft profit grew"]
    
    # First call - cache miss
    emb1 = await embeddings.embed_texts(texts)
    cache_stats1 = await embeddings.get_cache_stats()
    
    # Second call - cache hit
    emb2 = await embeddings.embed_texts(texts)
    cache_stats2 = await embeddings.get_cache_stats()
    
    # Same results
    assert emb1 == emb2
    
    # Cache size increased
    assert cache_stats2['memory_cache_size'] >= cache_stats1['memory_cache_size']


@pytest.mark.asyncio
async def test_hybrid_retrieval():
    """Test hybrid retrieval finds relevant chunks."""
    
    # Mock setup
    mock_db = MockDatabase()
    mock_llm = MockLLMProvider()
    
    pipeline = RAGPipeline(mock_db, mock_llm)
    
    # Process document
    await pipeline.process_document("doc_1", SAMPLE_10K, {"type": "10-K"})
    
    # Query
    result = await pipeline.query(
        "What was Apple's revenue in 2023?",
        retrieval_strategy='hybrid'
    )
    
    # Should find relevant information
    assert '383.9' in result.answer
    assert len(result.sources) > 0
    assert any('revenue' in s['content'].lower() for s in result.sources)


@pytest.mark.asyncio
async def test_query_transformation():
    """Test query transformation improves retrieval."""
    
    from src.rag.query_transform import QueryTransformer, QueryStrategy
    
    mock_llm = MockLLMProvider()
    transformer = QueryTransformer(mock_llm)
    
    # Test HyDE
    queries = await transformer.transform(
        "What is revenue recognition?",
        QueryStrategy.HYDE
    )
    assert len(queries) == 2  # Original + hypothetical
    
    # Test multi-query
    queries = await transformer.transform(
        "Apple revenue",
        QueryStrategy.MULTI_QUERY
    )
    assert len(queries) > 1  # Original + variations
    
    # Test decomposition
    queries = await transformer.transform(
        "Compare Apple and Microsoft revenue and profit margins",
        QueryStrategy.DECOMPOSITION
    )
    assert len(queries) >= 2  # Should break into sub-queries


@pytest.mark.asyncio
async def test_citation_extraction():
    """Test citations are properly extracted."""
    
    mock_db = MockDatabase()
    mock_llm = MockLLMProvider()
    
    pipeline = RAGPipeline(mock_db, mock_llm)
    
    # Process and query
    await pipeline.process_document("doc_1", SAMPLE_10K, {})
    result = await pipeline.query("What was Apple's R&D spending?")
    
    # Should have citations
    assert len(result.metadata['citations']) > 0
    assert any('[doc_' in result.answer)


@pytest.mark.asyncio
async def test_numerical_accuracy():
    """Test that numbers are preserved accurately."""
    
    mock_db = MockDatabase()
    mock_llm = MockLLMProvider()
    
    pipeline = RAGPipeline(mock_db, mock_llm)
    
    await pipeline.process_document("doc_1", SAMPLE_10K, {})
    result = await pipeline.query("What was Apple's R&D spending percentage?")
    
    # Should preserve exact percentage
    assert '7.8%' in result.answer or '7.8' in result.answer
```

---

## 8. Performance Optimization Tips

### Caching Strategy
```python
# Multi-level cache
1. Memory cache (fast, limited)
   - Store recent embeddings
   - LRU eviction

2. Database cache (persistent)
   - Store all embeddings
   - Indexed by hash

3. Query result cache (optional)
   - Cache entire query results
   - Expire after 1 hour
```

### Batching
```python
# Batch embedding calls
texts = [chunk1, chunk2, ..., chunk100]
embeddings = await embed_service.embed_texts(texts)  # Single API call

# vs
for text in texts:
    embedding = await embed_service.embed_texts([text])  # 100 API calls!
```

### Parallel Processing
```python
# Process multiple documents in parallel
import asyncio

documents = [doc1, doc2, doc3]
results = await asyncio.gather(*[
    pipeline.process_document(doc.id, doc.text, doc.metadata)
    for doc in documents
])
```

### Index Optimization
```sql
-- Tune pgvector index
CREATE INDEX ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);  -- Tune based on dataset size

-- Rule of thumb: lists = sqrt(num_rows)
-- More lists = faster search, lower recall
-- Fewer lists = slower search, higher recall

-- Analyze table after bulk inserts
ANALYZE document_chunks;
```

---

## 9. Evaluation & Monitoring

### Track Key Metrics
```python
@dataclass
class RAGMetrics:
    """Track RAG pipeline performance."""
    
    # Retrieval metrics
    retrieval_latency: float  # Time to retrieve
    num_chunks_retrieved: int
    avg_chunk_relevance: float
    
    # Generation metrics
    generation_latency: float
    tokens_used: int
    cost: float
    
    # Quality metrics
    has_citations: bool
    citation_count: int
    answer_length: int
    
    # Cache metrics
    cache_hit_rate: float
    
    def to_dict(self) -> Dict:
        return {
            'retrieval_latency_ms': self.retrieval_latency * 1000,
            'generation_latency_ms': self.generation_latency * 1000,
            'total_latency_ms': (self.retrieval_latency + self.generation_latency) * 1000,
            'tokens_used': self.tokens_used,
            'cost_usd': self.cost,
            'citations': self.citation_count,
            'cache_hit_rate': self.cache_hit_rate
        }
```

### Log Every Query
```python
# In pipeline.py
async def query(self, query: str, ...) -> RAGResult:
    start = time.time()
    
    # ... retrieval ...
    retrieval_time = time.time() - start
    
    # ... generation ...
    generation_time = time.time() - start - retrieval_time
    
    # Log metrics
    await self._log_metrics(RAGMetrics(
        retrieval_latency=retrieval_time,
        generation_latency=generation_time,
        # ... other metrics
    ))
```

---

## 10. Common Pitfalls & Solutions

### Pitfall 1: Context Window Overflow
```python
# Problem: Too many chunks exceed LLM context window

# Solution: Intelligent truncation
def truncate_context(chunks: List[str], max_tokens: int = 8000) -> List[str]:
    """Keep most relevant chunks within token budget."""
    current_tokens = 0
    selected = []
    
    for chunk in chunks:
        chunk_tokens = len(chunk) // 4  # Rough estimate
        if current_tokens + chunk_tokens > max_tokens:
            break
        selected.append(chunk)
        current_tokens += chunk_tokens
    
    return selected
```

### Pitfall 2: Poor Chunking Breaks Tables
```python
# Problem: Table split across chunks loses meaning

# Solution: Keep tables intact (implemented in chunker)
if section['type'] == 'table':
    # Store entire table as single chunk
    chunks.append(Chunk(content=table, chunk_type='table'))
```

### Pitfall 3: No Diversity in Results
```python
# Problem: Top 10 results all from same document section

# Solution: Use MMR for diversity
from .retrieval import MMRRetriever

mmr = MMRRetriever(embeddings, lambda_param=0.7)
diverse_results = await mmr.diversify_results(query, candidates, k=10)
```

### Pitfall 4: Slow First Query (Cold Start)
```python
# Problem: First embedding call is slow

# Solution: Warm up cache on startup
async def warm_up_cache():
    """Precompute common query embeddings."""
    common_queries = [
        "revenue",
        "profit",
        "cash flow",
        "earnings per share"
    ]
    await embeddings.embed_texts(common_queries)
```

---

## 11. Example Usage in FastAPI

```python
# In your API route
from fastapi import APIRouter, Depends
from src.rag.pipeline import RAGPipeline

router = APIRouter()

@router.post("/query")
async def query_documents(
    query: str,
    top_k: int = 10,
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Query documents with RAG."""
    
    result = await pipeline.query(
        query=query,
        top_k=top_k,
        retrieval_strategy='hybrid'
    )
    
    return {
        'answer': result.answer,
        'sources': result.sources,
        'metadata': result.metadata
    }

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """Upload and process a document."""
    
    # Parse document
    text = await parse_pdf(file)
    
    # Process through RAG pipeline
    result = await pipeline.process_document(
        document_id=str(uuid.uuid4()),
        text=text,
        metadata={'filename': file.filename}
    )
    
    return result
```

---

## Summary

This RAG implementation provides:

✅ **Smart Chunking**: Structure-aware, preserves tables, adds context  
✅ **Efficient Embeddings**: Batching, caching, retry logic  
✅ **Hybrid Retrieval**: Vector + keyword with RRF fusion  
✅ **Reranking**: Cohere for precision boost  
✅ **Query Transformation**: HyDE, multi-query, decomposition  
✅ **Complete Pipeline**: End-to-end orchestration  
✅ **Testing**: Comprehensive test suite  
✅ **Monitoring**: Metrics tracking  
✅ **Optimization**: Performance best practices  

**With plan.md + agents-implementation.md + rag-implementation.md, you have complete specifications for a production-grade AI system!** def chunk_semantically(self, text: str) -> List[str]:
        """
        Chunk text based on semantic boundaries.
        
        Algorithm:
        1. Split into sentences
        2. Embed each sentence
        3. Calculate cosine similarity between adjacent sentences
        4. Create chunk boundary when similarity drops below threshold
        """
        
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Embed all sentences
        embeddings = await self.embeddings.embed_texts(sentences)
        embeddings_array = np.array(embeddings)
        
        # Calculate similarities between adjacent sentences
        chunks = []
        current_chunk = [sentences[0]]
        
        for i in range(1, len(sentences)):
            # Cosine similarity between current and previous sentence
            sim = cosine_similarity(
                embeddings_array[i-1:i],
                embeddings_array[i:i+1]
            )[0][0]
            
            if sim >= self.threshold:
                # Similar enough, add to current chunk
                current_chunk.append(sentences[i])
            else:
                # Semantic boundary detected, start new chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentences[i]]
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
```

---

## 2. Embedding Service

**File**: `backend/src/rag/embeddings.py`

### Key Features
- Batch processing for efficiency
- Aggressive caching to reduce costs
- Rate limiting to avoid API throttling
- Retry logic with exponential backoff

```python
import asyncio
import hashlib
from typing import List, Dict, Optional
import numpy as np
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class EmbeddingService:
    """
    Production-grade embedding service with caching and optimization.
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-large",
        cache_backend: str = "memory",  # 'memory' or 'db'
        batch_size: int = 100
    ):
        self.model = model
        self.dimension = 3072  # text-embedding-3-large dimension
        self.batch_size = batch_size
        self.client = AsyncOpenAI()
        
        # Cache
        self.cache_backend = cache_backend
        self._memory_cache: Dict[str, List[float]] = {}
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts with caching and batching.
        
        Process:
        1. Check cache for each text
        2. Batch uncached texts
        3. Call API in batches
        4. Store in cache
        5. Return in original order
        """
        
        # Step 1: Check cache
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            
            # Try memory cache
            if cache_key in self._memory_cache:
                results[i] = self._memory_cache[cache_key]
            else:
                # Try DB cache if available
                if self.cache_backend == 'db':
                    cached = await self._get_from_db_cache(cache_key)
                    if cached:
                        results[i] = cached
                        self._memory_cache[cache_key] = cached
                        continue
                
                # Not cached
                uncached_indices.append(i)
                uncached_texts.append(text)
        
        # Step 2: Generate embeddings for uncached texts
        if uncached_texts:
            embeddings = await self._generate_embeddings(uncached_texts)
            
            # Store in cache and results
            for idx, embedding in zip(uncached_indices, embeddings):
                cache_key = self._get_cache_key(texts[idx])
                self._memory_cache[cache_key] = embedding
                
                if self.cache_backend == 'db':
                    await self._store_in_db_cache(cache_key, embedding)
                
                results[idx] = embedding
        
        return results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings with retry logic and batching.
        """
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float"
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Rate limiting: small delay between batches
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                print(f"Error embedding batch {i}: {e}")
                raise
        
        return all_embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """Embed a single query (optimized for queries)."""
        embeddings = await self.embed_texts([query])
        return embeddings[0]
    
    def _get_cache_key(self, text: str) -> str:
        """Generate deterministic cache key from text."""
        # Use MD5 hash of text
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    async def _get_from_db_cache(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from database cache."""
        # Implement based on your DB
        # Example with Supabase:
        try:
            from src.db.supabase import get_supabase_client
            db = get_supabase_client()
            
            result = await db.table('embedding_cache').select('embedding').eq('cache_key', cache_key).single()
            return result['embedding'] if result else None
        except:
            return None
    
    async def _store_in_db_cache(self, cache_key: str, embedding: List[float]):
        """Store embedding in database cache."""
        try:
            from src.db.supabase import get_supabase_client
            db = get_supabase_client()
            
            await db.table('embedding_cache').upsert({
                'cache_key': cache_key,
                'embedding': embedding,
                'model': self.model
            })
        except Exception as e:
            print(f"Error caching embedding: {e}")
    
    def cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        emb1_arr = np.array(emb1)
        emb2_arr = np.array(emb2)
        
        return np.dot(emb1_arr, emb2_arr) / (
            np.linalg.norm(emb1_arr) * np.linalg.norm(emb2_arr)
        )
    
    async def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        return {
            'memory_cache_size': len(self._memory_cache),
            'cache_backend': self.cache_backend,
            'model': self.model
        }
```

---

## 3. Hybrid Retrieval System

**File**: `backend/src/rag/retrieval.py`

### The Power of Hybrid Search
- **Vector search**: Great for semantic similarity, conceptual matches
- **Keyword search**: Great for exact matches, specific terms, names
- **Fusion**: Best of both worlds

```python
from typing import List, Dict, Optional
import asyncio
from dataclasses import dataclass

@dataclass
class RetrievalResult:
    """Single retrieval result."""
    chunk_id: str
    content: str
    score: float
    metadata: Dict
    retrieval_method: str  # 'vector', 'keyword', or 'hybrid'

class HybridRetriever:
    """
    Hybrid retrieval combining vector search (pgvector) and keyword search (PostgreSQL FTS).
    
    Uses Reciprocal Rank Fusion (RRF) to combine rankings.
    """
    
    def __init__(
        self,
        db_client,
        embedding_service,
        reranker=None,
        rrf_k: int = 60
    ):
        self.db = db_client
        self.embeddings = embedding_service
        self.reranker = reranker
        self.rrf_k = rrf_k
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict] = None,
        retrieval_strategy: str = 'hybrid'  # 'vector', 'keyword', or 'hybrid'
    ) -> List[RetrievalResult]:
        """
        Main retrieval method.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters (e.g., {'document_type': '10-K'})
            retrieval_strategy: Which retrieval method(s) to use
        
        Returns:
            List of retrieved chunks, ranked by relevance
        """
        
        if retrieval_strategy == 'vector':
            results = await self._vector_search(query, top_k * 2, filters)
        
        elif retrieval_strategy == 'keyword':
            results = await self._keyword_search(query, top_k * 2, filters)
        
        else:  # hybrid
            # Run both searches in parallel
            vector_results, keyword_results = await asyncio.gather(
                self._vector_search(query, top_k * 2, filters),
                self._keyword_search(query, top_k * 2, filters)
            )
            
            # Fuse results with RRF
            results = self._reciprocal_rank_fusion(
                vector_results,
                keyword_results,
                k=self.rrf_k
            )
        
        # Rerank if reranker available
        if self.reranker and len(results) > top_k:
            results = await self.reranker.rerank(query, results, top_k)
        else:
            results = results[:top_k]
        
        return results
    
    async def _vector_search(
        self,
        query: str,
        k: int,
        filters: Optional[Dict]
    ) -> List[RetrievalResult]:
        """
        Vector similarity search using pgvector.
        
        Uses cosine distance: 1 - (embedding <=> query_embedding)
        """
        
        # Generate query embedding
        query_embedding = await self.embeddings.embed_query(query)
        
        # Build SQL query
        sql = """
            SELECT 
                id,
                content,
                metadata,
                1 - (embedding <=> $1::vector) as similarity
            FROM document_chunks
            WHERE 1=1
        """
        
        params = [query_embedding]
        param_count = 1
        
        # Add filters
        if filters:
            for key, value in filters.items():
                param_count += 1
                sql += f" AND metadata->>{param_count}::text = ${param_count}"
                params.append(value)
        
        # Order and limit
        sql += f" ORDER BY embedding <=> $1::vector LIMIT ${param_count + 1}"
        params.append(k)
        
        # Execute
        rows = await self.db.fetch(sql, *params)
        
        # Convert to RetrievalResult
        results = [
            RetrievalResult(
                chunk_id=row['id'],
                content=row['content'],
                score=row['similarity'],
                metadata=row['metadata'],
                retrieval_method='vector'
            )
            for row in rows
        ]
        
        return results
    
    async def _keyword_search(
        self,
        query: str,
        k: int,
        filters: Optional[Dict]
    ) -> List[RetrievalResult]:
        """
        Keyword search using PostgreSQL full-text search.
        
        Uses tsvector and ts_rank for ranking.
        """
        
        sql = """
            SELECT 
                id,
                content,
                metadata,
                ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
            FROM document_chunks
            WHERE search_vector @@ plainto_tsquery('english', $1)
        """
        
        params = [query]
        param_count = 1
        
        # Add filters
        if filters:
            for key, value in filters.items():
                param_count += 1
                sql += f" AND metadata->>'{key}' = ${param_count}"
                params.append(value)
        
        # Order and limit
        sql += f" ORDER BY rank DESC LIMIT ${param_count + 1}"
        params.append(k)
        
        # Execute
        rows = await self.db.fetch(sql, *params)
        
        # Convert to RetrievalResult
        results = [
            RetrievalResult(
                chunk_id=row['id'],
                content=row['content'],
                score=row['rank'],
                metadata=row['metadata'],
                retrieval_method='keyword'
            )
            for row in rows
        ]
        
        return results
    
    def _reciprocal_rank_fusion(
        self,
        list1: List[RetrievalResult],
        list2: List[RetrievalResult],
        k: int = 60
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion algorithm.
        
        RRF formula: score(d) = Σ 1/(k + rank(d))
        
        Combines rankings from multiple retrievers.
        Documents appearing in both lists get higher scores.
        
        Args:
            list1: Results from first retriever
            list2: Results from second retriever
            k: RRF constant (typically 60)
        
        Returns:
            Fused and ranked results
        """
        
        scores = {}
        doc_map = {}
        
        # Score from first list
        for rank, result in enumerate(list1, start=1):
            doc_id = result.chunk_id
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
            if doc_id not in doc_map:
                doc_map[doc_id] = result
        
        # Score from second list
        for rank, result in enumerate(list2, start=1):
            doc_id = result.chunk_id
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
            if doc_id not in doc_map:
                doc_map[doc_id] = result
        
        # Sort by fused score
        ranked_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Create result list with hybrid scores
        fused_results = []
        for doc_id, score in ranked_ids:
            result = doc_map[doc_id]
            result.score = score
            result.retrieval_method = 'hybrid'
            fused_results.append(result)
        
        return fused_results


# Additional: MMR (Maximal Marginal Relevance) for diversity
class MMRRetriever:
    """
    Retrieves diverse results using Maximal Marginal Relevance.
    Avoids redundant/similar chunks in results.
    """
    
    def __init__(self, embedding_service, lambda_param: float = 0.5):
        self.embeddings = embedding_service
        self.lambda_param = lambda_param  # Balance relevance vs diversity
    
    async def diversify_results(
        self,
        query: str,
        candidates: List[RetrievalResult],
        k: int
    ) -> List[RetrievalResult]:
        """
        Select k diverse results from candidates using MMR.
        
        MMR formula:
        MMR = argmax[λ * Sim(q, d) - (1-λ) * max Sim(d, s)]
                d∈D\S                    s∈S
        
        Where:
        - q = query
        - d = candidate document
        - S = selected documents
        - λ = relevance vs diversity tradeoff
        """
        
        if len(candidates) <= k:
            return candidates
        
        # Embed query and all candidates
        query_emb = await self.embeddings.embed_query(query)
        candidate_texts = [c.content for c in candidates]
        candidate_embs = await self.embeddings.embed_texts(candidate_texts)
        
        # Calculate relevance scores
        relevance_scores = [
            self.embeddings.cosine_similarity(query_emb, cand_emb)
            for cand_emb in candidate_embs
        ]
        
        # MMR selection
        selected_indices = []
        remaining_indices = list(range(len(candidates)))
        
        # Select first document (highest relevance)
        first_idx = max(remaining_indices, key=lambda i: relevance_scores[i])
        selected_indices.append(first_idx)
        remaining_indices.remove(first_idx)
        
        # Select remaining k-1 documents
        while len(selected_indices) < k and remaining_indices:
            mmr_scores = []
            
            for idx in remaining_indices:
                # Relevance component
                relevance = relevance_scores[idx]
                
                # Diversity component (max similarity to selected docs)
                max_sim = max(
                    self.embeddings.cosine_similarity(
                        candidate_embs[idx],
                        candidate_embs[sel_idx]
                    )
                    for sel_idx in selected_indices
                )
                
                # MMR score
                mmr = self.lambda_param * relevance - (1 - self.lambda_param) * max_sim
                mmr_scores.append((idx, mmr))
            
            # Select document with highest MMR
            best_idx = max(mmr_scores, key=lambda x: x[1])[0]
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        return [candidates[i] for i in selected_indices]
```

---

## 4. Reranking

**File**: `backend/src/rag/reranking.py`

### Why Rerank?
- Initial retrieval optimizes for recall (get all relevant docs)
- Reranking optimizes for precision (get most relevant at top)
- Cohere rerank models are trained specifically for this

```python
import cohere
from typing import List
from .retrieval import RetrievalResult

class CohereReranker:
    """
    Rerank retrieved documents using Cohere's rerank API.
    """
    
    def __init__(self, api_key: str, model: str = "rerank-english-v3.0"):
        self.client = cohere.Client(api_key)
        self.model = model
    
    async def rerank(
        self,
        query: str,
        documents: List[RetrievalResult],
        top_k: int
    ) -> List[RetrievalResult]:
        """
        Rerank documents using Cohere.
        
        Args:
            query: Search query
            documents: Initial retrieved documents
            top_k: Number of top documents to return
        
        Returns:
            Reranked documents
        """
        
        if len(documents) <= top_k:
            return documents
        
        # Extract text content
        texts = [doc.content for doc in documents]
        
        # Call Cohere rerank API
        response = self.client.rerank(
            query=query,
            documents=texts,
            top_n=top_k,
            model=self.model
        )
        
        # Map back to original documents with new scores
        reranked = []
        for result in response.results:
            original_doc = documents[result.index]
            original_doc.score = result.relevance_score
            reranked.append(original_doc)
        
        return reranked
```

---

## 5. Query Transformation

**File**: `backend/src/rag/query_transform.py`

### Three Strategies

```python
from typing import List
from enum import Enum

class QueryStrategy(Enum):
    NONE = "none"
    HYDE = "hyde"
    MULTI_QUERY = "multi_query"
    DECOMPOSITION = "decomposition"

class QueryTransformer:
    """
    Transform queries for better retrieval.
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def transform(
        self,
        query: str,
        strategy: QueryStrategy = QueryStrategy.NONE
    ) -> List[str]:
        """
        Transform query based on strategy.
        
        Returns list of queries to retrieve for.
        """
        
        if strategy == QueryStrategy.NONE:
            return [query]
        elif strategy == QueryStrategy.HYDE:
            return await self._hyde(query)
        elif strategy == QueryStrategy.MULTI_QUERY:
            return await self._multi_query(query)
        elif strategy == QueryStrategy.DECOMPOSITION:
            return await self._decompose(query)
        else:
            return [query]
    
    async