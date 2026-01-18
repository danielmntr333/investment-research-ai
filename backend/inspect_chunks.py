"""
Inspect document chunks to see how a document was chunked.

Usage:
    poetry run python inspect_chunks.py --doc-name "apple" --search "accounting"
"""
import sys
import argparse
from src.db.supabase import get_supabase


def print_chunk(chunk, index, total):
    """Print a single chunk with formatting."""
    print(f"\n{'='*80}")
    print(f"CHUNK {index}/{total}")
    print(f"{'='*80}")
    print(f"ID: {chunk['id']}")
    print(f"Chunk Index: {chunk['chunk_index']}")
    
    metadata = chunk.get('metadata', {})
    print(f"Type: {metadata.get('chunk_type', 'unknown')}")
    print(f"Parent Section: {metadata.get('parent_section', 'N/A')}")
    print(f"Length: {len(chunk['content'])} characters")
    
    print(f"\nCONTENT:")
    print("-" * 80)
    print(chunk['content'])
    print("-" * 80)


def inspect_chunks(doc_filter: str = None, search_term: str = None, limit: int = 10):
    """
    Inspect chunks in documents.
    
    Args:
        doc_filter: Filter documents by filename
        search_term: Search for chunks containing this term
        limit: Maximum chunks to display
    """
    db = get_supabase()
    
    # Find documents
    print(f"🔍 Searching for documents...")
    docs_query = db.table('documents').select('id, filename, processed')
    
    if doc_filter:
        docs_query = docs_query.ilike('filename', f'%{doc_filter}%')
    
    docs_result = docs_query.execute()
    documents = docs_result.data if docs_result.data else []
    
    if not documents:
        print(f"❌ No documents found{' matching: ' + doc_filter if doc_filter else ''}")
        return
    
    # Get chunks first to count them per document
    doc_ids = [doc['id'] for doc in documents]
    
    print(f"\n📄 Fetching chunks to count...")
    chunks_query = db.table('document_chunks').select(
        'id, content, metadata, chunk_index, document_id'
    ).in_('document_id', doc_ids).order('document_id, chunk_index')
    
    chunks_result = chunks_query.execute()
    all_chunks = chunks_result.data if chunks_result.data else []
    
    # Count chunks per document
    chunk_counts = {}
    for chunk in all_chunks:
        doc_id = chunk['document_id']
        chunk_counts[doc_id] = chunk_counts.get(doc_id, 0) + 1
    
    print(f"\n✅ Found {len(documents)} document(s):")
    for doc in documents:
        count = chunk_counts.get(doc['id'], 0)
        print(f"   - {doc['filename']} (Chunks: {count})")
    
    print(f"✅ Total chunks: {len(all_chunks)}")
    
    # Filter by search term if provided
    if search_term:
        print(f"\n🔎 Filtering chunks containing '{search_term}'...")
        search_lower = search_term.lower()
        filtered_chunks = [
            c for c in all_chunks 
            if search_lower in c['content'].lower()
        ]
        
        print(f"✅ Found {len(filtered_chunks)} matching chunks")
        
        if not filtered_chunks:
            print("\n❌ No chunks contain the search term")
            print("   Try a different search term or inspect all chunks with --all")
            return
        
        chunks_to_show = filtered_chunks
    else:
        chunks_to_show = all_chunks
    
    # Show chunks
    num_to_show = min(limit, len(chunks_to_show))
    
    if num_to_show < len(chunks_to_show):
        print(f"\n📋 Showing first {num_to_show} of {len(chunks_to_show)} chunks (use --limit to show more)")
    else:
        print(f"\n📋 Showing all {num_to_show} chunks")
    
    for i, chunk in enumerate(chunks_to_show[:num_to_show], 1):
        print_chunk(chunk, i, num_to_show)
    
    # Summary
    if search_term and chunks_to_show:
        print(f"\n\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        
        # Group by parent section
        sections = {}
        for chunk in chunks_to_show:
            section = chunk.get('metadata', {}).get('parent_section', 'Unknown')
            if section not in sections:
                sections[section] = []
            sections[section].append(chunk)
        
        print(f"\nChunks grouped by section:")
        for section, chunks in sections.items():
            print(f"   - {section}: {len(chunks)} chunks")
        
        # Check if chunks have proper context
        chunks_with_context = sum(
            1 for c in chunks_to_show 
            if c.get('metadata', {}).get('parent_section') and 
               c.get('metadata', {}).get('parent_section') != 'Document'
        )
        
        print(f"\nChunks with section context: {chunks_with_context}/{len(chunks_to_show)}")
        
        if chunks_with_context < len(chunks_to_show) * 0.5:
            print("   ⚠️  Many chunks lack section context - chunking may not be optimal")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inspect document chunks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Inspect all chunks in Apple document
  python inspect_chunks.py --doc-name apple
  
  # Search for chunks containing "accounting"
  python inspect_chunks.py --doc-name apple --search "accounting"
  
  # Show more chunks
  python inspect_chunks.py --doc-name apple --search "pronouncements" --limit 20
        """
    )
    
    parser.add_argument(
        '--doc-name',
        type=str,
        help='Filter documents by filename (case insensitive)'
    )
    
    parser.add_argument(
        '--search',
        type=str,
        help='Search for chunks containing this term'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of chunks to display (default: 10)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all chunks (no limit)'
    )
    
    args = parser.parse_args()
    
    limit = sys.maxsize if args.all else args.limit
    
    inspect_chunks(
        doc_filter=args.doc_name,
        search_term=args.search,
        limit=limit
    )


if __name__ == "__main__":
    main()
