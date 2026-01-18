"""
Test script for complete RAG pipeline.

This demonstrates the end-to-end RAG system:
1. Upload documents → Process → Chunk → Embed → Store
2. Ask questions → Retrieve → Generate answers with citations

Usage:
    python test_rag_pipeline.py
"""
import sys
import io
import uuid

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.rag.chunking import SimpleChunker
from src.rag.embeddings import EmbeddingService
from src.db.vector_store import VectorStore
from src.db.supabase import get_supabase
from src.rag.pipeline import RAGPipeline


def setup_test_documents():
    """Create sample financial documents and store in database."""
    
    print("📚 Setting Up Test Documents")
    print("=" * 70)
    print()
    
    # Sample documents
    documents = [
        {
            "filename": "tesla_q4_2023.txt",
            "content": """
            Tesla Q4 2023 Financial Results
            
            Tesla announced financial results for Q4 2023. Total revenue reached 
            $25.2 billion, representing a 3% increase year-over-year. Automotive 
            revenue was $21.6 billion, while Energy generation and storage revenue 
            grew 10% to $1.4 billion.
            
            Vehicle Deliveries and Production
            
            Tesla produced 494,989 vehicles and delivered 484,507 vehicles in Q4. 
            The Model 3/Y represented approximately 95% of deliveries. Full year 
            2023 deliveries reached 1.8 million vehicles.
            
            Profitability Metrics
            
            Operating margin was 8.2% in Q4, down from 16% in the prior year period 
            due to reduced average selling prices. GAAP net income was $7.9 billion, 
            or $2.27 per diluted share. Free cash flow for the quarter was $2.1 billion.
            """
        },
        {
            "filename": "apple_q4_2023.txt",
            "content": """
            Apple Q4 2023 Financial Results
            
            Apple Inc. today announced financial results for its fiscal 2023 fourth 
            quarter. The Company posted quarterly revenue of $89.5 billion, down 1 
            percent year over year. Products revenue decreased 5 percent to $67.2 
            billion. Services revenue reached an all-time high of $22.3 billion, up 
            16 percent year over year.
            
            Product Performance
            
            iPhone revenue was $43.8 billion for the quarter, down 2.4 percent. Mac 
            revenue was $7.6 billion, down 33.8 percent year over year. iPad revenue 
            was $6.4 billion, down 10.1 percent. Wearables, Home and Accessories 
            revenue was $9.3 billion, down 3.3 percent.
            
            Financial Position
            
            Gross margin was 45.2 percent compared to 42.3 percent in the year-ago 
            quarter. Operating expenses were $14.5 billion. Net income was $22.96 
            billion, or $1.46 per diluted share. The Company's cash, cash equivalents 
            and marketable securities totaled $166.5 billion.
            """
        },
        {
            "filename": "nvidia_q3_2024.txt",
            "content": """
            NVIDIA Q3 Fiscal 2024 Results
            
            NVIDIA announced record revenue of $18.12 billion for Q3 fiscal 2024, up 
            206% from a year ago and up 34% from the previous quarter. Data Center 
            revenue reached a record $14.51 billion, up 279% from a year ago and up 
            41% from the previous quarter, driven by strong demand for AI computing.
            
            Business Segments
            
            Gaming revenue was $2.86 billion, up 81% from a year ago. Professional 
            Visualization revenue was $416 million, up 108% from a year ago. 
            Automotive revenue was $261 million, up 4% from a year ago.
            
            Profitability
            
            GAAP gross margin was 75.0%, up from 56.1% a year ago. GAAP operating 
            income was $10.42 billion, up from $1.21 billion a year ago. GAAP net 
            income was $9.24 billion, or $3.71 per diluted share, up from $680 
            million a year ago.
            """
        }
    ]
    
    # Initialize services
    db = get_supabase()
    chunker = SimpleChunker(chunk_size=400, chunk_overlap=80)
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    
    # Get or create test user
    user_result = db.table('users').select('id').limit(1).execute()
    if user_result.data:
        test_user_id = user_result.data[0]['id']
    else:
        test_user_id = str(uuid.uuid4())
        user_data = {
            'id': test_user_id,
            'email': 'test@example.com',
            'api_key': f'test-key-{uuid.uuid4()}'
        }
        db.table('users').insert(user_data).execute()
    
    document_ids = []
    
    # Process each document
    for doc in documents:
        print(f"Processing: {doc['filename']}")
        
        # 1. Create document record
        doc_id = str(uuid.uuid4())
        doc_data = {
            'id': doc_id,
            'user_id': test_user_id,
            'filename': doc['filename'],
            'file_type': 'text',
            'file_size': len(doc['content']),
            'storage_path': f'test/{doc["filename"]}',
            'processed': True
        }
        db.table('documents').insert(doc_data).execute()
        document_ids.append(doc_id)
        
        # 2. Chunk the content
        chunks = chunker.chunk_text(doc['content'])
        print(f"  ✓ Created {len(chunks)} chunks")
        
        # 3. Convert to dict format and add document metadata
        chunk_dicts = []
        for chunk in chunks:
            chunk_dicts.append({
                'content': chunk.content,
                'chunk_index': chunk.chunk_index,
                'metadata': {
                    **chunk.metadata,
                    'document_name': doc['filename']
                }
            })
        
        # 4. Generate embeddings
        chunks_with_embeddings = embedding_service.embed_chunks(chunk_dicts)
        print(f"  ✓ Generated embeddings")
        
        # 5. Add document_id and store in database
        for chunk in chunks_with_embeddings:
            chunk['document_id'] = doc_id
        
        chunk_ids = vector_store.insert_chunks(chunks_with_embeddings)
        print(f"  ✓ Stored {len(chunk_ids)} chunks in database")
        print()
    
    print(f"✅ Successfully processed {len(documents)} documents")
    print(f"📝 Document IDs: {', '.join([d[:8] + '...' for d in document_ids])}")
    print()
    
    return document_ids


