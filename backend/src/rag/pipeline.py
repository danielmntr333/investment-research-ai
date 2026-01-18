"""
Main RAG orchestration pipeline.

Combines retrieval and generation to answer questions from documents.
Supports advanced features like hybrid search, query transformation, and reranking.
"""
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass
import time
from src.rag.retrieval import Retriever
from src.rag.embeddings import EmbeddingService
from src.rag.query_transform import QueryTransformer, QueryStrategy
from src.rag.reranking import CohereReranker
from src.llm.provider import LLMProvider
from src.db.vector_store import VectorStore


@dataclass
class RAGResult:
    """Result from RAG pipeline."""
    answer: str
    sources: List[Dict]
    metadata: Dict


class RAGPipeline:
    """
    Advanced RAG pipeline with query transformation, hybrid search, and reranking.
    
    Architecture:
        User Query
            ↓
        Query Transformation (HyDE/Multi-query/Decomposition)
            ↓
        Hybrid Retrieval (Vector + Keyword + RRF)
            ↓
        Reranking (Cohere)
            ↓
        Retrieved Chunks (with sources)
            ↓
        LLM Generation (with context)
            ↓
        Answer + Citations
    
    Example:
        pipeline = RAGPipeline()
        result = pipeline.query(
            "What was Tesla's revenue in Q4?",
            strategy='hybrid',
            use_reranking=True
        )
    """
    
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        llm_provider: Optional[LLMProvider] = None,
        query_transformer: Optional[QueryTransformer] = None,
        reranker: Optional[CohereReranker] = None,
        top_k: int = 5,
        temperature: float = 0.0
    ):
        """
        Initialize advanced RAG pipeline.
        
        Args:
            retriever: Document retriever (creates default if not provided)
            llm_provider: LLM for answer generation (creates default if not provided)
            query_transformer: Query transformer for HyDE/multi-query (optional)
            reranker: Reranker for precision boost (optional)
            top_k: Number of chunks to retrieve (default: 5)
            temperature: LLM temperature for answers (default: 0.0 for factual)
        """
        # Initialize LLM first (needed by other components)
        self.llm_provider = llm_provider or LLMProvider()
        
        # Initialize components
        self.retriever = retriever or Retriever(reranker=reranker)
        self.query_transformer = query_transformer or QueryTransformer(self.llm_provider)
        self.reranker = reranker
        self.top_k = top_k
        self.temperature = temperature
    
    def query(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        min_similarity: float = 0.3,
        system_prompt: Optional[str] = None,
        strategy: str = 'hybrid',
        use_query_transform: bool = False,
        use_reranking: bool = False,
        query_transform_strategy: Optional[QueryStrategy] = None
    ) -> Dict:
        """
        Execute advanced RAG query pipeline.
        
        Args:
            question: User's question
            document_ids: Optional list of document IDs to search within
            top_k: Number of chunks to retrieve (overrides default)
            min_similarity: Minimum similarity threshold (0-1)
            system_prompt: Optional custom system prompt for LLM
            strategy: Retrieval strategy ('vector', 'keyword', 'hybrid', 'rrf')
            use_query_transform: Enable query transformation
            use_reranking: Enable reranking
            query_transform_strategy: Specific transform strategy (auto if None)
            
        Returns:
            Dict with:
                - answer: Generated answer text
                - sources: List of source chunks used
                - metadata: Additional info (tokens, retrieval stats, etc.)
                
        Process:
            1. Transform query (if enabled)
            2. Retrieve relevant chunks using specified strategy
            3. Rerank results (if enabled)
            4. Generate answer using LLM with retrieved context
            5. Return answer with citations
        """
        try:
            start_time = time.time()
            k = top_k or self.top_k
            
            # Step 1: Query transformation (if enabled)
            transformed_queries = [question]
            if use_query_transform:
                # Auto-select strategy if not provided
                if query_transform_strategy is None:
                    query_transform_strategy = self.query_transformer.auto_select_strategy(question)
                
                # Transform query (sync wrapper for async method)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                transformed_queries = loop.run_until_complete(
                    self.query_transformer.transform(question, query_transform_strategy)
                )
            
            # Step 2: Retrieve for all transformed queries
            all_chunks = []
            for query in transformed_queries:
                chunks = self.retriever.retrieve(
                    query=query,
                    top_k=k * 2 if use_reranking else k,  # Get more if reranking
                    document_ids=document_ids,
                    min_similarity=min_similarity,
                    strategy=strategy,
                    use_reranking=False  # Rerank once at the end
                )
                all_chunks.extend(chunks)
            
            # Deduplicate chunks by ID
            seen_ids = set()
            unique_chunks = []
            for chunk in all_chunks:
                chunk_id = chunk.get('id')
                if chunk_id and chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    unique_chunks.append(chunk)
            
            # Sort by score and take top candidates
            unique_chunks.sort(
                key=lambda x: x.get('score', x.get('similarity', 0)), 
                reverse=True
            )
            retrieved_chunks = unique_chunks[:k * 2 if use_reranking else k]
            
            # Step 3: Rerank (if enabled)
            if use_reranking and self.reranker and len(retrieved_chunks) > k:
                retrieved_chunks = self.reranker.rerank(
                    question, 
                    retrieved_chunks, 
                    k
                )
            else:
                retrieved_chunks = retrieved_chunks[:k]
            
            # Step 4: Check if we have results
            if not retrieved_chunks:
                return {
                    "answer": "I couldn't find relevant information in the documents to answer your question. Please try rephrasing or check if the relevant documents have been uploaded.",
                    "sources": [],
                    "metadata": {
                        "retrieved_chunks": 0,
                        "status": "no_results",
                        "processing_time": time.time() - start_time
                    }
                }
            
            # Step 5: Generate answer using LLM
            generation_result = self.llm_provider.generate_with_context(
                query=question,
                context_chunks=retrieved_chunks,
                system_prompt=system_prompt,
                temperature=self.temperature
            )
            
            # Step 6: Compile final result
            return {
                "answer": generation_result["answer"],
                "sources": generation_result["sources"],
                "metadata": {
                    "retrieved_chunks": len(retrieved_chunks),
                    "unique_chunks": len(unique_chunks),
                    "transformed_queries": transformed_queries,
                    "retrieval_strategy": strategy,
                    "used_query_transform": use_query_transform,
                    "used_reranking": use_reranking and self.reranker is not None,
                    "avg_score": sum(c.get('score', c.get('similarity', 0)) for c in retrieved_chunks) / len(retrieved_chunks) if retrieved_chunks else 0,
                    "top_score": retrieved_chunks[0].get('score', retrieved_chunks[0].get('similarity', 0)) if retrieved_chunks else 0,
                    "model": self.llm_provider.model,
                    "usage": generation_result.get("usage", {}),
                    "processing_time": time.time() - start_time,
                    "status": "success"
                }
            }
            
        except Exception as e:
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": [],
                "metadata": {
                    "retrieved_chunks": 0,
                    "status": "error",
                    "error": str(e),
                    "processing_time": time.time() - start_time if 'start_time' in locals() else 0
                }
            }
    
    async def query_stream(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        min_similarity: float = 0.3,
        system_prompt: Optional[str] = None,
        strategy: str = 'hybrid',
        use_query_transform: bool = False,
        use_reranking: bool = False,
        query_transform_strategy: Optional[QueryStrategy] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Execute RAG query pipeline with streaming for real-time updates.
        
        Yields events at each stage:
        - Pipeline progress (query transform, retrieval, reranking)
        - Token-by-token generation
        - Final result with sources
        
        Args:
            Same as query() method
            
        Yields:
            Dict events with different types:
            - {'type': 'step', 'step': str, 'status': 'start'|'complete', 'data': Dict}
            - {'type': 'token', 'content': str}
            - {'type': 'sources', 'sources': List[Dict]}
            - {'type': 'done', 'answer': str, 'sources': List, 'metadata': Dict}
            - {'type': 'error', 'message': str}
        """
        try:
            start_time = time.time()
            k = top_k or self.top_k
            
            # Step 1: Query transformation (if enabled)
            if use_query_transform:
                yield {
                    "type": "step",
                    "step": "query_transform",
                    "status": "start",
                    "message": "Analyzing your question..."
                }
                
                if query_transform_strategy is None:
                    query_transform_strategy = self.query_transformer.auto_select_strategy(question)
                
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                transformed_queries = loop.run_until_complete(
                    self.query_transformer.transform(question, query_transform_strategy)
                )
                
                yield {
                    "type": "step",
                    "step": "query_transform",
                    "status": "complete",
                    "data": {
                        "queries": transformed_queries,
                        "strategy": query_transform_strategy
                    }
                }
            else:
                transformed_queries = [question]
            
            # Step 2: Retrieval
            yield {
                "type": "step",
                "step": "retrieval",
                "status": "start",
                "message": "Searching through documents..."
            }
            
            all_chunks = []
            for query in transformed_queries:
                chunks = self.retriever.retrieve(
                    query=query,
                    top_k=k * 2 if use_reranking else k,
                    document_ids=document_ids,
                    min_similarity=min_similarity,
                    strategy=strategy,
                    use_reranking=False
                )
                all_chunks.extend(chunks)
            
            # Deduplicate chunks
            seen_ids = set()
            unique_chunks = []
            for chunk in all_chunks:
                chunk_id = chunk.get('id')
                if chunk_id and chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    unique_chunks.append(chunk)
            
            unique_chunks.sort(
                key=lambda x: x.get('score', x.get('similarity', 0)), 
                reverse=True
            )
            retrieved_chunks = unique_chunks[:k * 2 if use_reranking else k]
            
            yield {
                "type": "step",
                "step": "retrieval",
                "status": "complete",
                "data": {
                    "chunks_found": len(retrieved_chunks),
                    "strategy": strategy
                }
            }
            
            # Step 3: Reranking (if enabled)
            if use_reranking and self.reranker and len(retrieved_chunks) > k:
                yield {
                    "type": "step",
                    "step": "reranking",
                    "status": "start",
                    "message": "Prioritizing most relevant information..."
                }
                
                retrieved_chunks = self.reranker.rerank(question, retrieved_chunks, k)
                
                yield {
                    "type": "step",
                    "step": "reranking",
                    "status": "complete",
                    "data": {"final_chunks": len(retrieved_chunks)}
                }
            else:
                retrieved_chunks = retrieved_chunks[:k]
            
            # Step 4: Check if we have results
            if not retrieved_chunks:
                yield {
                    "type": "error",
                    "message": "No relevant information found in documents"
                }
                return
            
            # Step 5: Generate answer with streaming
            yield {
                "type": "step",
                "step": "generation",
                "status": "start",
                "message": "Generating answer..."
            }
            
            full_answer = ""
            sources = []
            
            async for event in self.llm_provider.generate_with_context_stream(
                query=question,
                context_chunks=retrieved_chunks,
                system_prompt=system_prompt,
                temperature=self.temperature
            ):
                if event['type'] == 'token':
                    full_answer += event['content']
                    yield event
                elif event['type'] == 'sources':
                    sources = event['sources']
                    yield event
                elif event['type'] == 'done':
                    full_answer = event['full_answer']
                    sources = event['sources']
                elif event['type'] == 'error':
                    yield event
                    return
            
            # Step 6: Send final result
            processing_time = time.time() - start_time
            
            yield {
                "type": "done",
                "answer": full_answer,
                "sources": sources,
                "metadata": {
                    "retrieved_chunks": len(retrieved_chunks),
                    "unique_chunks": len(unique_chunks),
                    "transformed_queries": transformed_queries,
                    "retrieval_strategy": strategy,
                    "used_query_transform": use_query_transform,
                    "used_reranking": use_reranking and self.reranker is not None,
                    "model": self.llm_provider.model,
                    "processing_time": processing_time,
                    "status": "success"
                }
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "message": f"Pipeline error: {str(e)}"
            }
    
    def query_with_conversation(
        self,
        question: str,
        conversation_history: List[Dict],
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None
    ) -> Dict:
        """
        Execute RAG query with conversation context.
        
        For multi-turn conversations where context from previous messages
        is important.
        
        Args:
            question: Current user question
            conversation_history: Previous messages
                [{"role": "user", "content": "..."}, 
                 {"role": "assistant", "content": "..."}]
            document_ids: Optional document filter
            top_k: Number of chunks to retrieve
            
        Returns:
            Same format as query()
            
        Note:
            Currently uses the same retrieval as single-turn.
            Future: Implement query reformulation based on conversation history.
        """
        # For now, just pass through to regular query
        # TODO: Implement conversation-aware retrieval
        return self.query(
            question=question,
            document_ids=document_ids,
            top_k=top_k
        )
    
    def batch_query(
        self,
        questions: List[str],
        document_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Process multiple queries in batch.
        
        Useful for evaluation or processing multiple questions at once.
        
        Args:
            questions: List of questions to answer
            document_ids: Optional document filter
            
        Returns:
            List of results (one per question)
        """
        results = []
        
        for question in questions:
            result = self.query(
                question=question,
                document_ids=document_ids
            )
            results.append(result)
        
        return results
    
    def get_usage_stats(self) -> Dict:
        """
        Get usage statistics for the pipeline.
        
        Returns:
            Token usage and cost estimates
        """
        return self.llm_provider.get_usage_stats()
    
    def get_relevant_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
        strategy: str = 'hybrid'
    ) -> List[Dict]:
        """
        Lightweight method to get relevant context without generating answer.
        
        Useful for agents that need context for reasoning.
        
        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            document_ids: Optional document filter
            strategy: Retrieval strategy
        
        Returns:
            List of relevant chunks with metadata
        """
        k = top_k or self.top_k
        
        chunks = self.retriever.retrieve(
            query=query,
            top_k=k,
            document_ids=document_ids,
            strategy=strategy
        )
        
        return chunks
