"""Evaluation pipeline orchestrator."""
from typing import Dict, List
import asyncio
import json


class EvaluationPipeline:
    """
    Orchestrate all evaluation components.
    """
    
    def __init__(
        self,
        rag_pipeline,
        db_client,
        llm_provider
    ):
        """
        Initialize evaluation pipeline.
        
        Args:
            rag_pipeline: RAG pipeline instance
            db_client: Database client
            llm_provider: LLM provider
        """
        from .ragas_eval import RAGASEvaluator
        from .custom_metrics import FinancialMetrics
        from .llm_judge import LLMJudge
        from .golden_set import GoldenDataset
        from .regression import RegressionTestSuite
        
        self.rag = rag_pipeline
        self.db = db_client
        self.llm = llm_provider
        
        # Initialize evaluators
        self.ragas = RAGASEvaluator(rag_pipeline, llm_provider)
        self.custom = FinancialMetrics()
        self.judge = LLMJudge(llm_provider)
        self.golden = GoldenDataset()
        self.regression = RegressionTestSuite(
            rag_pipeline, self.golden, self.ragas,
            self.custom, self.judge, db_client
        )
    
    async def evaluate_single_query(
        self,
        question: str,
        answer: str,
        ground_truth: str,
        sources: List[Dict]
    ) -> Dict:
        """
        Comprehensive evaluation of a single query.
        
        Returns all metrics for immediate feedback.
        
        Args:
            question: Question text
            answer: Generated answer
            ground_truth: Expected answer
            sources: List of source documents
        
        Returns:
            Dict with all evaluation metrics
        """
        # Run all evaluations in parallel
        ragas_task = self.ragas.evaluate_single_query(
            question, answer,
            [s.get('content', '') if isinstance(s, dict) else str(s) for s in sources],
            ground_truth
        )
        
        custom_task = asyncio.create_task(
            self._evaluate_custom_single(answer, ground_truth)
        )
        
        judge_task = self.judge.evaluate_answer(
            question, answer, ground_truth, sources
        )
        
        # Wait for all
        ragas_scores, custom_scores, judge_scores = await asyncio.gather(
            ragas_task, custom_task, judge_task
        )
        
        return {
            'ragas': ragas_scores,
            'custom': custom_scores,
            'judge': judge_scores,
            'overall_score': self._calculate_overall_score(
                ragas_scores, custom_scores, judge_scores
            )
        }
    
    async def _evaluate_custom_single(
        self,
        answer: str,
        ground_truth: str
    ) -> Dict:
        """Evaluate custom metrics for single answer."""
        return self.custom.comprehensive_score(answer, ground_truth)
    
    def _calculate_overall_score(
        self,
        ragas: Dict,
        custom: Dict,
        judge: Dict
    ) -> float:
        """
        Calculate weighted overall score.
        
        Weights:
        - RAGAS: 40%
        - Custom: 35%
        - Judge: 25%
        """
        # Average RAGAS metrics
        ragas_avg = sum(ragas.values()) / len(ragas) if ragas else 0
        
        # Custom overall
        custom_score = custom.get('overall_score', 0)
        
        # Judge overall (normalize from 1-5 to 0-1)
        judge_score = judge.get('overall', 3) / 5.0
        
        overall = (
            0.40 * ragas_avg +
            0.35 * custom_score +
            0.25 * judge_score
        )
        
        return overall
    
    async def run_full_evaluation(self) -> Dict:
        """
        Run complete evaluation suite.
        
        This is the main method to call for comprehensive evaluation.
        """
        result = await self.regression.run_full_suite()
        return result
    
    async def get_evaluation_history(self, limit: int = 10) -> List[Dict]:
        """
        Get historical evaluation results.
        
        Args:
            limit: Number of results to return
        
        Returns:
            List of evaluation results
        """
        try:
            results = await self.db.table('evaluation_runs')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return results.data if results and results.data else []
        except Exception as e:
            print(f"Error getting evaluation history: {e}")
            return []
    
    async def get_metrics_dashboard_data(self) -> Dict:
        """
        Get data for metrics dashboard.
        
        Returns aggregated metrics, trends, and highlights.
        """
        # Get recent evaluations
        history = await self.get_evaluation_history(limit=30)
        
        if not history:
            return {'error': 'No evaluation data available'}
        
        # Extract metrics over time
        metrics_over_time = {}
        for run in history:
            metrics = json.loads(run['metrics']) if isinstance(run['metrics'], str) else run['metrics']
            timestamp = run['timestamp']
            
            for metric, value in metrics.items():
                if metric not in metrics_over_time:
                    metrics_over_time[metric] = []
                metrics_over_time[metric].append({
                    'timestamp': timestamp,
                    'value': value
                })
        
        # Calculate trends
        trends = {}
        for metric, values in metrics_over_time.items():
            if len(values) >= 2:
                recent = values[0]['value']
                older = values[-1]['value']
                change = recent - older
                trends[metric] = {
                    'current': recent,
                    'change': change,
                    'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable'
                }
        
        # Latest metrics
        latest = json.loads(history[0]['metrics']) if isinstance(history[0]['metrics'], str) else history[0]['metrics']
        
        return {
            'latest_metrics': latest,
            'trends': trends,
            'history': metrics_over_time,
            'pass_rate': history[0]['pass_rate'],
            'last_updated': history[0]['timestamp']
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics about golden dataset and evaluations."""
        return {
            'golden_dataset': self.golden.get_statistics(),
            'thresholds': self.regression.thresholds
        }
