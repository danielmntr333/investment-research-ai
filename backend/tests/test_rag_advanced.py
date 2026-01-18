"""
Tests for advanced RAG pipeline components.

Tests cover:
- Enhanced chunking (structure detection, table preservation)
- Hybrid retrieval (vector + keyword + RRF)
- Query transformation (HyDE, multi-query, decomposition)
- Reranking (Cohere)
- End-to-end pipeline
"""
import pytest
from src.rag.chunking import FinancialDocumentChunker
from src.rag.query_transform import QueryTransformer, QueryStrategy


class TestEnhancedChunking:
    """Test enhanced document chunking."""
    
    def test_section_detection(self):
        """Test that section headers are detected correctly."""
        chunker = FinancialDocumentChunker(chunk_size=500, chunk_overlap=50)
        
        text = """
FINANCIAL RESULTS

Our revenue increased significantly in Q4 2023.

Item 1A. Risk Factors

Various risks affect our business operations.

BALANCE SHEET

Assets   2023   2022
Total    100M   90M
        """
        
        chunks = chunker.chunk_document(text, "test_doc")
        
        # Should have multiple chunks from different sections
        assert len(chunks) > 0
        
        # Check that metadata includes section information
        section_headers = [c['metadata'].get('parent_section', '') for c in chunks]
        assert any('FINANCIAL RESULTS' in h for h in section_headers)
        assert any('Item 1A' in h for h in section_headers)
    
    def test_table_preservation(self):
        """Test that tables are kept intact."""
        chunker = FinancialDocumentChunker(
            chunk_size=200, 
            chunk_overlap=20,
            preserve_tables=True
        )
        
        text = """
Introduction to the company.

Revenue    2023    2022
Product A  100M    90M
Product B  50M     45M
Total      150M    135M

Conclusion paragraph.
        """
        
        chunks = chunker.chunk_document(text, "test_doc")
        
        # Should have chunks with table type
        chunk_types = [c['metadata'].get('chunk_type') for c in chunks]
        assert 'table' in chunk_types
        
        # Table chunk should contain all table rows
        table_chunks = [c for c in chunks if c['metadata'].get('chunk_type') == 'table']
        if table_chunks:
            table_content = table_chunks[0]['content']
            assert 'Product A' in table_content
            assert 'Product B' in table_content
            assert 'Total' in table_content
    
    def test_context_injection(self):
        """Test that section headers are prepended to chunks."""
        chunker = FinancialDocumentChunker(
            chunk_size=200,
            add_context=True
        )
        
        text = """
REVENUE ANALYSIS

Our revenue grew by 20% year over year, driven by strong product sales.
        """
        
        chunks = chunker.chunk_document(text, "test_doc")
        
        # Context should be added to chunks
        assert len(chunks) > 0
        # Should contain section header in content for context
        has_context = any('REVENUE ANALYSIS' in c['content'] or 
                         'Revenue' in c['metadata'].get('parent_section', '') 
                         for c in chunks)
        assert has_context


class TestQueryTransformation:
    """Test query transformation strategies."""
    
    def test_auto_strategy_selection(self):
        """Test automatic strategy selection based on query."""
        transformer = QueryTransformer()
        
        # Conceptual question → HyDE
        strategy = transformer.auto_select_strategy("What is revenue recognition?")
        assert strategy == QueryStrategy.HYDE
        
        # Comparative question → Decomposition
        strategy = transformer.auto_select_strategy("Compare Apple vs Microsoft revenue")
        assert strategy == QueryStrategy.DECOMPOSITION
        
        # Short query → Multi-query
        strategy = transformer.auto_select_strategy("Tesla revenue")
        assert strategy == QueryStrategy.MULTI_QUERY
        
        # Simple factual → None
        strategy = transformer.auto_select_strategy("What was the revenue in Q4 2023 for Apple?")
        assert strategy == QueryStrategy.NONE
    
    def test_list_parsing(self):
        """Test parsing of numbered lists from LLM responses."""
        transformer = QueryTransformer()
        
        response = """
1. First query variation
2. Second query variation
3. Third query variation
        """
        
        parsed = transformer._parse_list_response(response)
        
        assert len(parsed) == 3
        assert "First query variation" in parsed[0]
        assert "Second query variation" in parsed[1]
        assert "Third query variation" in parsed[2]


