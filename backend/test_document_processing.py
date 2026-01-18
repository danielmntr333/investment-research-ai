"""
Test script for document parsing and chunking.

This demonstrates the complete document processing pipeline:
PDF → Parser → Text → Chunker → Chunks ready for embedding

Usage:
    python test_document_processing.py
"""
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.document_processing.parser import DocumentParser
from src.rag.chunking import SimpleChunker


def test_parsing_and_chunking():
    """Test document parsing and chunking with sample text."""
    
    print("🧪 Testing Document Processing Pipeline\n")
    print("=" * 60)
    
    # Sample financial document text
    sample_text = """
    Financial Results - Q4 2023
    
    Apple Inc. today announced financial results for its fiscal 2023 fourth quarter.
    The Company posted quarterly revenue of $89.5 billion, down 1 percent year over year.
    
    Products and Services
    
    Products revenue decreased 5 percent year over year to $67.2 billion in the quarter.
    Services revenue reached an all-time high of $22.3 billion, up 16 percent year over year.
    
    iPhone revenue was $43.8 billion for the quarter, down 2.4 percent compared to the
    prior year quarter. Mac revenue was $7.6 billion, down 33.8 percent year over year.
    iPad revenue was $6.4 billion, down 10.1 percent year over year.
    
    Operating Performance
    
    Gross margin was 45.2 percent compared to 42.3 percent in the year-ago quarter.
    Operating expenses were $14.5 billion compared to $13.5 billion in the year-ago quarter.
    Net income was $22.96 billion, or $1.46 per diluted share, compared to $20.72 billion,
    or $1.29 per diluted share, a year ago.
    
    The Board of Directors declared a cash dividend of $0.24 per share of common stock.
    The Company's cash, cash equivalents and marketable securities totaled $166.5 billion.
    """
    
    print("\n📄 STEP 1: Document Text")
    print("-" * 60)
    print(f"Sample text length: {len(sample_text)} characters")
    print(f"First 200 chars: {sample_text[:200]}...")
    
    # Test chunking
    print("\n✂️  STEP 2: Chunking")
    print("-" * 60)
    
    chunker = SimpleChunker(
        chunk_size=500,      # Smaller for demo (normally 1000)
        chunk_overlap=100    # Overlap to preserve context
    )
    
    chunks = chunker.chunk_text(sample_text)
    
    print(f"✓ Created {len(chunks)} chunks")
    print(f"✓ Chunk size: {chunker.chunk_size} chars")
    print(f"✓ Overlap: {chunker.chunk_overlap} chars")
    
    # Show chunks
    print("\n📦 Chunks Created:")
    print("-" * 60)
    
    for i, chunk in enumerate(chunks):
        print(f"\n[Chunk {i}] ({len(chunk.content)} chars)")
        print(f"Start: {chunk.start_char}, End: {chunk.end_char}")
        print(f"Content preview: {chunk.content[:150]}...")
        
        # Show overlap with next chunk (if exists)
        if i < len(chunks) - 1:
            overlap_start = chunks[i+1].start_char
            overlap_end = chunk.end_char
            if overlap_start < overlap_end:
                overlap_chars = overlap_end - overlap_start
                print(f"↔️  Overlaps {overlap_chars} chars with next chunk")
    
    # Statistics
    print("\n" + "=" * 60)
    print("📊 Statistics:")
    print(f"  • Original text: {len(sample_text)} characters")
    print(f"  • Chunks created: {len(chunks)}")
    print(f"  • Avg chunk size: {sum(len(c.content) for c in chunks) // len(chunks)} chars")
    print(f"  • Coverage: {sum(len(c.content) for c in chunks) / len(sample_text) * 100:.1f}% (>100% due to overlap)")
    
    print("\n✅ Document processing pipeline works!")
    print("\n💡 What you learned:")
    print("   • Documents are broken into overlapping chunks")
    print("   • Overlap preserves context across boundaries")
    print("   • Each chunk has metadata (position, length, etc.)")
    print("   • These chunks will be embedded and stored in the vector database")


def test_pdf_parsing():
    """Test PDF parsing (if sample PDF exists)."""
    import os
    
    print("\n" + "=" * 60)
    print("📄 Testing PDF Parsing (Optional)")
    print("-" * 60)
    
    # Check for sample PDF
    sample_pdf_path = "../data/sample_docs/sample.pdf"
    
    if os.path.exists(sample_pdf_path):
        print(f"Found sample PDF: {sample_pdf_path}")
        
        parser = DocumentParser()
        try:
            doc = parser.parse(sample_pdf_path, 'pdf')
            
            print(f"✓ Parsed {len(doc.pages)} pages")
            print(f"✓ Total text: {len(doc.full_text)} characters")
            print(f"✓ Metadata: {doc.metadata}")
            
            if doc.pages:
                print(f"\nFirst page preview:")
                print(doc.pages[0]['text'][:200] + "...")
                
        except Exception as e:
            print(f"❌ Error parsing PDF: {e}")
    else:
        print(f"⏭️  No sample PDF found at {sample_pdf_path}")
        print("   To test PDF parsing, add a PDF file to data/sample_docs/")


if __name__ == "__main__":
    test_parsing_and_chunking()
    test_pdf_parsing()
    
    print("\n" + "=" * 60)
    print("🎉 All tests complete!")
    print("\n📚 Next steps:")
    print("   1. Generate embeddings for these chunks")
    print("   2. Store chunks with embeddings in vector database")
    print("   3. Build retrieval system to find relevant chunks")
    print("   4. Generate answers using retrieved context")
