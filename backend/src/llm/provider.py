"""
LLM Provider for OpenAI.

Handles text generation for RAG responses with proper context management.
"""
from typing import List, Dict, Optional, Generator, AsyncGenerator
import openai
from src.utils.config import settings


class LLMProvider:
    """
    OpenAI LLM provider for generating answers from retrieved context.
    
    Why OpenAI?
    - GPT-4o: Best balance of speed, quality, and cost
    - Strong reasoning for financial analysis
    - Excellent at following citation instructions
    
    Token Limits:
    - GPT-4o: 128k context, 16k output
    - GPT-4o-mini: 128k context, 16k output (cheaper, faster)
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize LLM provider.
        
        Args:
            api_key: OpenAI API key (uses settings.openai_api_key if not provided)
            model: Model to use (default: gpt-4o-mini for cost efficiency)
                   Options: gpt-4o, gpt-4o-mini, gpt-4-turbo
        """
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY in .env file."
            )
        
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Track usage for monitoring
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
    
    def generate(
        self, 
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        Generate text completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     [{"role": "system", "content": "..."}, 
                      {"role": "user", "content": "..."}]
            temperature: Randomness (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in response
            stream: Whether to stream response (for real-time UI)
            
        Returns:
            Generated text content
            
        Note:
            - Temperature 0.0 is best for factual financial queries
            - Higher temperature (0.3-0.7) for creative analysis
        """
        try:
            if stream:
                return self._generate_stream(messages, temperature, max_tokens)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Track usage
            self._track_usage(response.usage)
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")
    
    def _generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Generator[str, None, None]:
        """
        Generate streaming completion (for real-time responses).
        
        Yields chunks of text as they're generated.
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise RuntimeError(f"LLM streaming failed: {str(e)}")
    
    def generate_with_context(
        self,
        query: str,
        context_chunks: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict:
        """
        Generate answer using retrieved context chunks.
        
        This is the main method used by RAG pipeline.
        
        Args:
            query: User's question
            context_chunks: Retrieved document chunks with content and metadata
            system_prompt: Optional system instructions
            temperature: Response randomness
            
        Returns:
            Dict with 'answer', 'sources', and 'usage' info
        """
        # Build system prompt
        if system_prompt is None:
            system_prompt = """You are a financial research assistant. Answer questions based on the provided context from financial documents.

Rules:
1. Only use information from the provided context
2. Cite sources using [Source X] notation
3. If the context doesn't contain enough information, say so
4. Be precise with numbers and dates
5. Provide concise, accurate answers"""
        
        # Format context
        context_text = self._format_context(context_chunks)
        
        # Build user message
        user_message = f"""Context from documents:

{context_text}

Question: {query}

Please provide a detailed answer based on the context above."""
        
        # Generate response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        answer = self.generate(
            messages=messages,
            temperature=temperature
        )
        
        # Extract sources used
        sources = self._extract_sources(context_chunks)
        
        return {
            "answer": answer,
            "sources": sources,
            "usage": {
                "prompt_tokens": self.total_prompt_tokens,
                "completion_tokens": self.total_completion_tokens,
                "model": self.model
            }
        }
    
    async def generate_with_context_stream(
        self,
        query: str,
        context_chunks: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> AsyncGenerator[Dict, None]:
        """
        Generate answer using retrieved context chunks with streaming.
        
        Yields tokens as they are generated for real-time UI updates.
        
        Args:
            query: User's question
            context_chunks: Retrieved document chunks with content and metadata
            system_prompt: Optional system instructions
            temperature: Response randomness
            
        Yields:
            Dict events:
            - {'type': 'token', 'content': str} - Individual token
            - {'type': 'sources', 'sources': List[Dict]} - Source documents
            - {'type': 'done', 'full_answer': str} - Complete answer
        """
        # Build system prompt
        if system_prompt is None:
            system_prompt = """You are a financial research assistant. Answer questions based on the provided context from financial documents.

Rules:
1. Only use information from the provided context
2. Cite sources using [Source X] notation
3. If the context doesn't contain enough information, say so
4. Be precise with numbers and dates
5. Provide concise, accurate answers"""
        
        # Format context
        context_text = self._format_context(context_chunks)
        
        # Build user message
        user_message = f"""Context from documents:

{context_text}

Question: {query}

Please provide a detailed answer based on the context above."""
        
        # Generate response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Extract and yield sources first
        sources = self._extract_sources(context_chunks)
        yield {
            "type": "sources",
            "sources": sources
        }
        
        # Stream tokens
        full_answer = ""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_answer += token
                    yield {
                        "type": "token",
                        "content": token
                    }
            
            # Yield completion event
            yield {
                "type": "done",
                "full_answer": full_answer,
                "sources": sources
            }
                    
        except Exception as e:
            yield {
                "type": "error",
                "message": f"LLM streaming failed: {str(e)}"
            }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into context string.
        
        Example output:
        [Source 1] From document "Apple Q4 2023":
        Apple revenue was $383B...
        
        [Source 2] From document "Tesla Q4 2023":
        Tesla delivered 484,507 vehicles...
        """
        formatted = []
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            # Get document info from metadata if available
            doc_info = metadata.get('document_name', 'document')
            
            formatted.append(f"[Source {i}] From {doc_info}:\n{content}")
        
        return "\n\n".join(formatted)
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract source metadata from chunks."""
        sources = []
        
        for i, chunk in enumerate(chunks, 1):
            sources.append({
                "source_number": i,
                "chunk_id": chunk.get('id'),
                "document_id": chunk.get('document_id'),
                "content": chunk.get('content', '')[:200] + "...",  # Preview
                "metadata": chunk.get('metadata', {}),
                "similarity": chunk.get('similarity', 0.0)
            })
        
        return sources
    
    def _track_usage(self, usage):
        """Track token usage for monitoring and cost estimation."""
        if usage:
            self.total_prompt_tokens += usage.prompt_tokens
            self.total_completion_tokens += usage.completion_tokens
    
    def get_usage_stats(self) -> Dict:
        """
        Get usage statistics and cost estimation.
        
        Returns:
            Dict with token counts and estimated costs
        """
        # Pricing for GPT-4o-mini (as of 2024)
        # $0.150 per 1M input tokens, $0.600 per 1M output tokens
        prompt_cost = (self.total_prompt_tokens / 1_000_000) * 0.150
        completion_cost = (self.total_completion_tokens / 1_000_000) * 0.600
        
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "estimated_cost": prompt_cost + completion_cost,
            "model": self.model
        }
