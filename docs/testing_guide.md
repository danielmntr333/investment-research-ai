# Testing Guide - Comprehensive Testing Strategy

## Overview

This guide provides complete testing strategies for all components of the Investment Research AI platform.

**Testing Levels**:
1. Unit Tests (Functions, classes)
2. Integration Tests (Components working together)
3. End-to-End Tests (Full user flows)
4. Evaluation Tests (AI quality metrics)
5. Performance Tests (Load, stress)

**Tools**:
- pytest (Python testing)
- pytest-asyncio (Async tests)
- pytest-cov (Coverage)
- Playwright (E2E tests)
- Locust (Load testing)

---

## 1. Unit Tests

### File: `backend/tests/unit/test_chunking.py`

```python
import pytest
from src.rag.chunking import FinancialDocumentChunker

class TestFinancialDocumentChunker:
    """Test smart document chunking."""
    
    @pytest.fixture
    def chunker(self):
        return FinancialDocumentChunker(chunk_size=500, chunk_overlap=50)
    
    @pytest.fixture
    def sample_document(self):
        return """
Item 1. Business

Apple Inc. designs, manufactures, and markets smartphones.

Revenue
Total revenue was $383.9 billion in 2023.

Table:
Quarter | Revenue
Q1      | $95B
Q2      | $97B
Q3      | $96B
Q4      | $95B
"""
    
    def test_chunk_creation(self, chunker, sample_document):
        """Test that chunks are created."""
        chunks = chunker.chunk_document(sample_document, "doc_1")
        
        assert len(chunks) > 0
        assert all(hasattr(c, 'content') for c in chunks)
        assert all(hasattr(c, 'metadata') for c in chunks)
    
    def test_section_detection(self, chunker, sample_document):
        """Test that document sections are detected."""
        chunks = chunker.chunk_document(sample_document, "doc_1")
        
        # Should detect "Item 1. Business" and "Revenue" sections
        sections = set(c.parent_section for c in chunks)
        assert len(sections) >= 2
    
    def test_table_preservation(self, chunker, sample_document):
        """Test that tables are kept intact."""
        chunks = chunker.chunk_document(sample_document, "doc_1")
        
        table_chunks = [c for c in chunks if c.chunk_type == 'table']
        assert len(table_chunks) > 0
        
        # Table should contain all quarters
        table_content = table_chunks[0].content
        assert 'Q1' in table_content
        assert 'Q2' in table_content
        assert 'Q3' in table_content
        assert 'Q4' in table_content
    
    def test_numerical_preservation(self, chunker, sample_document):
        """Test that numbers are preserved accurately."""
        chunks = chunker.chunk_document(sample_document, "doc_1")
        
        all_content = ' '.join(c.content for c in chunks)
        assert '$383.9 billion' in all_content or '383.9' in all_content
    
    def test_context_injection(self, chunker, sample_document):
        """Test that parent section headers are added to chunks."""
        chunks = chunker.chunk_document(sample_document, "doc_1")
        
        # Find a chunk from "Revenue" section
        revenue_chunks = [c for c in chunks if 'Revenue' in c.parent_section]
        if revenue_chunks:
            # Content should reference the section
            assert any('Revenue' in c.content for c in revenue_chunks)
```

### File: `backend/tests/unit/test_embeddings.py`

```python
import pytest
from src.rag.embeddings import EmbeddingService

class TestEmbeddingService:
    """Test embedding generation and caching."""
    
    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService(cache_backend='memory')
    
    @pytest.mark.asyncio
    async def test_single_embedding(self, embedding_service):
        """Test generating a single embedding."""
        text = "Apple revenue increased significantly."
        embedding = await embedding_service.embed_query(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 3072  # text-embedding-3-large dimension
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_batch_embedding(self, embedding_service):
        """Test batch embedding generation."""
        texts = [
            "Apple revenue increased",
            "Microsoft profit grew",
            "Tesla deliveries declined"
        ]
        
        embeddings = await embedding_service.embed_texts(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 3072 for emb in embeddings)
    
    @pytest.mark.asyncio
    async def test_caching(self, embedding_service):
        """Test that embeddings are cached."""
        text = "Test caching"
        
        # First call - cache miss
        emb1 = await embedding_service.embed_query(text)
        stats1 = await embedding_service.get_cache_stats()
        
        # Second call - cache hit
        emb2 = await embedding_service.embed_query(text)
        stats2 = await embedding_service.get_cache_stats()
        
        # Should return same embedding
        assert emb1 == emb2
        
        # Cache size should have grown
        assert stats2['memory_cache_size'] >= stats1['memory_cache_size']
    
    def test_cosine_similarity(self, embedding_service):
        """Test cosine similarity calculation."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]
        emb3 = [0.0, 1.0, 0.0]
        
        # Identical vectors
        sim1 = embedding_service.cosine_similarity(emb1, emb2)
        assert abs(sim1 - 1.0) < 0.001
        
        # Orthogonal vectors
        sim2 = embedding_service.cosine_similarity(emb1, emb3)
        assert abs(sim2 - 0.0) < 0.001
```

