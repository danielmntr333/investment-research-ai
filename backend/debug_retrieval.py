"""
Debug script to diagnose retrieval issues.

This script helps identify why specific queries aren't finding relevant information
in uploaded documents.

Usage:
    poetry run python debug_retrieval.py "Recent Accounting Pronouncements" --doc-name "apple"
"""
import asyncio
import sys
from src.db.supabase import get_supabase
from src.rag.embeddings import EmbeddingService
from src.db.vector_store import VectorStore
from src.rag.retrieval import Retriever


def print_section(title: str, width: int = 80):
    """Print a section header."""
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width + "\n")


async def debug_retrieval(query: str, document_filter: str = None):
    """
    Debug retrieval for a specific query.
    
    Args:
        query: The query to test
        document_filter: Optional string to filter documents by name
    """
    print_section("RETRIEVAL DEBUG REPORT")
    print(f"Query: '{query}'")
    print(f"Document filter: {document_filter or 'None (all documents)'}")
    
    try:
        # Initialize components
        db = get_supabase()
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        retriever = Retriever(embedding_service=embedding_service, vector_store=vector_store)
        
        # Step 1: Find documents
        print_section("STEP 1: Available Documents")
        
        docs_query = db.table('documents').select('id, filename, processed, uploaded_at')
        if document_filter:
            docs_query = docs_query.ilike('filename', f'%{document_filter}%')
        
        docs_result = docs_query.execute()
        documents = docs_result.data if docs_result.data else []
        
        if not documents:
            print(f"❌ No documents found{' matching filter: ' + document_filter if document_filter else ''}")
            return
        
        # Get document IDs
        doc_ids = [doc['id'] for doc in documents]
        
        # Step 2: Check chunks
        print_section("STEP 2: Document Chunks Analysis")
        
        chunks_result = db.table('document_chunks').select('id, content, metadata, chunk_index, document_id').in_('document_id', doc_ids).order('chunk_index').execute()
        all_chunks = chunks_result.data if chunks_result.data else []
        
        # Count chunks per document
        chunk_counts = {}
        for chunk in all_chunks:
            doc_id = chunk.get('document_id')
            if doc_id:
                chunk_counts[doc_id] = chunk_counts.get(doc_id, 0) + 1
        
        print(f"✅ Found {len(documents)} document(s):")
        for doc in documents:
            count = chunk_counts.get(doc['id'], 0)
            processed_status = "✓ Processed" if doc.get('processed') else "⚠ Not Processed"
            print(f"   - {doc['filename']} (ID: {doc['id'][:8]}..., Chunks: {count}, {processed_status})")
        
        print(f"\n✅ Total chunks in document(s): {len(all_chunks)}")
        
        # Check if query appears in any chunk (case insensitive)
        query_lower = query.lower()
        matching_chunks = []
        
        for chunk in all_chunks:
            content_lower = chunk['content'].lower()
            if any(word.lower() in content_lower for word in query.split()):
                matching_chunks.append(chunk)
        
        print(f"\n📝 Chunks containing query keywords: {len(matching_chunks)}")
        
        if matching_chunks:
            print("\n   Sample matching chunks:")
            for i, chunk in enumerate(matching_chunks[:3]):
                content_preview = chunk['content'][:200].replace('\n', ' ')
                print(f"\n   Chunk {chunk['chunk_index']}:")
                print(f"   {content_preview}...")
                
                # Check metadata
                metadata = chunk.get('metadata', {})
                parent_section = metadata.get('parent_section', 'N/A')
                print(f"   Parent section: {parent_section}")
        else:
            print("   ⚠️  No chunks contain exact keyword matches")
            print("   This might be okay if using semantic search, but could indicate chunking issues")
        
        # Step 3: Test retrieval strategies
        print_section("STEP 3: Testing Retrieval Strategies")
        
        strategies = ['vector', 'keyword', 'hybrid']
        
        for strategy in strategies:
            print(f"\n🔍 Testing '{strategy}' retrieval...")
            
            try:
                results = retriever.retrieve(
                    query=query,
                    top_k=5,
                    document_ids=doc_ids,
                    strategy=strategy,
                    min_similarity=0.0  # Don't filter by similarity for debugging
                )
                
                print(f"   Retrieved: {len(results)} chunks")
                
                if results:
                    print(f"   Top result score: {results[0].get('score', results[0].get('similarity', 'N/A')):.4f}")
                    print(f"   Preview: {results[0]['content'][:150].replace(chr(10), ' ')}...")
                    
                    # Check if any retrieved chunks are in our matching set
                    retrieved_ids = {r['id'] for r in results}
                    matching_ids = {c['id'] for c in matching_chunks}
                    overlap = retrieved_ids & matching_ids
                    
                    if matching_chunks:
                        print(f"   ✓ Retrieved {len(overlap)}/{len(matching_chunks)} keyword-matching chunks")
                else:
                    print("   ❌ No results retrieved!")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        # Step 4: Test with full RAG pipeline
        print_section("STEP 4: Full RAG Pipeline Test")
        
        from src.rag.pipeline import RAGPipeline
        from src.llm.provider import LLMProvider
        
        llm_provider = LLMProvider()
        rag_pipeline = RAGPipeline(
            retriever=retriever,
            llm_provider=llm_provider
        )
        
        print("🤖 Running full RAG query...")
        
        try:
            result = rag_pipeline.query(
                question=query,
                document_ids=doc_ids,
                top_k=5,
                strategy='hybrid',
                use_reranking=False
            )
            
            print(f"\n   Answer preview: {result['answer'][:300]}...")
            print(f"\n   Sources retrieved: {len(result.get('sources', []))}")
            print(f"   Status: {result.get('metadata', {}).get('status', 'unknown')}")
            
            # Show sources
            sources = result.get('sources', [])
            if sources:
                print("\n   📚 Sources used:")
                for i, source in enumerate(sources[:3]):
                    print(f"\n   Source {i+1}:")
                    print(f"   Similarity: {source.get('similarity', 'N/A')}")
                    print(f"   Content: {source['content'][:150]}...")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Step 5: Recommendations
        print_section("RECOMMENDATIONS")
        
        if not all_chunks:
            print("❌ ISSUE: No chunks found in database")
            print("   → Re-upload your document or check document processing")
            
        elif not matching_chunks:
            print("⚠️  WARNING: Query keywords not found in any chunks")
            print("   → Check if the section exists in your uploaded document")
            print("   → Verify document was processed correctly")
            print("   → Try a different query with keywords that appear in the document")
            
        elif len(matching_chunks) > 0:
            # Check if keyword search found them
            keyword_results = retriever.retrieve(
                query=query,
                top_k=10,
                document_ids=doc_ids,
                strategy='keyword',
                min_similarity=0.0
            )
            
            keyword_ids = {r['id'] for r in keyword_results}
            matching_ids = {c['id'] for c in matching_chunks}
            
            if not (keyword_ids & matching_ids):
                print("⚠️  ISSUE: Keyword search not finding relevant chunks")
                print("   → Full-text search (FTS) may not be configured")
                print("   → Run migration: backend/migrations/add_fts_support.sql")
                print("   → Or use 'vector' or 'hybrid' strategies")
            
            # Check vector search
            vector_results = retriever.retrieve(
                query=query,
                top_k=10,
                document_ids=doc_ids,
                strategy='vector',
                min_similarity=0.0
            )
            
            if vector_results:
                vector_ids = {r['id'] for r in vector_results}
                if not (vector_ids & matching_ids):
                    print("⚠️  ISSUE: Vector search ranking irrelevant chunks higher")
                    print("   → Embeddings may not capture the semantic meaning well")
                    print("   → Try using query transformation or reranking")
                    print("   → Consider adjusting chunk size/overlap")
                else:
                    print("✅ Vector search is finding relevant chunks!")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python debug_retrieval.py <query> [--doc-name <filter>]")
        print("\nExample:")
        print('  python debug_retrieval.py "Recent Accounting Pronouncements" --doc-name apple')
        sys.exit(1)
    
    query = sys.argv[1]
    
    # Parse optional document filter
    doc_filter = None
    if '--doc-name' in sys.argv:
        idx = sys.argv.index('--doc-name')
        if idx + 1 < len(sys.argv):
            doc_filter = sys.argv[idx + 1]
    
    # Run debug
    asyncio.run(debug_retrieval(query, doc_filter))


if __name__ == "__main__":
    main()
