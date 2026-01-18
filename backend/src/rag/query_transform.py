"""
Query transformation strategies for improved retrieval.

Includes HyDE, multi-query generation, and query decomposition.
"""
from typing import List, Optional
from enum import Enum


class QueryStrategy(Enum):
    """Query transformation strategies."""
    NONE = "none"
    HYDE = "hyde"
    MULTI_QUERY = "multi_query"
    DECOMPOSITION = "decomposition"


class QueryTransformer:
    """
    Transform queries for better retrieval.
    
    Strategies:
    - HyDE: Generate hypothetical answer, retrieve documents similar to it
    - Multi-query: Generate query variations for broader coverage
    - Decomposition: Break complex questions into simpler sub-questions
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize query transformer.
        
        Args:
            llm_provider: LLM provider for query generation (optional)
        """
        self.llm = llm_provider
    
    async def transform(
        self,
        query: str,
        strategy: QueryStrategy = QueryStrategy.NONE
    ) -> List[str]:
        """
        Transform query based on strategy.
        
        Args:
            query: Original query
            strategy: Transformation strategy to use
        
        Returns:
            List of queries to retrieve for (includes original)
        """
        if strategy == QueryStrategy.NONE:
            return [query]
        elif strategy == QueryStrategy.HYDE:
            return await self.apply_hyde(query)
        elif strategy == QueryStrategy.MULTI_QUERY:
            return await self.generate_multi_query(query)
        elif strategy == QueryStrategy.DECOMPOSITION:
            return await self.decompose_query(query)
        else:
            return [query]
    
    async def apply_hyde(self, query: str) -> List[str]:
        """
        Hypothetical Document Embeddings (HyDE).
        
        Generate a hypothetical answer, then retrieve documents similar to it.
        Works well for conceptual questions.
        
        Args:
            query: Original query
        
        Returns:
            [original_query, hypothetical_document]
        """
        if not self.llm:
            return [query]
        
        try:
            prompt = f"""Given this question: "{query}"

Write a detailed hypothetical paragraph that would answer this question,
as it might appear in a financial document. Include:
- Specific details and context
- Relevant numbers and metrics  
- Technical/financial terminology
- The style of a professional financial document

Write ONLY the hypothetical answer paragraph, nothing else.

Hypothetical answer:"""
            
            hypothetical_doc = await self._generate_text(prompt)
            
            # Return both original query and hypothetical doc
            return [query, hypothetical_doc.strip()]
            
        except Exception as e:
            print(f"HyDE generation failed: {e}")
            return [query]
    
    async def generate_multi_query(self, query: str) -> List[str]:
        """
        Generate multiple query variations.
        
        Improves recall by capturing different phrasings of the same question.
        
        Args:
            query: Original query
        
        Returns:
            [original_query, variation1, variation2, variation3]
        """
        if not self.llm:
            return [query]
        
        try:
            prompt = f"""Generate 3 alternative phrasings of this query that preserve 
the intent but use different words or perspectives:

Original query: "{query}"

Focus on financial/business terminology variations.

Format your response as a simple list with one query per line:
1. [first variation]
2. [second variation]
3. [third variation]

Alternative queries:"""
            
            response = await self._generate_text(prompt)
            
            # Parse response to extract queries
            variations = self._parse_list_response(response)
            
            # Return original + variations
            return [query] + variations[:3]
            
        except Exception as e:
            print(f"Multi-query generation failed: {e}")
            return [query]
    
    async def decompose_query(self, query: str) -> List[str]:
        """
        Decompose complex query into simpler sub-questions.
        
        Works well for multi-part or comparative questions.
        
        Args:
            query: Original complex query
        
        Returns:
            List of simpler sub-questions
        """
        if not self.llm:
            return [query]
        
        try:
            prompt = f"""Break this complex question into 2-4 simpler, independent sub-questions:

Complex query: "{query}"

Each sub-question should:
- Be answerable independently
- Cover one aspect of the original question
- Be specific and clear

Format your response as a simple list with one question per line:
1. [first sub-question]
2. [second sub-question]
3. [third sub-question]

Sub-questions:"""
            
            response = await self._generate_text(prompt)
            
            # Parse response to extract sub-questions
            sub_queries = self._parse_list_response(response)
            
            return sub_queries[:4]  # Return up to 4 sub-questions
            
        except Exception as e:
            print(f"Query decomposition failed: {e}")
            return [query]
    
    def auto_select_strategy(self, query: str) -> QueryStrategy:
        """
        Automatically select best transformation strategy based on query.
        
        Heuristics:
        - "What is...", "Explain..." → HyDE
        - Comparative ("compare", "vs") → Decomposition
        - Short/ambiguous → Multi-query
        - Simple factual → None
        
        Args:
            query: Query to analyze
        
        Returns:
            Recommended strategy
        """
        query_lower = query.lower()
        
        # Decomposition for complex/comparative queries
        comparative_words = ['compare', 'vs', 'versus', 'difference between', 'and']
        if any(word in query_lower for word in comparative_words):
            return QueryStrategy.DECOMPOSITION
        
        # HyDE for conceptual questions
        conceptual_starts = ['what is', 'explain', 'describe', 'how does', 'why']
        if any(query_lower.startswith(phrase) for phrase in conceptual_starts):
            return QueryStrategy.HYDE
        
        # Multi-query for short/potentially ambiguous queries
        if len(query_lower.split()) <= 5:
            return QueryStrategy.MULTI_QUERY
        
        # Default: no transformation for simple factual queries
        return QueryStrategy.NONE
    
    async def _generate_text(self, prompt: str) -> str:
        """Generate text using LLM provider."""
        if not self.llm:
            raise ValueError("LLM provider not configured")
        
        # Use LLM provider's generate method
        messages = [{"role": "user", "content": prompt}]
        return self.llm.generate(messages, temperature=0.7, max_tokens=500)
    
    def _parse_list_response(self, response: str) -> List[str]:
        """
        Parse numbered list from LLM response.
        
        Handles formats like:
        1. First item
        2. Second item
        - First item
        - Second item
        """
        items = []
        
        # Split by newlines
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Remove numbering (1., 2., etc.) or bullets (-, *)
            line = line.lstrip('0123456789.-*• ')
            
            # Remove brackets if present [item]
            line = line.strip('[]')
            
            if line:
                items.append(line)
        
        return items