### File: `backend/tests/unit/test_retrieval.py`

```python
import pytest
from src.rag.retrieval import HybridRetriever
from unittest.mock import Mock, AsyncMock

class TestHybridRetriever:
    """Test hybrid retrieval system."""
    
    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.fetch = AsyncMock(return_value=[
            {
                'id': 'chunk_1',
                'content': 'Apple revenue was $383.9 billion',
                'similarity': 0.95,
                'metadata': {'document': 'apple_10k'}
            }
        ])
        return db
    
    @pytest.fixture
    def mock_embeddings(self):
        emb = Mock()
        emb.embed_query = AsyncMock(return_value=[0.1] * 3072)
        return emb
    
    @pytest.fixture
    def retriever(self, mock_db, mock_embeddings):
        return HybridRetriever(mock_db, mock_embeddings)
    
    @pytest.mark.asyncio
    async def test_vector_search(self, retriever):
        """Test vector similarity search."""
        results = await retriever._vector_search("test query", k=5, filters=None)
        
        assert len(results) > 0
        assert all(hasattr(r, 'chunk_id') for r in results)
        assert all(hasattr(r, 'score') for r in results)
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self, retriever):
        """Test hybrid retrieval combining vector and keyword."""
        results = await retriever.retrieve(
            query="What is Apple's revenue?",
            top_k=5,
            retrieval_strategy='hybrid'
        )
        
        assert len(results) > 0
        # Check that results have hybrid retrieval method
        assert any(r.retrieval_method == 'hybrid' for r in results)
    
    def test_rrf_fusion(self, retriever):
        """Test Reciprocal Rank Fusion algorithm."""
        from src.rag.retrieval import RetrievalResult
        
        list1 = [
            RetrievalResult('doc1', 'content1', 0.9, {}, 'vector'),
            RetrievalResult('doc2', 'content2', 0.8, {}, 'vector'),
        ]
        
        list2 = [
            RetrievalResult('doc2', 'content2', 0.95, {}, 'keyword'),
            RetrievalResult('doc3', 'content3', 0.85, {}, 'keyword'),
        ]
        
        fused = retriever._reciprocal_rank_fusion(list1, list2, k=60)
        
        # doc2 appears in both, should be ranked higher
        assert fused[0].chunk_id == 'doc2'
        assert fused[0].retrieval_method == 'hybrid'
```

---

## 2. Integration Tests

### File: `backend/tests/integration/test_rag_pipeline.py`

```python
import pytest
from src.rag.pipeline import RAGPipeline
from src.db.supabase import get_supabase_client
from src.llm.provider import LLMProvider

@pytest.mark.integration
class TestRAGPipeline:
    """Integration tests for complete RAG pipeline."""
    
    @pytest.fixture
    async def setup_test_document(self, db_client):
        """Setup a test document in the database."""
        # Insert test document
        doc_id = "test_doc_001"
        text = "Apple Inc. reported revenue of $383.9 billion in fiscal 2023."
        
        # This would actually process and store the document
        # For testing, we'll use mock data
        yield doc_id
        
        # Cleanup
        await db_client.table('documents').delete().eq('id', doc_id).execute()
    
    @pytest.mark.asyncio
    async def test_document_processing(self, rag_pipeline, setup_test_document):
        """Test end-to-end document processing."""
        doc_id = setup_test_document
        text = "Sample financial document..."
        
        result = await rag_pipeline.process_document(
            document_id=doc_id,
            text=text,
            metadata={'type': '10-K'}
        )
        
        assert result['success'] is True
        assert result['chunks_created'] > 0
        assert result['processing_time'] > 0
    
    @pytest.mark.asyncio
    async def test_query_pipeline(self, rag_pipeline, setup_test_document):
        """Test complete query pipeline."""
        result = await rag_pipeline.query(
            query="What was Apple's revenue?",
            top_k=5
        )
        
        assert result.answer
        assert len(result.sources) > 0
        assert result.metadata['processing_time'] > 0
        
        # Check citations
        assert '[doc_' in result.answer  # Should have citations
    
    @pytest.mark.asyncio
    async def test_query_with_filters(self, rag_pipeline):
        """Test query with metadata filters."""
        result = await rag_pipeline.query(
            query="Revenue",
            filters={'document_type': '10-K'}
        )
        
        # All sources should match filter
        assert all(
            s['metadata'].get('document_type') == '10-K'
            for s in result.sources
        )
```

