"""
Document retrieval for RAG pipeline.

Retrieves relevant document chunks based on semantic similarity, keyword matching,
or hybrid approaches.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from src.rag.embeddings import EmbeddingService
from src.db.vector_store import VectorStore
from src.db.supabase import get_supabase


@dataclass
class RetrievalResult:
    """Single retrieval result with metadata."""
    chunk_id: str
    content: str
    score: float
    metadata: Dict
    retrieval_method: str  # 'vector', 'keyword', 'hybrid', or 'rrf'
    document_id: str
    chunk_index: int


class Retriever:
    """
    Advanced retriever with multiple search strategies.
    
    Supports:
    - Vector similarity search (semantic)
    - Keyword search (exact matches)
    - Hybrid search (combined)
    - RRF (Reciprocal Rank Fusion)
    - Reranking integration
    """
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        reranker=None
    ):
        """
        Initialize retriever.
        
        Args:
            embedding_service: Service for generating query embeddings
            vector_store: Vector store for similarity search
            reranker: Optional reranker for precision boost
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.reranker = reranker
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        min_similarity: float = 0.3,
        strategy: str = 'hybrid',
        use_reranking: bool = False
    ) -> List[Dict]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: User's question
            top_k: Number of chunks to return
            document_ids: Optional list of document IDs to filter by
            min_similarity: Minimum similarity threshold (0-1)
            strategy: Retrieval strategy ('vector', 'keyword', 'hybrid', 'rrf')
            use_reranking: Whether to apply reranking
            
        Returns:
            List of relevant chunks with metadata and scores
            
        Process:
            1. Generate query embedding (if needed)
            2. Execute retrieval strategy
            3. Optionally rerank results
            4. Enrich with document metadata
            5. Return top_k most relevant results
        """
        try:
            # Generate query embedding for vector/hybrid strategies
            query_embedding = None
            if strategy in ['vector', 'hybrid', 'rrf']:
                query_embedding = self.embedding_service.embed_query(query)
            
            # Execute retrieval strategy
            if strategy == 'vector':
                results = self._vector_search(
                    query_embedding, top_k, document_ids, min_similarity
                )
            elif strategy == 'keyword':
                results = self._keyword_search(
                    query, top_k, document_ids
                )
            elif strategy == 'hybrid':
                results = self._hybrid_search(
                    query, query_embedding, top_k, document_ids
                )
            elif strategy == 'rrf':
                results = self._rrf_search(
                    query, query_embedding, top_k, document_ids
                )
            else:
                raise ValueError(f"Unknown retrieval strategy: {strategy}")
            
            # Apply reranking if requested and available
            if use_reranking and self.reranker and len(results) > 0:
                results = self.reranker.rerank(query, results, top_k)
            
            # Enrich results with document metadata (filename, etc.)
            results = self._enrich_with_document_metadata(results)
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Retrieval failed: {str(e)}")
    
    def _vector_search(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]],
        min_similarity: float
    ) -> List[Dict]:
        """Vector similarity search only."""
        return self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
            min_similarity=min_similarity
        )
    
    def _keyword_search(
        self,
        query: str,
        top_k: int,
        document_ids: Optional[List[str]]
    ) -> List[Dict]:
        """Keyword search only."""
        return self.vector_store.keyword_search(
            query=query,
            top_k=top_k,
            document_ids=document_ids
        )
    
    def _hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]],
        alpha: float = 0.5
    ) -> List[Dict]:
        """Hybrid search with linear combination."""
        return self.vector_store.hybrid_search(
            query=query,
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
            alpha=alpha
        )
    
    def _rrf_search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]],
        k: int = 60
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) for combining rankings.
        
        RRF formula: score = sum(1 / (k + rank_i))
        where rank_i is the rank in each retrieval method
        
        More robust than linear combination, less sensitive to score scales.
        """
        # Get results from both methods
        vector_results = self._vector_search(
            query_embedding,
            top_k * 2,  # Get more to account for overlap
            document_ids,
            min_similarity=0.0
        )
        
        keyword_results = self._keyword_search(
            query,
            top_k * 2,
            document_ids
        )
        
        # Build rankings
        vector_ranks = {
            result['id']: i + 1 
            for i, result in enumerate(vector_results)
        }
        keyword_ranks = {
            result['id']: i + 1 
            for i, result in enumerate(keyword_results)
        }
        
        # Collect all unique chunks
        all_chunks = {}
        for result in vector_results:
            all_chunks[result['id']] = result
        for result in keyword_results:
            if result['id'] not in all_chunks:
                all_chunks[result['id']] = result
        
        # Calculate RRF scores
        rrf_results = []
        for chunk_id, chunk in all_chunks.items():
            rrf_score = 0.0
            
            # Add vector rank score
            if chunk_id in vector_ranks:
                rrf_score += 1.0 / (k + vector_ranks[chunk_id])
            
            # Add keyword rank score
            if chunk_id in keyword_ranks:
                rrf_score += 1.0 / (k + keyword_ranks[chunk_id])
            
            result = chunk.copy()
            result['score'] = rrf_score
            result['retrieval_method'] = 'rrf'
            rrf_results.append(result)
        
        # Sort by RRF score and return top_k
        rrf_results.sort(key=lambda x: x['score'], reverse=True)
        return rrf_results[:top_k]
    
    def retrieve_with_context(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Retrieve chunks with conversation context.
        
        For multi-turn conversations, this reformulates the query using
        conversation history to improve retrieval.
        
        Args:
            query: Current user question
            conversation_history: Previous messages in conversation
            top_k: Number of chunks to return
            document_ids: Optional document filter
            
        Returns:
            Retrieved chunks
            
        Note:
            Currently just passes query through. In future, could:
            - Reformulate query based on context
            - Retrieve from multiple reformulations
            - Use conversation history to filter results
        """
        # For now, just use the original query
        # TODO: Implement query reformulation using conversation history
        return self.retrieve(
            query=query,
            top_k=top_k,
            document_ids=document_ids
        )
    
    def retrieve_multi_query(
        self,
        queries: List[str],
        top_k_per_query: int = 3,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Retrieve chunks for multiple query variations.
        
        Useful for query expansion or multi-perspective retrieval.
        
        Args:
            queries: List of query variations
            top_k_per_query: How many chunks to retrieve per query
            document_ids: Optional document filter
            
        Returns:
            Deduplicated list of chunks from all queries
        """
        all_chunks = []
        seen_ids = set()
        
        for query in queries:
            chunks = self.retrieve(
                query=query,
                top_k=top_k_per_query,
                document_ids=document_ids
            )
            
            # Deduplicate by chunk ID
            for chunk in chunks:
                chunk_id = chunk.get('id')
                if chunk_id and chunk_id not in seen_ids:
                    all_chunks.append(chunk)
                    seen_ids.add(chunk_id)
        
        # Sort by similarity (highest first)
        all_chunks.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        return all_chunks
    
    def _enrich_with_document_metadata(self, results: List[Dict]) -> List[Dict]:
        """
        Enrich chunk results with document metadata (filename, etc.).
        
        For chunks that don't have document_name in their metadata,
        fetch it from the documents table.
        
        Args:
            results: List of chunk results
            
        Returns:
            Results enriched with document metadata
        """
        if not results:
            return results
        
        try:
            # Collect document IDs that need metadata
            doc_ids_to_fetch = set()
            for result in results:
                metadata = result.get('metadata', {})
                # If document_name is missing, we need to fetch it
                if not metadata.get('document_name'):
                    doc_ids_to_fetch.add(result.get('document_id'))
            
            # Fetch document info from database
            doc_info_map = {}
            if doc_ids_to_fetch:
                db = get_supabase()
                doc_result = db.table('documents')\
                    .select('id, filename, file_type')\
                    .in_('id', list(doc_ids_to_fetch))\
                    .execute()
                
                for doc in doc_result.data:
                    doc_info_map[doc['id']] = {
                        'document_name': doc['filename'],
                        'file_type': doc.get('file_type', 'unknown')
                    }
            
            # Enrich results
            for result in results:
                metadata = result.get('metadata', {})
                doc_id = result.get('document_id')
                
                # Add document_name if missing
                if not metadata.get('document_name') and doc_id in doc_info_map:
                    metadata['document_name'] = doc_info_map[doc_id]['document_name']
                    metadata['file_type'] = doc_info_map[doc_id]['file_type']
                    result['metadata'] = metadata
            
            return results
            
        except Exception as e:
            # If enrichment fails, log but don't break the retrieval
            print(f"[WARNING] Failed to enrich results with document metadata: {e}")
            return results


# For backward compatibility with existing code that imports HybridRetriever
HybridRetriever = Retriever
