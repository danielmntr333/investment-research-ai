"""
Cohere reranker integration for precision boost.

Reranking improves precision by reordering retrieved documents
based on cross-encoder models trained specifically for relevance ranking.
"""
from typing import List, Dict, Optional
import os


class CohereReranker:
    """
    Rerank retrieved documents using Cohere's rerank API.
    
    Why rerank?
    - Initial retrieval optimizes for recall (get all relevant docs)
    - Reranking optimizes for precision (get most relevant at top)
    - Cohere's models are trained specifically for relevance ranking
    - Can significantly improve answer quality
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "rerank-english-v3.0"):
        """
        Initialize Cohere reranker.
        
        Args:
            api_key: Cohere API key (uses COHERE_API_KEY env var if not provided)
            model: Reranking model to use
        """
        self.api_key = api_key or os.getenv('COHERE_API_KEY')
        self.model = model
        
        # Lazy import and initialization
        self._client = None
    
    @property
    def client(self):
        """Lazy load Cohere client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Cohere API key not found. Set COHERE_API_KEY environment variable."
                )
            
            try:
                import cohere
                self._client = cohere.Client(self.api_key)
            except ImportError:
                raise ImportError(
                    "Cohere package not installed. Install with: pip install cohere"
                )
        
        return self._client
    
    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 10,
        return_documents: bool = True
    ) -> List[Dict]:
        """
        Rerank documents using Cohere.
        
        Args:
            query: Search query
            documents: Initial retrieved documents (dicts with 'content' key)
            top_k: Number of top documents to return
            return_documents: Whether to return full document objects
        
        Returns:
            Reranked documents with updated scores
        """
        if len(documents) <= top_k:
            return documents
        
        try:
            # Extract text content from documents
            texts = [doc.get('content', '') for doc in documents]
            
            # Call Cohere rerank API
            response = self.client.rerank(
                query=query,
                documents=texts,
                top_n=top_k,
                model=self.model,
                return_documents=return_documents
            )
            
            # Map back to original documents with new scores
            reranked = []
            for result in response.results:
                original_doc = documents[result.index].copy()
                
                # Update score with reranking relevance score
                original_doc['score'] = result.relevance_score
                original_doc['rerank_score'] = result.relevance_score
                original_doc['original_rank'] = result.index
                original_doc['retrieval_method'] = 'reranked'
                
                reranked.append(original_doc)
            
            return reranked
            
        except Exception as e:
            # If reranking fails, log and return original results
            print(f"Reranking failed: {e}. Returning original results.")
            return documents[:top_k]


# Backward compatibility alias
class Reranker(CohereReranker):
    """Alias for CohereReranker for backward compatibility."""
    pass