### File: `backend/tests/integration/test_agents.py`

```python
import pytest
from src.agents.graph import ResearchAgentGraph

@pytest.mark.integration
class TestAgentSystem:
    """Integration tests for multi-agent system."""
    
    @pytest.mark.asyncio
    async def test_supervisor_routing(self, agent_graph):
        """Test that supervisor routes queries correctly."""
        
        # Simple factual question
        result = await agent_graph.arun("What is the revenue?")
        
        # Should route to research agent
        agent_names = [step['agent'] for step in result['agent_trace']]
        assert 'supervisor' in agent_names
        assert 'research' in agent_names
    
    @pytest.mark.asyncio
    async def test_comparative_analysis(self, agent_graph):
        """Test comparative analysis routing."""
        
        result = await agent_graph.arun(
            "Compare Apple and Microsoft's R&D spending"
        )
        
        # Should route to analysis agent
        agent_names = [step['agent'] for step in result['agent_trace']]
        assert 'analysis' in agent_names
    
    @pytest.mark.asyncio
    async def test_fact_checking(self, agent_graph):
        """Test that fact checker validates claims."""
        
        result = await agent_graph.arun("What is the revenue?")
        
        # Should include fact checking
        agent_names = [step['agent'] for step in result['agent_trace']]
        assert 'fact_checker' in agent_names
        
        # Should have fact check results
        assert 'fact_check_results' in result
```

---

## 3. End-to-End Tests

### File: `frontend/e2e/test_user_flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Complete User Flow', () => {
  test('upload document and query', async ({ page }) => {
    // Navigate to app
    await page.goto('http://localhost:3000');
    
    // Enter API key
    await page.fill('[placeholder="Enter API key"]', 'test_key');
    await page.click('button:has-text("Submit")');
    
    // Upload document
    await page.click('text=Documents');
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/sample.pdf');
    
    // Wait for processing
    await page.waitForSelector('text=Processing complete', { timeout: 60000 });
    
    // Start new chat
    await page.click('text=Chat');
    await page.click('button:has-text("New Chat")');
    
    // Send query
    await page.fill('textarea', 'What is this document about?');
    await page.click('button:has-text("Send")');
    
    // Wait for response
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 30000 });
    
    // Verify response
    const response = await page.textContent('[data-testid="assistant-message"]');
    expect(response).toBeTruthy();
    expect(response.length).toBeGreaterThan(50);
    
    // Verify sources shown
    await expect(page.locator('text=Source 1')).toBeVisible();
  });
  
  test('view agent trace', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // ... setup and query ...
    
    // Expand agent trace
    await page.click('summary:has-text("View agent execution")');
    
    // Verify trace visible
    await expect(page.locator('text=supervisor')).toBeVisible();
    await expect(page.locator('text=research')).toBeVisible();
  });
  
  test('view metrics dashboard', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Navigate to metrics
    await page.click('text=Metrics');
    
    // Verify dashboard loads
    await expect(page.locator('text=Evaluation Metrics')).toBeVisible();
    await expect(page.locator('text=Overall Pass Rate')).toBeVisible();
    
    // Verify charts render
    await expect(page.locator('.recharts-wrapper')).toBeVisible();
  });
});
```

---

## 4. Evaluation Tests

### File: `backend/tests/evals/test_ragas.py`

```python
import pytest
from src.evaluation.ragas_eval import RAGASEvaluator

