"""RAGAS metrics integration."""
from typing import Dict, List
import time
import os
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
from datasets import Dataset
from langchain_openai import ChatOpenAI


class RAGASEvaluator:
    """Evaluate RAG system using RAGAS metrics."""
    
    def __init__(self, rag_pipeline, llm_provider):
        """
        Initialize RAGAS evaluator.
        
        Args:
            rag_pipeline: RAG pipeline instance
            llm_provider: LLM provider for evaluation
        """
        self.rag = rag_pipeline
        self.llm = llm_provider
        
        # Set OpenAI API key for RAGAS
        if hasattr(llm_provider, 'api_key') and llm_provider.api_key:
            os.environ['OPENAI_API_KEY'] = llm_provider.api_key
        
        # Initialize RAGAS LLM (uses OpenAI)
        self.ragas_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=llm_provider.api_key if hasattr(llm_provider, 'api_key') else None
        )
        
        # RAGAS metrics
        self.metrics = [
            faithfulness,        # Answer grounded in context
            answer_relevancy,    # Answer addresses question
            context_precision,   # Relevant docs ranked high
            context_recall,      # All necessary docs retrieved
            answer_correctness   # Factually correct answer
        ]
    
    async def evaluate_test_set(self, test_cases: List[Dict]) -> Dict:
        """
        Evaluate RAG system on a test set.
        
        Args:
            test_cases: List of test cases with format:
                {
                    'question': str,
                    'expected_answer': str,
                    'document_ids': List[str]  # Optional
                }
        
        Returns:
            Dict with RAGAS scores and detailed results
        """
        # Prepare data for RAGAS
        data = {
            'question': [],
            'answer': [],
            'contexts': [],
            'ground_truth': []
        }
        
        # Run system on each test case
        for case in test_cases:
            # Query the RAG system
            result = self.rag.query(
                question=case['question'],
                document_ids=case.get('document_ids')
            )
            
            # Collect data
            data['question'].append(case['question'])
            data['answer'].append(result.answer if hasattr(result, 'answer') else result.get('answer', ''))
            sources = result.sources if hasattr(result, 'sources') else result.get('sources', [])
            data['contexts'].append([s.get('content', '') if isinstance(s, dict) else str(s) for s in sources])
            data['ground_truth'].append(case['expected_answer'])
        
        # Convert to RAGAS dataset
        dataset = Dataset.from_dict(data)
        
        # Run RAGAS evaluation with configured LLM
        ragas_results = evaluate(
            dataset,
            metrics=self.metrics,
            llm=self.ragas_llm,
        )
        
        # Format results - RAGAS returns per-sample scores, calculate means
        def get_mean_score(value):
            """Get mean score from RAGAS result (handles both list and scalar)."""
            if isinstance(value, (list, tuple)):
                return sum(value) / len(value) if len(value) > 0 else 0.0
            return float(value)
        
        results = {
            'overall_scores': {
                'faithfulness': get_mean_score(ragas_results['faithfulness']),
                'answer_relevancy': get_mean_score(ragas_results['answer_relevancy']),
                'context_precision': get_mean_score(ragas_results['context_precision']),
                'context_recall': get_mean_score(ragas_results['context_recall']),
                'answer_correctness': get_mean_score(ragas_results['answer_correctness'])
            },
            'per_question_results': self._format_per_question_results(ragas_results, data),
            'num_questions': len(test_cases),
            'timestamp': time.time()
        }
        
        return results
    
    def _format_per_question_results(self, ragas_results, data) -> List[Dict]:
        """Format detailed per-question results."""
        def get_score_at_index(value, i):
            """Get score at index (handles both list and scalar)."""
            if isinstance(value, (list, tuple)):
                return float(value[i]) if i < len(value) else 0.0
            return float(value)
        
        per_question = []
        for i in range(len(data['question'])):
            per_question.append({
                'question': data['question'][i],
                'answer': data['answer'][i],
                'ground_truth': data['ground_truth'][i],
                'scores': {
                    'faithfulness': get_score_at_index(ragas_results['faithfulness'], i),
                    'answer_relevancy': get_score_at_index(ragas_results['answer_relevancy'], i),
                    'context_precision': get_score_at_index(ragas_results['context_precision'], i),
                    'context_recall': get_score_at_index(ragas_results['context_recall'], i),
                    'answer_correctness': get_score_at_index(ragas_results['answer_correctness'], i)
                }
            })
        
        return per_question
    
    async def evaluate_single_query(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str
    ) -> Dict:
        """
        Evaluate a single query-answer pair.
        Useful for real-time evaluation during demo.
        """
        dataset = Dataset.from_dict({
            'question': [question],
            'answer': [answer],
            'contexts': [contexts],
            'ground_truth': [ground_truth]
        })
        
        results = evaluate(dataset, metrics=self.metrics, llm=self.ragas_llm)
        
        # Handle both list and scalar results
        def get_score(value):
            if isinstance(value, (list, tuple)):
                return float(value[0]) if len(value) > 0 else 0.0
            return float(value)
        
        return {
            'faithfulness': get_score(results['faithfulness']),
            'answer_relevancy': get_score(results['answer_relevancy']),
            'context_precision': get_score(results['context_precision']),
            'context_recall': get_score(results['context_recall']),
            'answer_correctness': get_score(results['answer_correctness'])
        }
    
    # Backward compatibility
    async def evaluate(self, test_cases: List[Dict]) -> Dict:
        """Legacy method for backward compatibility."""
        result = await self.evaluate_test_set(test_cases)
        return result['overall_scores']
