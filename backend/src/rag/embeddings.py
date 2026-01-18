"""
Embedding service with caching.

Uses OpenAI's text-embedding-3-small model for generating vector embeddings.
These embeddings are stored in pgvector for semantic search.
"""
from typing import List, Optional
import openai
from src.utils.config import settings


class EmbeddingService:
    """
    Generate and cache embeddings using OpenAI.
    
    Model: text-embedding-3-small
    - Dimensions: 1536 (matches our database schema)
    - Cost: $0.02 per 1M tokens
    - Performance: Fast and high quality
    
    Why embeddings?
    - Convert text to numerical vectors
    - Similar text = similar vectors
    - Enables semantic search (meaning-based, not keyword matching)
    
    Example:
        "Apple revenue grew 20%" → [0.23, -0.45, 0.89, ...]
        "Apple sales increased 20%" → [0.24, -0.44, 0.87, ...] (similar!)
        "Banana prices fell 10%" → [0.01, 0.92, -0.34, ...] (different!)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embedding service.
        
        Args:
            api_key: OpenAI API key (uses settings.openai_api_key if not provided)
        """
        self.model = "text-embedding-3-small"
        self.dimension = 1536
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file. "
                "Get your API key from https://platform.openai.com/api-keys"
            )
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Batch embed multiple texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per text)
            
        Note:
            - OpenAI API supports up to 2048 texts per request
            - Batching is more efficient than individual calls
            - Each embedding is a 1536-dimensional vector
        """
        if not texts:
            return []
        
        # Filter out empty strings
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        
        try:
            # Call OpenAI API
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )
            
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}")
    
    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            query: Query string to embed
            
        Returns:
            Single embedding vector
            
        Note:
            This is a convenience method that calls embed_texts internally.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        embeddings = self.embed_texts([query])
        return embeddings[0] if embeddings else []
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Embed document chunks and add embeddings to chunk data.
        
        Args:
            chunks: List of chunk dictionaries (from chunker)
                    Each should have 'content' field
            
        Returns:
            Same chunks with 'embedding' field added
            
        Example:
            Input: [{'content': 'Apple revenue...', 'chunk_index': 0}]
            Output: [{'content': 'Apple revenue...', 'chunk_index': 0, 
                      'embedding': [0.23, -0.45, ...]}]
        """
        if not chunks:
            return []
        
        # Extract content from chunks
        contents = [chunk['content'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embed_texts(contents)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        return chunks
