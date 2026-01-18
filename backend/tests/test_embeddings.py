"""
Test script for embedding pipeline.

This demonstrates the complete RAG pipeline:
1. Document text → Chunking
2. Chunks → Embeddings (OpenAI)
3. Chunks + Embeddings → Supabase (pgvector)
4. Query → Similarity Search → Relevant chunks

Usage:
    python test_embeddings.py
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


def test_embedding_pipeline():
    """Test the complete embedding pipeline."""
    
    print("🧪 Testing Embedding Pipeline")
    print("=" * 70)
    print()
    
    # Sample financial document
    sample_text = """
    Tesla Q4 2023 Financial Results
    
    Tesla announced record financial results for Q4 2023. Total revenue reached 
    $25.2 billion, representing a 3% increase year-over-year. Automotive revenue 
    was $21.6 billion, while Energy generation and storage revenue grew 10% to 
    $1.4 billion.
    
    Vehicle Deliveries and Production
    
    Tesla produced 494,989 vehicles and delivered 484,507 vehicles in Q4. The 
    Model 3/Y represented approximately 95% of deliveries. Full year 2023 
    deliveries reached 1.8 million vehicles, achieving the company's stated goal.
    
    Profitability Metrics
    
    Operating margin was 8.2% in Q4, down from 16% in the prior year period due 
    to reduced average selling prices. GAAP net income was $7.9 billion, or $2.27 
    per diluted share. Free cash flow for the quarter was $2.1 billion.
    
    Future Outlook
    
    Tesla expects to grow vehicle volume in 2024, with production start of the 
    next-generation vehicle planned at Gigafactory Texas. Energy storage 
    deployments are expected to grow faster than vehicle business in 2024.
    """
    
    # Step 1: Chunking
    print("📝 STEP 1: Chunking Document")
    print("-" * 70)
    
    chunker = SimpleChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_text(sample_text)
    
    print(f"✓ Created {len(chunks)} chunks")
    print(f"✓ Chunk size: {chunker.chunk_size} chars")
    print(f"✓ Overlap: {chunker.chunk_overlap} chars")
    print()
    
    # Show first chunk
    if chunks:
        print(f"First chunk preview:")
        print(f"  Content: {chunks[0].content[:100]}...")
        print(f"  Length: {len(chunks[0].content)} chars")
        print()
    
    # Step 2: Generate embeddings
    print("🔮 STEP 2: Generating Embeddings")
    print("-" * 70)
    
    try:
        embedding_service = EmbeddingService()
        print(f"✓ Using model: {embedding_service.model}")
        print(f"✓ Dimensions: {embedding_service.dimension}")
        print()
        
        # Convert chunks to dict format
        chunk_dicts = []
        for chunk in chunks:
            chunk_dicts.append({
                'content': chunk.content,
                'chunk_index': chunk.chunk_index,
                'metadata': chunk.metadata
            })
        
        # Generate embeddings
        print("  Calling OpenAI API...")
        chunks_with_embeddings = embedding_service.embed_chunks(chunk_dicts)
        
        print(f"✓ Generated {len(chunks_with_embeddings)} embeddings")
        
        # Show embedding stats
        if chunks_with_embeddings and chunks_with_embeddings[0].get('embedding'):
            first_embedding = chunks_with_embeddings[0]['embedding']
            print(f"✓ Embedding dimensions: {len(first_embedding)}")
            print(f"✓ Sample values: [{first_embedding[0]:.4f}, {first_embedding[1]:.4f}, {first_embedding[2]:.4f}, ...]")
        print()
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Next steps:")
        print("   1. Add OPENAI_API_KEY to your .env file")
        print("   2. Get API key from: https://platform.openai.com/api-keys")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 3: Store in vector database
    print("💾 STEP 3: Storing in Vector Database")
    print("-" * 70)
    
    try:
        # Create a test document entry first
        db = get_supabase()
        
        # Create test document
        test_doc_id = str(uuid.uuid4())
        test_user_id = str(uuid.uuid4())
        
        # Check if test user exists, create if not
        user_result = db.table('users').select('id').limit(1).execute()
        if user_result.data:
            test_user_id = user_result.data[0]['id']
        else:
            user_data = {
                'id': test_user_id,
                'email': 'test@example.com',
                'api_key': f'test-key-{uuid.uuid4()}'
            }
            db.table('users').insert(user_data).execute()
            print("✓ Created test user")
        
        # Create test document
        doc_data = {
            'id': test_doc_id,
            'user_id': test_user_id,
            'filename': 'tesla_q4_2023.txt',
            'file_type': 'text',
            'file_size': len(sample_text),
            'storage_path': 'test/tesla_q4_2023.txt',
            'processed': True
        }
        db.table('documents').insert(doc_data).execute()
        print(f"✓ Created test document: {test_doc_id}")
        
        # Prepare chunks for insertion
        for chunk in chunks_with_embeddings:
            chunk['document_id'] = test_doc_id
        
        # Insert chunks with embeddings
        vector_store = VectorStore()
        chunk_ids = vector_store.insert_chunks(chunks_with_embeddings)
        
        print(f"✓ Stored {len(chunk_ids)} chunks in database")
        print(f"✓ Chunk IDs: {chunk_ids[0][:8]}..., {chunk_ids[-1][:8]}...")
        print()
        
    except Exception as e:
        print(f"❌ Storage Error: {e}")
        print("\n💡 Make sure:")
        print("   1. Supabase is configured correctly")
        print("   2. You ran setup_supabase.sql")
        return
    
    # Step 4: Test similarity search
    print("🔍 STEP 4: Testing Similarity Search")
    print("-" * 70)
    
    try:
        # Test query
        test_query = "What was Tesla's revenue in Q4?"
        print(f"Query: \"{test_query}\"")
        print()
        
        # Generate query embedding
        query_embedding = embedding_service.embed_query(test_query)
        print(f"✓ Generated query embedding ({len(query_embedding)} dims)")
        
        # Search for similar chunks
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=3,
            document_ids=[test_doc_id]
        )
        
        print(f"✓ Found {len(results)} similar chunks")
        print()
        
        # Display results
        print("📊 Top Results:")
        print("-" * 70)
        
        for i, result in enumerate(results):
            print(f"\n[Result {i+1}] Similarity: {result['similarity']:.4f}")
            print(f"Content: {result['content'][:150]}...")
            if result['similarity'] > 0.8:
                print("  → Highly relevant! ✨")
            elif result['similarity'] > 0.7:
                print("  → Relevant ✓")
        
        print()
        
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return
    
    # Cleanup
    print("=" * 70)
    print("🧹 Cleaning Up")
    print("-" * 70)
    
    try:
        # Delete test document (cascades to chunks)
        db.table('documents').delete().eq('id', test_doc_id).execute()
        print("✓ Deleted test document and chunks")
        print()
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
        print()
    
    # Success summary
    print("=" * 70)
    print("🎉 Embedding Pipeline Test Complete!")
    print()
    print("✅ What we verified:")
    print("   1. Document chunking works")
    print("   2. OpenAI embeddings generation works")
    print("   3. Vector storage in Supabase works")
    print("   4. Similarity search works")
    print()
    print("🚀 Your RAG pipeline is ready!")
    print()
    print("📚 Next steps:")
    print("   1. Build document upload API endpoint")
    print("   2. Create retrieval pipeline")
    print("   3. Integrate with LLM for answer generation")


def test_embedding_quality():
    """Test that similar texts get similar embeddings."""
    
    print("\n" + "=" * 70)
    print("🔬 Bonus Test: Embedding Quality")
    print("-" * 70)
    print()
    
    try:
        embedding_service = EmbeddingService()
        
        # Similar texts (should have high similarity)
        text1 = "Apple's revenue grew by 20% year over year"
        text2 = "Apple saw a 20% increase in revenue compared to last year"
        
        # Different text (should have low similarity)
        text3 = "Tesla announced new electric vehicle models"
        
        print("Testing semantic similarity:")
        print(f"  Text 1: \"{text1}\"")
        print(f"  Text 2: \"{text2}\"")
        print(f"  Text 3: \"{text3}\"")
        print()
        
        # Generate embeddings
        embeddings = embedding_service.embed_texts([text1, text2, text3])
        
        # Calculate similarities
        vector_store = VectorStore()
        sim_1_2 = vector_store._cosine_similarity(embeddings[0], embeddings[1])
        sim_1_3 = vector_store._cosine_similarity(embeddings[0], embeddings[2])
        
        print("Similarity scores:")
        print(f"  Text 1 vs Text 2 (similar): {sim_1_2:.4f}")
        print(f"  Text 1 vs Text 3 (different): {sim_1_3:.4f}")
        print()
        
        if sim_1_2 > sim_1_3:
            print("✅ Embeddings capture semantic similarity correctly!")
        else:
            print("⚠️  Unexpected similarity scores")
        
    except Exception as e:
        print(f"⏭️  Skipping quality test: {e}")


if __name__ == "__main__":
    test_embedding_pipeline()
    test_embedding_quality()
    
    print("\n" + "=" * 70)
    print("💡 Pro Tips:")
    print("   • Use batch embedding for efficiency (up to 2048 texts)")
    print("   • Cache embeddings to avoid regenerating")
    print("   • Monitor OpenAI costs ($0.02 per 1M tokens)")
    print("   • Consider fine-tuning chunk size for your domain")
