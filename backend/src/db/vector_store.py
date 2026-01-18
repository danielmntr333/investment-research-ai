"""
pgvector operations for vector search.

This module handles storing and retrieving document chunks with embeddings
using Supabase (PostgreSQL + pgvector extension).
"""
from typing import List, Dict, Optional
from .supabase import get_supabase


class VectorStore:
    """
    Handle pgvector operations for semantic search.
    
    Key concepts:
    - pgvector: PostgreSQL extension for vector operations
    - Cosine distance (<=>): Measures similarity between vectors
    - Lower distance = more similar (0 = identical, 2 = opposite)
    
    Example similarity search:
        Query: "What was Apple's revenue?"
        → Embedding: [0.23, -0.45, 0.89, ...]
        → Find chunks with closest embeddings
        → Return: "Apple revenue was $383B..." (distance: 0.15)
    """
    
    def __init__(self):
        """Initialize vector store with Supabase client."""
        self.client = get_supabase()
    
    def insert_chunks(self, chunks: List[Dict]) -> List[str]:
        """
        Insert document chunks with embeddings into database.
        
        Args:
            chunks: List of chunk dictionaries with fields:
                - document_id: UUID of parent document
                - content: Text content
                - embedding: 1536-dimensional vector
                - chunk_index: Position in document
                - metadata: Additional chunk metadata
                
        Returns:
            List of inserted chunk IDs
            
        Note:
            - Supabase automatically creates UUID for each chunk
            - Trigger auto-generates search_vector for full-text search
            - ivfflat index enables fast similarity search
        """
        if not chunks:
            return []
        
        try:
            # Insert all chunks in batch
            result = self.client.table('document_chunks').insert(chunks).execute()
            
            # Extract IDs from inserted rows
            chunk_ids = [row['id'] for row in result.data]
            
            return chunk_ids
            
        except Exception as e:
            raise RuntimeError(f"Failed to insert chunks: {str(e)}")
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        document_ids: Optional[List[str]] = None,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        Perform vector similarity search using pgvector.
        
        Args:
            query_embedding: Query vector (1536 dimensions)
            top_k: Number of results to return
            document_ids: Optional list of document IDs to filter by
            min_similarity: Minimum similarity threshold (0-1, higher = more similar)
            
        Returns:
            List of chunks with similarity scores, sorted by relevance
            Each result contains: id, content, metadata, document_id, similarity
            
        How it works:
            1. pgvector calculates cosine distance: embedding <=> query_embedding
            2. Distance is converted to similarity: 1 - (distance / 2)
            3. Results sorted by similarity (highest first)
            4. Returns top_k most similar chunks
            
        Note:
            - Cosine distance range: [0, 2]
            - Similarity range: [0, 1] where 1 = identical
            - ivfflat index makes this fast even with millions of vectors
        """
        try:
            # Build query
            query = self.client.table('document_chunks').select(
                'id, content, metadata, document_id, chunk_index, embedding'
            )
            
            # Filter by document IDs if provided
            if document_ids:
                query = query.in_('document_id', document_ids)
            
            # Execute query (get all matching chunks)
            result = query.execute()
            
            if not result.data:
                return []
            
            # Calculate similarities manually (Supabase Python client doesn't support
            # pgvector operators directly yet, so we fetch and compute)
            chunks_with_similarity = []
            
            for chunk in result.data:
                if chunk.get('embedding'):
                    # Parse embedding (it might be a string or list)
                    chunk_embedding = self._parse_embedding(chunk['embedding'])
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(
                        query_embedding, 
                        chunk_embedding
                    )
                    
                    # Filter by minimum similarity
                    if similarity >= min_similarity:
                        chunks_with_similarity.append({
                            'id': chunk['id'],
                            'content': chunk['content'],
                            'metadata': chunk['metadata'],
                            'document_id': chunk['document_id'],
                            'chunk_index': chunk['chunk_index'],
                            'similarity': similarity
                        })
            
            # Sort by similarity (highest first) and take top_k
            chunks_with_similarity.sort(key=lambda x: x['similarity'], reverse=True)
            return chunks_with_similarity[:top_k]
            
        except Exception as e:
            raise RuntimeError(f"Similarity search failed: {str(e)}")
    
    def delete_document_chunks(self, document_id: str) -> int:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: UUID of document
            
        Returns:
            Number of chunks deleted
            
        Note:
            This is automatically called when a document is deleted
            (CASCADE in database schema)
        """
        try:
            result = self.client.table('document_chunks').delete().eq(
                'document_id', document_id
            ).execute()
            
            return len(result.data) if result.data else 0
            
        except Exception as e:
            raise RuntimeError(f"Failed to delete chunks: {str(e)}")
    
    def get_document_chunks(self, document_id: str) -> List[Dict]:
        """
        Retrieve all chunks for a document.
        
        Args:
            document_id: UUID of document
            
        Returns:
            List of chunks ordered by chunk_index
        """
        try:
            result = self.client.table('document_chunks').select(
                'id, content, chunk_index, metadata'
            ).eq(
                'document_id', document_id
            ).order('chunk_index').execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve chunks: {str(e)}")
    
    def _parse_embedding(self, embedding) -> List[float]:
        """
        Parse embedding from database format to list of floats.
        
        Supabase/pgvector can return embeddings in different formats:
        - Already a list: [0.1, 0.2, ...]
        - String representation: "[0.1,0.2,...]"
        - Other serialized format
        
        Args:
            embedding: Embedding in any format
            
        Returns:
            List of floats
        """
        # If already a list of numbers, return as-is
        if isinstance(embedding, list) and embedding and isinstance(embedding[0], (int, float)):
            return [float(x) for x in embedding]
        
        # If it's a string, parse it
        if isinstance(embedding, str):
            import json
            # Remove any whitespace and parse as JSON
            embedding = embedding.strip()
            if embedding.startswith('['):
                return json.loads(embedding)
        
        # Otherwise, try to convert directly
        return list(embedding)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Formula: similarity = dot(A, B) / (norm(A) * norm(B))
        Range: [-1, 1] where 1 = identical, -1 = opposite
        
        Note: We normalize to [0, 1] range by: (similarity + 1) / 2
        """
        import math
        
        # Ensure both vectors are lists of floats
        vec1 = [float(x) for x in vec1]
        vec2 = [float(x) for x in vec2]
        
        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Normalize to [0, 1] range
        return (similarity + 1) / 2
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        document_ids: Optional[List[str]] = None,
        min_rank: float = 0.0
    ) -> List[Dict]:
        """
        Perform keyword-based full-text search using PostgreSQL FTS.
        
        Args:
            query: Search query
            top_k: Number of results to return
            document_ids: Optional list of document IDs to filter by
            min_rank: Minimum ranking threshold
            
        Returns:
            List of chunks with ranking scores, sorted by relevance
            Each result contains: id, content, metadata, document_id, rank
            
        How it works:
            1. PostgreSQL's full-text search finds keyword matches
            2. ts_rank calculates relevance score
            3. Results sorted by rank (higher = more relevant)
            4. Returns top_k most relevant chunks
            
        Note:
            - Uses search_vector column (tsvector) for fast search
            - Handles stemming, stop words automatically
            - Good for exact matches and specific terminology
        """
        try:
            # Build query - use RPC function for FTS
            # Note: This requires a custom SQL function in Supabase
            result = self.client.rpc(
                'keyword_search_chunks',
                {
                    'search_query': query,
                    'match_count': top_k,
                    'doc_ids': document_ids or [],
                    'min_rank_threshold': min_rank
                }
            ).execute()
            
            if not result.data:
                return []
            
            # Format results
            chunks = []
            for chunk in result.data:
                chunks.append({
                    'id': chunk['id'],
                    'content': chunk['content'],
                    'metadata': chunk['metadata'],
                    'document_id': chunk['document_id'],
                    'chunk_index': chunk['chunk_index'],
                    'rank': chunk.get('rank', 0.0),
                    'retrieval_method': 'keyword'
                })
            
            return chunks
            
        except Exception as e:
            # If RPC function doesn't exist, fall back to basic search
            print(f"Keyword search RPC failed: {e}. Falling back to basic search.")
            return self._fallback_keyword_search(query, top_k, document_ids)
    
    def _fallback_keyword_search(
        self,
        query: str,
        top_k: int,
        document_ids: Optional[List[str]]
    ) -> List[Dict]:
        """
        Fallback keyword search using basic text matching.
        Used when PostgreSQL FTS is not available.
        """
        try:
            # Build query
            db_query = self.client.table('document_chunks').select(
                'id, content, metadata, document_id, chunk_index'
            )
            
            # Filter by document IDs if provided
            if document_ids:
                db_query = db_query.in_('document_id', document_ids)
            
            # Execute query
            result = db_query.execute()
            
            if not result.data:
                return []
            
            # Simple keyword matching
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            chunks_with_score = []
            for chunk in result.data:
                content_lower = chunk['content'].lower()
                content_words = set(content_lower.split())
                
                # Calculate simple overlap score
                matches = len(query_words & content_words)
                if matches > 0:
                    score = matches / len(query_words)
                    chunks_with_score.append({
                        'id': chunk['id'],
                        'content': chunk['content'],
                        'metadata': chunk['metadata'],
                        'document_id': chunk['document_id'],
                        'chunk_index': chunk['chunk_index'],
                        'rank': score,
                        'retrieval_method': 'keyword'
                    })
            
            # Sort by score and return top_k
            chunks_with_score.sort(key=lambda x: x['rank'], reverse=True)
            return chunks_with_score[:top_k]
            
        except Exception as e:
            print(f"Fallback keyword search failed: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = 10,
        document_ids: Optional[List[str]] = None,
        alpha: float = 0.5
    ) -> List[Dict]:
        """
        Hybrid search combining vector and keyword search.
        
        Args:
            query: Search query text
            query_embedding: Query embedding vector
            top_k: Number of results to return
            document_ids: Optional document filter
            alpha: Weight for combining scores (0 = keyword only, 1 = vector only)
            
        Returns:
            List of chunks with combined scores
            
        Algorithm:
            1. Perform vector search → get vector_results with similarities
            2. Perform keyword search → get keyword_results with ranks
            3. Normalize both score types to [0, 1]
            4. Combine: score = alpha * vector_score + (1 - alpha) * keyword_score
            5. Sort by combined score and return top_k
        """
        # Get results from both methods
        vector_results = self.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more to account for overlap
            document_ids=document_ids
        )
        
        keyword_results = self.keyword_search(
            query=query,
            top_k=top_k * 2,
            document_ids=document_ids
        )
        
        # Combine results
        chunk_scores = {}
        
        # Add vector scores
        for chunk in vector_results:
            chunk_id = chunk['id']
            chunk_scores[chunk_id] = {
                'chunk': chunk,
                'vector_score': chunk['similarity'],
                'keyword_score': 0.0
            }
        
        # Add keyword scores
        for chunk in keyword_results:
            chunk_id = chunk['id']
            if chunk_id in chunk_scores:
                chunk_scores[chunk_id]['keyword_score'] = chunk['rank']
            else:
                chunk_scores[chunk_id] = {
                    'chunk': chunk,
                    'vector_score': 0.0,
                    'keyword_score': chunk['rank']
                }
        
        # Calculate combined scores
        combined_results = []
        for chunk_id, scores in chunk_scores.items():
            combined_score = (
                alpha * scores['vector_score'] + 
                (1 - alpha) * scores['keyword_score']
            )
            
            result = scores['chunk'].copy()
            result['score'] = combined_score
            result['vector_score'] = scores['vector_score']
            result['keyword_score'] = scores['keyword_score']
            result['retrieval_method'] = 'hybrid'
            
            combined_results.append(result)
        
        # Sort by combined score and return top_k
        combined_results.sort(key=lambda x: x['score'], reverse=True)
        return combined_results[:top_k]