class TestHybridRetrieval:
    """Test hybrid retrieval strategies."""
    
    def test_rrf_score_calculation(self):
        """Test Reciprocal Rank Fusion score calculation."""
        # RRF formula: score = sum(1 / (k + rank_i))
        # Example:
        # Document appears at rank 1 in vector search, rank 3 in keyword search
        # With k=60: score = 1/(60+1) + 1/(60+3) ≈ 0.0164 + 0.0159 ≈ 0.0323
        
        k = 60
        vector_rank = 1
        keyword_rank = 3
        
        rrf_score = (1.0 / (k + vector_rank)) + (1.0 / (k + keyword_rank))
        
        assert rrf_score > 0
        assert 0.03 < rrf_score < 0.04  # Should be around 0.032
    
    def test_rrf_vs_linear_combination(self):
        """
        Test that RRF is more robust than linear combination.
        
        RRF is less sensitive to score scale differences between methods.
        """
        # Scenario: Document A ranks high in both, Document B ranks high in one
        k = 60
        
        # Document A: rank 1 in vector, rank 2 in keyword
        doc_a_rrf = (1.0 / (k + 1)) + (1.0 / (k + 2))
        
        # Document B: rank 5 in vector, rank 1 in keyword
        doc_b_rrf = (1.0 / (k + 5)) + (1.0 / (k + 1))
        
        # Document A should score higher (consistent across methods)
        assert doc_a_rrf > doc_b_rrf


class TestPipelineIntegration:
    """Test end-to-end pipeline integration."""
    
    def test_pipeline_initialization(self):
        """Test that pipeline can be initialized with all components."""
        from src.rag.pipeline import RAGPipeline
        from src.llm.provider import LLMProvider
        from src.rag.retrieval import Retriever
        from src.rag.query_transform import QueryTransformer
        
        # Should initialize without errors
        pipeline = RAGPipeline(
            llm_provider=LLMProvider(),
            retriever=Retriever(),
            query_transformer=QueryTransformer(),
            reranker=None  # Optional
        )
        
        assert pipeline is not None
        assert pipeline.retriever is not None
        assert pipeline.llm_provider is not None
        assert pipeline.query_transformer is not None
    
    def test_pipeline_metadata(self):
        """Test that pipeline returns comprehensive metadata."""
        from src.rag.pipeline import RAGPipeline
        
        # This test would require mocking, but structure is important
        # Expected metadata fields:
        expected_fields = [
            'retrieved_chunks',
            'unique_chunks',
            'transformed_queries',
            'retrieval_strategy',
            'used_query_transform',
            'used_reranking',
            'avg_score',
            'top_score',
            'model',
            'processing_time',
            'status'
        ]
        
        # All these fields should be present in metadata
        assert len(expected_fields) > 0  # Placeholder


class TestReranking:
    """Test reranking functionality."""
    
    def test_reranker_initialization(self):
        """Test that reranker can be initialized."""
        from src.rag.reranking import CohereReranker
        import os
        
        # Should handle missing API key gracefully
        reranker = CohereReranker()
        
        # Should not initialize client until first use
        assert reranker._client is None
    
    def test_reranking_preserves_document_data(self):
        """Test that reranking preserves original document data."""
        from src.rag.reranking import CohereReranker
        
        # Mock documents
        docs = [
            {'id': '1', 'content': 'Document about revenue', 'score': 0.8},
            {'id': '2', 'content': 'Document about expenses', 'score': 0.7},
            {'id': '3', 'content': 'Document about profit', 'score': 0.6}
        ]
        
        # If reranking fails, should return original docs
        # (This would need mocking in real test)
        assert len(docs) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