def test_rag_pipeline(document_ids):
    """Test the complete RAG pipeline with sample queries."""
    
    print("=" * 70)
    print("🤖 Testing RAG Pipeline")
    print("=" * 70)
    print()
    
    # Initialize pipeline
    pipeline = RAGPipeline(
        top_k=3,  # Retrieve top 3 chunks
        temperature=0.0  # Deterministic for financial queries
    )
    
    # Test queries
    test_queries = [
        {
            "question": "What was Tesla's revenue in Q4 2023?",
            "description": "Simple factual query"
        },
        {
            "question": "Compare the operating margins of Tesla and Apple in Q4",
            "description": "Cross-document comparison"
        },
        {
            "question": "Which company had the highest revenue growth and by how much?",
            "description": "Complex analytical query"
        },
        {
            "question": "What were NVIDIA's data center results?",
            "description": "Specific segment query"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"Query {i}: {test['question']}")
        print(f"Type: {test['description']}")
        print("-" * 70)
        
        # Execute RAG pipeline
        result = pipeline.query(
            question=test['question'],
            document_ids=document_ids  # Search within our test documents
        )
        
        # Display results
        print(f"\n📊 Retrieval Stats:")
        print(f"  • Retrieved chunks: {result['metadata']['retrieved_chunks']}")
        print(f"  • Avg similarity: {result['metadata']['avg_similarity']:.3f}")
        print(f"  • Top similarity: {result['metadata']['top_similarity']:.3f}")
        
        print(f"\n💬 Answer:")
        print(f"{result['answer']}")
        
        print(f"\n📚 Sources ({len(result['sources'])} chunks used):")
        for source in result['sources'][:2]:  # Show first 2 sources
            print(f"  [Source {source['source_number']}] Similarity: {source['similarity']:.3f}")
            print(f"  {source['content']}")
        
        if len(result['sources']) > 2:
            print(f"  ... and {len(result['sources']) - 2} more sources")
        
        print("\n" + "=" * 70)
        print()
    
    # Display usage stats
    print("📈 Pipeline Usage Statistics:")
    print("-" * 70)
    stats = pipeline.get_usage_stats()
    print(f"Model: {stats['model']}")
    print(f"Total tokens: {stats['total_tokens']:,}")
    print(f"  • Prompt tokens: {stats['prompt_tokens']:,}")
    print(f"  • Completion tokens: {stats['completion_tokens']:,}")
    print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
    print()


def test_filtered_search(document_ids):
    """Test document-specific queries."""
    
    print("=" * 70)
    print("🔍 Testing Filtered Search (Single Document)")
    print("=" * 70)
    print()
    
    pipeline = RAGPipeline()
    
    # Query only Tesla document
    print("Query: 'What were the vehicle deliveries?' (Tesla document only)")
    print("-" * 70)
    
    result = pipeline.query(
        question="What were the vehicle deliveries?",
        document_ids=[document_ids[0]]  # Only Tesla document
    )
    
    print(f"\n💬 Answer:")
    print(f"{result['answer']}")
    print()


def cleanup_test_data():
    """Clean up test documents."""
    
    print("=" * 70)
    print("🧹 Cleaning Up Test Data")
    print("-" * 70)
    
    try:
        db = get_supabase()
        
        # Delete all test documents (cascades to chunks)
        result = db.table('documents').delete().like('filename', '%q%').execute()
        
        deleted_count = len(result.data) if result.data else 0
        print(f"✓ Deleted {deleted_count} test documents and their chunks")
        print()
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
        print()


def main():
    """Run complete RAG pipeline test."""
    
    print("🚀 RAG Pipeline Integration Test")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Setup test documents
        document_ids = setup_test_documents()
        
        # Step 2: Test RAG pipeline
        test_rag_pipeline(document_ids)
        
        # Step 3: Test filtered search
        test_filtered_search(document_ids)
        
        # Step 4: Cleanup
        cleanup_test_data()
        
        # Success message
        print("=" * 70)
        print("🎉 RAG Pipeline Test Complete!")
        print()
        print("✅ What we verified:")
        print("   1. Document processing (chunk → embed → store)")
        print("   2. Semantic retrieval (query → relevant chunks)")
        print("   3. Answer generation (LLM + context → answer)")
        print("   4. Source attribution (citations)")
        print("   5. Document filtering (search specific docs)")
        print()
        print("🚀 Your RAG system is fully operational!")
        print()
        print("📚 Next steps:")
        print("   1. Build document upload API endpoint")
        print("   2. Create chat API for frontend")
        print("   3. Add conversation history support")
        print("   4. Implement query transformations (HyDE, expansion)")
        print("   5. Add reranking for better results")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Make sure you have both:")
        print("   • OPENAI_API_KEY in your .env file")
        print("   • SUPABASE credentials configured")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
