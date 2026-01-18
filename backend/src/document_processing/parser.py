"""
Parse different document types (PDF, Excel, HTML).

This module handles converting various file formats into text that can be processed by the RAG system.
"""
from typing import Dict, List, Optional
import fitz  # PyMuPDF


class ParsedDocument:
    """
    Parsed document structure.
    
    Attributes:
        pages: List of page dictionaries containing text and metadata
        full_text: Combined text from all pages
        metadata: Document-level metadata
    """
    
    def __init__(self, pages: List[Dict], metadata: Optional[Dict] = None):
        self.pages = pages
        self.metadata = metadata or {}
    
    @property
    def full_text(self) -> str:
        """Get combined text from all pages."""
        return "\n\n".join(page['text'] for page in self.pages if page.get('text'))
    
    def __repr__(self):
        return f"ParsedDocument(pages={len(self.pages)}, chars={len(self.full_text)})"


class DocumentParser:
    """
    Parse different file types into structured text.
    
    Currently supports:
    - PDF files (via PyMuPDF)
    - More formats coming soon!
    """
    
    def parse(self, file_path: str, file_type: str) -> ParsedDocument:
        """
        Parse document based on file type.
        
        Args:
            file_path: Path to the file
            file_type: Type of file ('pdf', 'xlsx', 'html')
            
        Returns:
            ParsedDocument with extracted text and metadata
            
        Raises:
            ValueError: If file type is not supported
            FileNotFoundError: If file doesn't exist
        """
        if file_type.lower() in ['pdf', 'application/pdf']:
            return self._parse_pdf(file_path)
        elif file_type.lower() in ['xlsx', 'xls', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            return self._parse_excel(file_path)
        elif file_type.lower() in ['html', 'htm', 'text/html']:
            return self._parse_html(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _parse_pdf(self, path: str) -> ParsedDocument:
        """
        Parse PDF with PyMuPDF (fitz).
        
        This extracts:
        - Text from each page
        - Page numbers
        - Basic document metadata
        
        Learning note: PyMuPDF is fast and reliable for text extraction.
        It handles most PDF formats well, including scanned docs (though OCR is not included).
        """
        try:
            # Open PDF
            doc = fitz.open(path)
            
            # Extract metadata
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'page_count': len(doc),
            }
            
            # Extract text from each page
            pages = []
            for page_num, page in enumerate(doc, start=1):
                # Get text from page
                text = page.get_text()
                
                # Store page data
                pages.append({
                    'page_num': page_num,
                    'text': text,
                    'char_count': len(text)
                })
            
            doc.close()
            
            return ParsedDocument(pages=pages, metadata=metadata)
            
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    def _parse_excel(self, path: str) -> ParsedDocument:
        """
        Parse Excel files.
        
        TODO: Implement Excel parsing with openpyxl/pandas
        For now, returns empty document.
        """
        # We'll implement this later when needed
        return ParsedDocument(pages=[{'page_num': 1, 'text': '', 'note': 'Excel parsing not yet implemented'}])
    
    def _parse_html(self, path: str) -> ParsedDocument:
        """
        Parse HTML documents.
        
        TODO: Implement HTML parsing with BeautifulSoup
        For now, returns empty document.
        """
        # We'll implement this later when needed
        return ParsedDocument(pages=[{'page_num': 1, 'text': '', 'note': 'HTML parsing not yet implemented'}])