@pytest.mark.eval
class TestRAGASEvaluation:
    """Test RAGAS evaluation metrics."""
    
    @pytest.fixture
    def test_cases(self):
        return [
            {
                'question': 'What was Apple\'s revenue in 2023?',
                'ground_truth': 'Apple\'s revenue in fiscal 2023 was $383.9 billion.',
                'document_ids': ['apple_10k_2023']
            },
            {
                'question': 'What was Microsoft\'s R&D spending?',
                'ground_truth': 'Microsoft spent $27.2 billion on R&D in 2023.',
                'document_ids': ['msft_10k_2023']
            }
        ]
    
    @pytest.mark.asyncio
    async def test_evaluate_test_set(self, ragas_evaluator, test_cases):
        """Test evaluation on test set."""
        results = await ragas_evaluator.evaluate_test_set(test_cases)
        
        # Check overall scores
        assert 'faithfulness' in results['overall_scores']
        assert 'answer_relevancy' in results['overall_scores']
        
        # Scores should be between 0 and 1
        for metric, score in results['overall_scores'].items():
            assert 0 <= score <= 1
        
        # Check per-question results
        assert len(results['per_question_results']) == len(test_cases)
    
    @pytest.mark.asyncio
    async def test_faithfulness_score(self, ragas_evaluator):
        """Test faithfulness metric specifically."""
        question = "What is the revenue?"
        answer = "The revenue is $383.9 billion according to the document."
        contexts = ["Apple's revenue in 2023 was $383.9 billion."]
        ground_truth = "$383.9 billion"
        
        result = await ragas_evaluator.evaluate_single_query(
            question, answer, contexts, ground_truth
        )
        
        # Faithful answer should score high
        assert result['faithfulness'] > 0.8
```

### File: `backend/tests/evals/test_custom_metrics.py`

```python
import pytest
from src.evaluation.custom_metrics import FinancialMetrics

class TestCustomMetrics:
    """Test custom financial metrics."""
    
    @pytest.fixture
    def metrics(self):
        return FinancialMetrics()
    
    def test_numerical_accuracy(self, metrics):
        """Test numerical accuracy metric."""
        generated = "The revenue was $383.9 billion in 2023."
        ground_truth = "Revenue: $383.9 billion"
        
        result = metrics.numerical_accuracy(generated, ground_truth)
        
        assert result['score'] > 0.95  # Should be very accurate
        assert result['correct_numbers'] > 0
    
    def test_citation_quality(self, metrics):
        """Test citation quality metric."""
        answer_with_citations = "Revenue increased [doc_1]. Profit grew [doc_2]."
        answer_without = "Revenue increased. Profit grew."
        
        result1 = metrics.citation_quality(answer_with_citations)
        result2 = metrics.citation_quality(answer_without)
        
        assert result1['has_citations'] is True
        assert result2['has_citations'] is False
        assert result1['score'] > result2['score']
    
    def test_temporal_accuracy(self, metrics):
        """Test temporal accuracy metric."""
        generated = "In 2023, revenue was high. Q3 2024 was strong."
        ground_truth = "2023 fiscal year. Q3 2024 quarter."
        
        result = metrics.temporal_accuracy(generated, ground_truth)
        
        assert result['dates_matched'] >= 2
        assert result['score'] > 0.5
```

---

## 5. Performance Tests

### File: `backend/tests/performance/test_load.py`

```python
from locust import HttpUser, task, between

class InvestmentResearchUser(HttpUser):
    """Simulate user load on the system."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login/setup before tasks."""
        self.client.headers = {'X-API-Key': 'test_key'}
    
    @task(3)
    def query_document(self):
        """Most common task - query documents."""
        self.client.post("/api/chat", json={
            "query": "What is the revenue?",
            "conversation_id": "test_conv"
        })
    
    @task(1)
    def upload_document(self):
        """Less common - upload document."""
        files = {'file': ('test.pdf', b'fake pdf content', 'application/pdf')}
        self.client.post("/api/documents/upload", files=files)
    
    @task(1)
    def get_metrics(self):
        """Check metrics."""
        self.client.get("/api/evals/metrics")

# Run with: locust -f test_load.py --host=https://your-app.modal.run
```

### File: `backend/tests/performance/test_latency.py`

```python
import pytest
import time
from src.rag.pipeline import RAGPipeline

