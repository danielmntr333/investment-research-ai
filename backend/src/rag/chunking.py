"""
Document chunking for RAG pipeline.

This module breaks long documents into smaller, overlapping chunks
that can be embedded and searched efficiently.

Uses LangChain's RecursiveCharacterTextSplitter for production-grade chunking.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


@dataclass
class Chunk:
    """
    Represents a single chunk of text.
    
    Attributes:
        content: The actual text content
        chunk_type: Type of content ('text', 'table', 'list')
        chunk_index: Position in the document (0, 1, 2, ...)
        start_char: Character position where chunk starts
        end_char: Character position where chunk ends
        parent_section: Section header this chunk belongs to
        metadata: Additional information about the chunk
    """
    content: str
    chunk_type: str
    chunk_index: int
    start_char: int
    end_char: int
    parent_section: str
    metadata: Dict


class SimpleChunker:
    """
    Text chunker using LangChain's RecursiveCharacterTextSplitter.
    
    Why chunking?
    - LLMs have token limits (can't process entire 50-page documents)
    - Smaller chunks = more precise retrieval
    - Overlap ensures we don't split important context
    
    Example:
        Text: "Apple revenue was $383B. This represents growth..."
        
        Chunk 1: "Apple revenue was $383B. This represents..."
        Chunk 2: "...This represents growth of 20% year over year..."
        
        Note: Chunks overlap so context isn't lost!
    
    Uses LangChain's RecursiveCharacterTextSplitter which:
    - Tries multiple separators intelligently (paragraphs → sentences → words)
    - Handles edge cases better than custom solutions
    - Battle-tested in thousands of production apps
    """
    
    def __init__(
        self, 
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize chunker using LangChain's RecursiveCharacterTextSplitter.
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: How many characters overlap between chunks
            separators: List of separators to try (default: smart hierarchy)
            
        Learning note:
            - 1000 chars ≈ 250 tokens (roughly 4 chars per token)
            - Overlap helps maintain context across boundaries
            - Separators are tried in order: paragraph → sentence → word
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        # Use smart separators by default (paragraph breaks → newlines → periods → spaces)
        if separators is None:
            separators = ["\n\n", "\n", ". ", " ", ""]
        
        # Initialize LangChain's splitter
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Optional[Dict] = None
    ) -> List[Chunk]:
        """
        Chunk text into overlapping segments using LangChain's splitter.
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Chunk objects with positions and metadata
            
        Algorithm (via RecursiveCharacterTextSplitter):
            1. Try to split on first separator (paragraph breaks)
            2. If chunks too big, try next separator (newlines)
            3. Continue down separator hierarchy (sentences, words)
            4. Maintain overlap between consecutive chunks
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        # Use LangChain's splitter to get text chunks
        text_chunks = self._splitter.split_text(text)
        
        # Convert to our Chunk objects with position tracking
        chunks = []
        current_pos = 0
        
        for i, chunk_text in enumerate(text_chunks):
            # Find where this chunk appears in the original text
            # (Note: This is approximate due to overlap, but good enough for tracking)
            chunk_start = text.find(chunk_text, current_pos)
            if chunk_start == -1:
                chunk_start = current_pos
            
            chunk_end = chunk_start + len(chunk_text)
            
            chunks.append(Chunk(
                content=chunk_text,
                chunk_type='text',
                chunk_index=i,
                start_char=chunk_start,
                end_char=chunk_end,
                parent_section='',
                metadata={
                    **metadata, 
                    'length': len(chunk_text),
                    'splitter': 'RecursiveCharacterTextSplitter'
                }
            ))
            
            # Move position forward (accounting for overlap)
            current_pos = chunk_start + len(chunk_text) - self.chunk_overlap
        
        return chunks
    
    def chunk_document(
        self, 
        text: str, 
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Chunk document and return in dict format (for database storage).
        
        Args:
            text: Document text
            document_id: ID of the document
            metadata: Additional metadata
            
        Returns:
            List of chunk dictionaries ready for database
        """
        chunks = self.chunk_text(text, metadata)
        
        result = []
        for chunk in chunks:
            result.append({
                'document_id': document_id,
                'content': chunk.content,
                'chunk_index': chunk.chunk_index,
                'metadata': {
                    **chunk.metadata,
                    'start_char': chunk.start_char,
                    'end_char': chunk.end_char,
                }
            })
        
        return result


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
        preserve_tables: bool = True,
        add_context: bool = True
    ):
        """
        Initialize advanced financial document chunker.
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: How many characters overlap between chunks
            preserve_tables: Keep tables as single chunks
            add_context: Prepend section headers to chunks for context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_tables = preserve_tables
        self.add_context = add_context
        
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
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Main chunking method with structure awareness.
        
        Process:
        1. Detect document structure
        2. Extract tables separately
        3. Chunk text sections with context
        4. Combine all chunks with metadata
        
        Args:
            text: Document text
            document_id: ID of the document
            metadata: Additional metadata
            
        Returns:
            List of chunk dictionaries ready for database
        """
        metadata = metadata or {}
        
        # Step 1: Detect structure
        sections = self._detect_sections(text)
        
        # Step 2: Process each section
        all_chunks = []
        position = 0
        
        for section in sections:
            section_chunks = self._process_section(
                section, 
                document_id, 
                metadata, 
                position
            )
            all_chunks.extend(section_chunks)
            position += len(section_chunks)
        
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
        current_section = {
            'header': 'Document',
            'content': '',
            'type': 'text',
            'start_line': 0
        }
        
        # Common financial document header patterns
        header_patterns = [
            r'^[A-Z][A-Z\s]{10,}$',  # ALL CAPS (min 10 chars)
            r'^Item\s+\d+[A-Za-z]?\.',  # Item 1., Item 1A., etc.
            r'^\d+\.\s+[A-Z]',  # 1. Header, 2. Header
            r'^[A-Z][a-z]+\s+Statement',  # Income Statement, Balance Sheet
            r'^Part\s+[IVX]+',  # Part I, Part II (Roman numerals)
        ]
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if line is a header
            is_header = any(
                re.match(pattern, line_stripped) 
                for pattern in header_patterns
            )
            
            # Headers shouldn't be too long and should have content
            if is_header and 5 < len(line_stripped) < 100:
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'header': line_stripped,
                    'content': '',
                    'type': 'text',
                    'start_line': i
                }
            else:
                # Check if this might be a table
                if self.preserve_tables and self._is_table_line(line_stripped):
                    # If we're in a text section, save it and start table section
                    if current_section['type'] == 'text' and current_section['content'].strip():
                        sections.append(current_section)
                        current_section = {
                            'header': current_section['header'],
                            'content': line + '\n',
                            'type': 'table',
                            'start_line': i
                        }
                    else:
                        current_section['content'] += line + '\n'
                else:
                    # If we were in a table, save it and start text section
                    if current_section['type'] == 'table' and len(current_section['content'].split('\n')) >= 3:
                        sections.append(current_section)
                        current_section = {
                            'header': current_section['header'],
                            'content': line + '\n',
                            'type': 'text',
                            'start_line': i
                        }
                    else:
                        current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _process_section(
        self,
        section: Dict,
        document_id: str,
        metadata: Dict,
        start_position: int
    ) -> List[Dict]:
        """Process a single section into chunks."""
        chunks = []
        
        if section['type'] == 'table':
            # Keep tables intact as single chunks
            chunk_dict = {
                'document_id': document_id,
                'content': section['content'].strip(),
                'chunk_index': start_position,
                'metadata': {
                    **metadata,
                    'chunk_type': 'table',
                    'parent_section': section['header'],
                    'length': len(section['content'])
                }
            }
            chunks.append(chunk_dict)
        
        else:
            # Chunk text with context
            text_chunks = self._chunk_with_context(
                section['content'],
                section['header']
            )
            
            for i, content in enumerate(text_chunks):
                chunk_dict = {
                    'document_id': document_id,
                    'content': content,
                    'chunk_index': start_position + i,
                    'metadata': {
                        **metadata,
                        'chunk_type': 'text',
                        'parent_section': section['header'],
                        'section_chunk_index': i,
                        'total_section_chunks': len(text_chunks),
                        'length': len(content)
                    }
                }
                chunks.append(chunk_dict)
        
        return chunks
    
    def _chunk_with_context(self, text: str, section_header: str) -> List[str]:
        """
        Chunk text while preserving context by prepending section header.
        
        Example:
        Original chunk: "Revenue increased by 20%..."
        With context: "## Financial Performance\n\nRevenue increased by 20%..."
        """
        # Split into base chunks
        base_chunks = self.text_splitter.split_text(text)
        
        # Add context to each chunk if enabled
        if self.add_context and section_header and section_header != 'Document':
            contextualized_chunks = []
            for chunk in base_chunks:
                # Prepend section header for context
                contextualized = f"## {section_header}\n\n{chunk}"
                contextualized_chunks.append(contextualized)
            return contextualized_chunks
        
        return base_chunks
    
    def _is_table_line(self, line: str) -> bool:
        """
        Check if a line is likely part of a table.
        
        Heuristics:
        - Multiple numbers in the line
        - Column separators (|, \t, multiple spaces)
        - Common table keywords
        """
        if not line:
            return False
        
        # Count numbers (including formatted numbers like 1,234.56)
        numbers = re.findall(r'\d+[\d,\.]*', line)
        
        # Check for separators
        has_pipes = line.count('|') >= 2
        has_tabs = '\t' in line
        has_multiple_spaces = '  ' in line  # Multiple consecutive spaces
        
        # Table keywords
        table_keywords = ['total', 'amount', 'balance', 'assets', 'liabilities', 
                         'revenue', 'income', 'expenses', 'year', 'quarter']
        has_table_keyword = any(kw in line.lower() for kw in table_keywords)
        
        # Line is likely a table if:
        # - Has multiple numbers AND separators OR keywords
        # - Has column separators (pipes/tabs)
        return (
            (len(numbers) >= 2 and (has_multiple_spaces or has_table_keyword)) or
            has_pipes or
            has_tabs
        )
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Optional[Dict] = None
    ) -> List[Chunk]:
        """
        Chunk text into overlapping segments (backward compatibility).
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Chunk objects with positions and metadata
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        # Use document chunking and convert to Chunk objects
        doc_chunks = self.chunk_document(text, 'temp_doc', metadata)
        
        chunks = []
        for i, chunk_dict in enumerate(doc_chunks):
            chunks.append(Chunk(
                content=chunk_dict['content'],
                chunk_type=chunk_dict['metadata'].get('chunk_type', 'text'),
                chunk_index=i,
                start_char=0,  # Not tracked in new implementation
                end_char=len(chunk_dict['content']),
                parent_section=chunk_dict['metadata'].get('parent_section', ''),
                metadata=chunk_dict['metadata']
            ))
        
        return chunks
