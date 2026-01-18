"""LLM-as-judge implementation using GPT-4."""
from typing import Dict, List, Optional
import json
from pydantic import BaseModel


class JudgmentSchema(BaseModel):
    """Schema for LLM judge output."""
    correctness: int
    completeness: int
    clarity: int
    citation_quality: int
    overall: int
    reasoning: str


class LLMJudge:
    """
    Use GPT-4 to evaluate answer quality.
    """
    
    def __init__(self, llm_provider):
        """
        Initialize LLM judge.
        
        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider
        self.judge_model = "gpt-4o"  # Use best model for judging
    
    async def evaluate_answer(
        self,
        question: str,
        generated_answer: str,
        ground_truth: str,
        sources: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Evaluate answer quality using LLM.
        
        Returns scores and reasoning for:
        - Correctness
        - Completeness
        - Clarity
        - Citation quality
        - Overall
        """
        # Build evaluation prompt
        prompt = self._build_judge_prompt(
            question,
            generated_answer,
            ground_truth,
            sources
        )
        
        # Get structured output from LLM
        try:
            # Use the generate method from LLMProvider
            messages = [
                {"role": "system", "content": "You are an expert evaluator. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.generate(
                messages=messages,
                temperature=0.0,
                max_tokens=500
            )
            
            # Extract JSON from response
            response_text = response if isinstance(response, str) else str(response)
            
            # Try to find JSON in the response
            try:
                # Look for JSON block
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    judgment = json.loads(json_str)
                    
                    # Validate required fields
                    required_fields = ['correctness', 'completeness', 'clarity', 'citation_quality', 'overall', 'reasoning']
                    if all(field in judgment for field in required_fields):
                        return judgment
            except Exception as parse_error:
                print(f"JSON parsing error: {parse_error}")
            
            # Return default scores if parsing fails
            return {
                'correctness': 3,
                'completeness': 3,
                'clarity': 3,
                'citation_quality': 3,
                'overall': 3,
                'reasoning': 'Unable to parse LLM judgment'
            }
        except Exception as e:
            print(f"Error in LLM judge: {e}")
            return {
                'correctness': 3,
                'completeness': 3,
                'clarity': 3,
                'citation_quality': 3,
                'overall': 3,
                'reasoning': f'Error: {str(e)}'
            }
    
    def _build_judge_prompt(
        self,
        question: str,
        generated_answer: str,
        ground_truth: str,
        sources: Optional[List[Dict]]
    ) -> str:
        """Build the judge evaluation prompt."""
        sources_str = ""
        if sources:
            sources_str = "\n\nSource Documents:\n" + "\n".join([
                f"[{i}] {s.get('content', '')[:200]}..."
                for i, s in enumerate(sources[:5])
            ])
        
        prompt = f"""You are an expert evaluator assessing the quality of AI-generated answers to financial questions.

**Question**: {question}

**Generated Answer**: 
{generated_answer}

**Reference Answer** (ground truth):
{ground_truth}
{sources_str}

**Evaluation Criteria**:

1. **Correctness** (1-5): Is the answer factually correct compared to the reference?
   - 5: Completely correct, all facts accurate
   - 4: Mostly correct, minor inaccuracies
   - 3: Partially correct, some significant errors
   - 2: Mostly incorrect
   - 1: Completely incorrect

2. **Completeness** (1-5): Does the answer address all aspects of the question?
   - 5: Fully complete, nothing missing
   - 4: Mostly complete, minor omissions
   - 3: Partially complete, missing some important points
   - 2: Significantly incomplete
   - 1: Barely addresses the question

3. **Clarity** (1-5): Is the answer clear, well-structured, and easy to understand?
   - 5: Exceptionally clear and well-organized
   - 4: Clear and understandable
   - 3: Somewhat clear but could be improved
   - 2: Confusing or poorly organized
   - 1: Very unclear

4. **Citation Quality** (1-5): Are sources properly cited?
   - 5: All claims cited with specific sources
   - 4: Most claims cited
   - 3: Some citations present
   - 2: Very few citations
   - 1: No citations

5. **Overall** (1-5): Overall quality considering all factors

**Return ONLY a JSON object** (no other text):
{{
    "correctness": 1-5,
    "completeness": 1-5,
    "clarity": 1-5,
    "citation_quality": 1-5,
    "overall": 1-5,
    "reasoning": "Brief explanation of the scores"
}}

Your evaluation:"""
        
        return prompt
    
    async def batch_evaluate(
        self,
        test_cases: List[Dict]
    ) -> List[Dict]:
        """
        Evaluate multiple test cases.
        
        Args:
            test_cases: List of {question, answer, ground_truth, sources}
        
        Returns:
            List of judgment dicts
        """
        results = []
        for case in test_cases:
            judgment = await self.evaluate_answer(
                question=case['question'],
                generated_answer=case['answer'],
                ground_truth=case['ground_truth'],
                sources=case.get('sources', [])
            )
            results.append(judgment)
        
        return results
    
    def aggregate_scores(self, judgments: List[Dict]) -> Dict:
        """Aggregate scores across multiple judgments."""
        if not judgments:
            return {}
        
        metrics = ['correctness', 'completeness', 'clarity', 'citation_quality', 'overall']
        
        aggregated = {}
        for metric in metrics:
            scores = [j[metric] for j in judgments if metric in j]
            if scores:
                aggregated[f'avg_{metric}'] = sum(scores) / len(scores)
                aggregated[f'min_{metric}'] = min(scores)
                aggregated[f'max_{metric}'] = max(scores)
        
        return aggregated
    
    # Backward compatibility
    async def judge(
        self,
        question: str,
        answer: str,
        ground_truth: str
    ) -> Dict:
        """Legacy method for backward compatibility."""
        return await self.evaluate_answer(question, answer, ground_truth)