@pytest.mark.performance
class TestLatency:
    """Test response latency."""
    
    @pytest.mark.asyncio
    async def test_query_latency(self, rag_pipeline):
        """Test that queries complete in acceptable time."""
        start = time.time()
        
        result = await rag_pipeline.query("What is the revenue?")
        
        latency = time.time() - start
        
        # Should complete within 5 seconds (p95)
        assert latency < 5.0
        
        # Typically should be faster
        assert latency < 3.0  # p50 target
    
    @pytest.mark.asyncio
    async def test_retrieval_latency(self, retriever):
        """Test retrieval speed."""
        start = time.time()
        
        results = await retriever.retrieve("test query", top_k=10)
        
        latency = time.time() - start
        
        # Retrieval should be fast (<1 second)
        assert latency < 1.0
```

---

## 6. Test Fixtures & Mocks

### File: `backend/tests/conftest.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.db.supabase import get_supabase_client
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = Mock()
    client.fetch = AsyncMock(return_value=[])
    client.table = Mock(return_value=client)
    client.select = Mock(return_value=client)
    client.insert = Mock(return_value=client)
    client.execute = AsyncMock(return_value=Mock(data=[]))
    return client

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    provider = Mock()
    provider.generate = AsyncMock(return_value="Mock response")
    provider.structured_output = AsyncMock(return_value={'result': 'mock'})
    return provider

@pytest.fixture
def rag_pipeline(mock_supabase_client, mock_llm_provider):
    """Create RAG pipeline with mocked dependencies."""
    return RAGPipeline(
        mock_supabase_client,
        mock_llm_provider
    )

@pytest.fixture(scope="session")
def test_document():
    """Sample test document."""
    return {
        'id': 'test_doc_001',
        'content': """
        Apple Inc. Financial Results
        
        Fiscal Year 2023
        Revenue: $383.9 billion
        Net Income: $97.0 billion
        R&D Expenses: $29.9 billion
        """,
        'metadata': {
            'company': 'Apple',
            'type': '10-K',
            'year': 2023
        }
    }
```

---

## 7. Running Tests

### Run All Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_chunking.py

# Run specific test
pytest tests/unit/test_chunking.py::TestFinancialDocumentChunker::test_chunk_creation

# Run tests matching pattern
pytest -k "test_chunk"
```

### Run by Marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only evaluation tests
pytest -m eval

# Run only fast tests (exclude slow)
pytest -m "not slow"
```

### Run with Verbosity
```bash
# Verbose output
pytest -v

# Very verbose (show print statements)
pytest -vv -s

# Show slowest tests
pytest --durations=10
```

---

## 8. Test Coverage Goals

**Target Coverage**:
- Unit tests: 80%+ coverage
- Critical paths: 95%+ coverage
- Integration tests: Cover all major workflows
- E2E tests: Cover all user journeys

**Check Coverage**:
```bash
pytest --cov=src --cov-report=term-missing

# View HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 9. Continuous Testing

### Pre-commit Hook

`.git/hooks/pre-commit`:
```bash
#!/bin/bash

# Run linting
ruff check src/

# Run type checking
mypy src/

# Run fast unit tests
pytest tests/unit/ -v

# If any fail, prevent commit
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### GitHub Actions

Already covered in deployment-guide.md - runs on every push.

---

## 10. Testing Checklist

**Before Each Commit**:
- [ ] All unit tests pass
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] No new warnings

**Before Each Deploy**:
- [ ] All tests pass (unit + integration)
- [ ] E2E tests pass
- [ ] Evaluation metrics stable
- [ ] Performance tests pass
- [ ] No errors in logs

**Weekly**:
- [ ] Run full evaluation suite
- [ ] Review test coverage
- [ ] Update golden dataset if needed
- [ ] Check for flaky tests

---

## Summary

This testing strategy provides:

✅ **Unit Tests**: Every component tested in isolation
✅ **Integration Tests**: Components working together
✅ **E2E Tests**: Full user flows automated
✅ **Evaluation Tests**: AI quality validated
✅ **Performance Tests**: Latency and load tested
✅ **Mocks & Fixtures**: Easy test setup
✅ **CI/CD Integration**: Automated on every commit
✅ **Coverage Tracking**: Know what's tested

**Testing is crucial for demonstrating quality in interviews!**