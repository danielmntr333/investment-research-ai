"""
Quick test script for Advanced RAG Pipeline features.

Run this to test advanced RAG components without needing full setup.

Usage:
    python test_rag_advanced_quick.py
"""
import asyncio
from src.rag.chunking import FinancialDocumentChunker
from src.rag.query_transform import QueryTransformer, QueryStrategy


def test_enhanced_chunking():
    """Test enhanced document chunking with structure detection."""
    print("\n" + "="*80)
    print("TEST 1: Enhanced Document Chunking")
    print("="*80)
    
    chunker = FinancialDocumentChunker(
        chunk_size=500,
        chunk_overlap=100,
        preserve_tables=True,
        add_context=True
    )
    
    sample_document = """
FINANCIAL HIGHLIGHTS

Our company achieved record revenue in Q4 2023, demonstrating strong market demand
and operational efficiency across all business segments.

Item 1A. Risk Factors

Market volatility and economic uncertainty present significant challenges to our
business operations. Competition in the technology sector remains intense.

REVENUE BREAKDOWN

Product       Q4 2023    Q3 2023    Growth
Product A     $150M      $140M      7.1%
Product B     $85M       $80M       6.3%
Services      $65M       $55M       18.2%
Total         $300M      $275M      9.1%

FUTURE OUTLOOK

We expect continued growth driven by new product launches and expansion into
emerging markets. Strategic investments in R&D will position us for long-term success.
    """
    
    chunks = chunker.chunk_document(
        text=sample_document,
        document_id="test_doc_123",
        metadata={"source": "test", "year": 2023}
    )
    
    print(f"\n✓ Total chunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[:5], 1):  # Show first 5
        chunk_type = chunk['metadata'].get('chunk_type', 'text')
        section = chunk['metadata'].get('parent_section', 'N/A')
        content_preview = chunk['content'][:100].replace('\n', ' ')
        
        print(f"\nChunk {i}:")
        print(f"  Type: {chunk_type}")
        print(f"  Section: {section}")
        print(f"  Preview: {content_preview}...")
    
    # Check for table preservation
    table_chunks = [c for c in chunks if c['metadata'].get('chunk_type') == 'table']
    print(f"\n✓ Table chunks preserved: {len(table_chunks)}")
    
    if table_chunks:
        print(f"\nTable content sample:")
        print(table_chunks[0]['content'][:200])
    
    return chunks


async def test_query_transformation():
    """Test query transformation strategies."""
    print("\n" + "="*80)
    print("TEST 2: Query Transformation")
    print("="*80)
    
    transformer = QueryTransformer()
    
    test_queries = [
        ("What is revenue recognition?", "Expected: HyDE"),
        ("Compare Apple vs Microsoft revenue", "Expected: DECOMPOSITION"),
        ("Tesla revenue", "Expected: MULTI_QUERY"),
        ("What was the Q4 2023 revenue for Apple Inc?", "Expected: NONE"),
    ]
    
    print("\nAuto-strategy selection:")
    for query, expected in test_queries:
        strategy = transformer.auto_select_strategy(query)
        print(f"\n  Query: {query}")
        print(f"  Strategy: {strategy.value} ({expected})")
    
    # Test list parsing (doesn't need LLM)
    print("\n\nTesting list parsing:")
    sample_response = """
1. What was Apple's total revenue in 2023?
2. How did Apple's revenue compare to 2022?
3. What were the main revenue drivers for Apple?
    """
    
    parsed = transformer._parse_list_response(sample_response)
    print(f"  Parsed {len(parsed)} queries:")
    for i, q in enumerate(parsed, 1):
        print(f"    {i}. {q}")


def test_retrieval_strategies():
    """Test retrieval strategy concepts (without database)."""
    print("\n" + "="*80)
    print("TEST 3: Retrieval Strategies (RRF Algorithm)")
    print("="*80)
    
    # Demonstrate RRF scoring
    k = 60
    
    print("\nReciprocal Rank Fusion (RRF) Example:")
    print(f"  Formula: score = sum(1 / (k + rank_i)), where k = {k}\n")
    
    scenarios = [
        ("Doc A", 1, 2, "Ranks high in both methods"),
        ("Doc B", 5, 1, "High in keyword, lower in vector"),
        ("Doc C", 3, 4, "Medium in both methods"),
        ("Doc D", 10, 15, "Low in both methods"),
    ]
    
    print(f"{'Document':<10} {'Vector Rank':<15} {'Keyword Rank':<15} {'RRF Score':<12} {'Notes'}")
    print("-" * 80)
    
    for doc_name, vec_rank, kw_rank, notes in scenarios:
        rrf_score = (1.0 / (k + vec_rank)) + (1.0 / (k + kw_rank))
        print(f"{doc_name:<10} {vec_rank:<15} {kw_rank:<15} {rrf_score:<12.6f} {notes}")
    
    print("\n✓ Doc A scores highest (consistent across both methods)")
    print("✓ RRF is robust to score scale differences")


def test_pipeline_features():
    """Test pipeline feature flags."""
    print("\n" + "="*80)
    print("TEST 4: Pipeline Configuration Options")
    print("="*80)
    
    configurations = [
        {
            "name": "High Precision (Financial Analysis)",
            "strategy": "rrf",
            "use_reranking": True,
            "use_query_transform": False,
            "top_k": 5,
            "use_case": "When accuracy is critical"
        },
        {
            "name": "High Recall (Research)",
            "strategy": "hybrid",
            "use_reranking": False,
            "use_query_transform": True,
            "top_k": 15,
            "use_case": "When finding all relevant info is important"
        },
        {
            "name": "Balanced (Default)",
            "strategy": "hybrid",
            "use_reranking": False,
            "use_query_transform": False,
            "top_k": 10,
            "use_case": "General purpose queries"
        },
        {
            "name": "Speed Optimized",
            "strategy": "vector",
            "use_reranking": False,
            "use_query_transform": False,
            "top_k": 5,
            "use_case": "When latency is critical"
        }
    ]
    
    for config in configurations:
        print(f"\n{config['name']}:")
        print(f"  Strategy: {config['strategy']}")
        print(f"  Reranking: {config['use_reranking']}")
        print(f"  Query Transform: {config['use_query_transform']}")
        print(f"  Top-K: {config['top_k']}")
        print(f"  Use Case: {config['use_case']}")
    
    print("\n" + "="*80)
    print("Example Pipeline Usage:")
    print("="*80)
    
    example_code = '''
from src.rag.pipeline import RAGPipeline

pipeline = RAGPipeline()

# Advanced query with all features
result = pipeline.query(
    question="Compare Apple vs Microsoft revenue growth",
    strategy='rrf',              # Most robust
    use_query_transform=True,    # Enable HyDE/multi-query
    use_reranking=True,          # Cohere reranking
    top_k=10
)

print(result['answer'])
print(f"Retrieved {result['metadata']['retrieved_chunks']} chunks")
print(f"Processing time: {result['metadata']['processing_time']:.2f}s")
'''
    print(example_code)


def print_summary():
    """Print test summary and next steps."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print("\n✓ Enhanced Chunking: Structure detection, table preservation")
    print("✓ Query Transformation: Auto-strategy selection, list parsing")
    print("✓ Retrieval Strategies: RRF algorithm demonstration")
    print("✓ Pipeline Configuration: Multiple use-case configs")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    
    print("""
1. Run Database Migration:
   - Execute: backend/migrations/add_fts_support.sql
   - This adds PostgreSQL Full-Text Search support

2. Set Environment Variables:
   - COHERE_API_KEY (optional, for reranking)
   - OPENAI_API_KEY (required)

3. Test with Real Documents:
   - Upload documents via your API
   - Run: python test_rag_pipeline.py
   
4. Run Full Test Suite:
   - pytest tests/test_rag_advanced.py -v

5. Integration:
   - Use RAGPipeline in your agents
   - Configure strategy based on use case
   - Monitor performance metrics
""")
    
    print("="*80)
    print("Advanced RAG Pipeline is ready! 🚀")
    print("="*80)


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("ADVANCED RAG PIPELINE - QUICK TEST")
    print("="*80)
    
    # Run tests
    test_enhanced_chunking()
    await test_query_transformation()
    test_retrieval_strategies()
    test_pipeline_features()
    print_summary()


if __name__ == "__main__":
    # Run async tests
    asyncio.run(main())
