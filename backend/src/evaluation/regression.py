"""Regression testing suite."""
import asyncio
from typing import Dict, List
from datetime import datetime
import json


class RegressionTestSuite:
    """
    Automated regression testing for RAG system.
    """
    
    def __init__(
        self,
        rag_pipeline,
        golden_dataset,
        ragas_evaluator,
        custom_metrics,
        llm_judge,
        db_client
    ):
        """
        Initialize regression test suite.
        
        Args:
            rag_pipeline: RAG pipeline instance
            golden_dataset: Golden dataset manager
            ragas_evaluator: RAGAS evaluator instance
            custom_metrics: Custom metrics evaluator
            llm_judge: LLM judge instance
            db_client: Database client
        """
        self.rag = rag_pipeline
        self.golden = golden_dataset
        self.ragas = ragas_evaluator
        self.custom = custom_metrics
        self.judge = llm_judge
        self.db = db_client
        
        # Baseline thresholds (set after initial run)
        self.thresholds = {
            'faithfulness': 0.85,
            'answer_relevancy': 0.90,
            'context_precision': 0.80,
            'numerical_accuracy': 0.95,
            'citation_rate': 0.80,
            'llm_judge_overall': 4.0
        }
    
    async def run_full_suite(self) -> Dict:
        """
        Run complete regression test suite.
        
        Returns:
            {
                'test_id': str,
                'timestamp': float,
                'total_cases': int,
                'passed': int,
                'failed': int,
                'metrics': Dict,
                'regressions': List[str],
                'improvements': List[str]
            }
        """
        test_id = f"regression_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Starting regression test: {test_id}")
        
        # Get all test cases
        test_cases = self.golden.get_all_cases()
        
        if not test_cases:
            print("Warning: No test cases found in golden dataset")
            return {
                'test_id': test_id,
                'timestamp': datetime.now().timestamp(),
                'total_cases': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0,
                'metrics': {},
                'regressions': [],
                'improvements': []
            }
        
        # Run evaluations
        ragas_results = await self.ragas.evaluate_test_set(test_cases)
        
        # Custom metrics
        custom_results = await self._evaluate_custom_metrics(test_cases)
        
        # LLM judge (sample of cases to save costs)
        sample_size = min(20, len(test_cases))
        sample_cases = test_cases[:sample_size]
        judge_results = await self._evaluate_with_judge(sample_cases)
        
        # Aggregate metrics
        metrics = {
            **ragas_results['overall_scores'],
            **custom_results,
            **judge_results
        }
        
        # Compare to baseline
        regressions = self._detect_regressions(metrics)
        improvements = self._detect_improvements(metrics)
        
        # Count pass/fail based on threshold
        passed = sum(1 for m, v in metrics.items() if m in self.thresholds and v >= self.thresholds[m])
        failed = len([m for m in self.thresholds.keys() if m in metrics]) - passed
        
        # Store results
        result = {
            'test_id': test_id,
            'timestamp': datetime.now().timestamp(),
            'total_cases': len(test_cases),
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / max(len(self.thresholds), 1),
            'metrics': metrics,
            'regressions': regressions,
            'improvements': improvements
        }
        
        # Save to database
        await self._store_results(result)
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    async def _evaluate_custom_metrics(self, test_cases: List[Dict]) -> Dict:
        """Evaluate custom financial metrics."""
        numerical_scores = []
        citation_rates = []
        
        for case in test_cases:
            try:
                result = self.rag.query(question=case['question'])
                answer = result.answer if hasattr(result, 'answer') else result.get('answer', '')
                
                # Numerical accuracy
                num_result = self.custom.numerical_accuracy(
                    answer,
                    case['expected_answer']
                )
                numerical_scores.append(num_result['score'])
                
                # Citation quality
                cit_result = self.custom.citation_quality(answer)
                citation_rates.append(cit_result['citation_rate'])
            except Exception as e:
                print(f"Error evaluating case {case.get('id', 'unknown')}: {e}")
                continue
        
        return {
            'numerical_accuracy': sum(numerical_scores) / len(numerical_scores) if numerical_scores else 0,
            'citation_rate': sum(citation_rates) / len(citation_rates) if citation_rates else 0
        }
    
    async def _evaluate_with_judge(self, test_cases: List[Dict]) -> Dict:
        """Evaluate with LLM judge on sample."""
        judgments = []
        
        for case in test_cases:
            try:
                result = self.rag.query(question=case['question'])
                answer = result.answer if hasattr(result, 'answer') else result.get('answer', '')
                sources = result.sources if hasattr(result, 'sources') else result.get('sources', [])
                
                judgment = await self.judge.evaluate_answer(
                    question=case['question'],
                    generated_answer=answer,
                    ground_truth=case['expected_answer'],
                    sources=sources
                )
                judgments.append(judgment)
            except Exception as e:
                print(f"Error judging case {case.get('id', 'unknown')}: {e}")
                continue
        
        # Aggregate
        aggregated = self.judge.aggregate_scores(judgments)
        
        return {
            'llm_judge_overall': aggregated.get('avg_overall', 0),
            'llm_judge_correctness': aggregated.get('avg_correctness', 0),
            'llm_judge_completeness': aggregated.get('avg_completeness', 0)
        }
    
    def _detect_regressions(self, current_metrics: Dict) -> List[str]:
        """Detect metrics that dropped below threshold."""
        regressions = []
        
        for metric, threshold in self.thresholds.items():
            if metric in current_metrics:
                current_value = current_metrics[metric]
                
                if current_value < threshold:
                    drop_percent = ((threshold - current_value) / threshold) * 100
                    regressions.append(
                        f"{metric}: {current_value:.3f} < {threshold:.3f} "
                        f"({drop_percent:.1f}% below threshold)"
                    )
        
        return regressions
    
    def _detect_improvements(self, current_metrics: Dict) -> List[str]:
        """Detect metrics that improved significantly."""
        improvements = []
        
        for metric, threshold in self.thresholds.items():
            if metric in current_metrics:
                current_value = current_metrics[metric]
                
                if current_value > threshold * 1.05:  # 5% improvement
                    improvement_percent = ((current_value - threshold) / threshold) * 100
                    improvements.append(
                        f"{metric}: {current_value:.3f} > {threshold:.3f} "
                        f"({improvement_percent:.1f}% improvement)"
                    )
        
        return improvements
    
    async def _store_results(self, result: Dict):
        """Store test results in database."""
        try:
            await self.db.table('evaluation_runs').insert({
                'test_id': result['test_id'],
                'timestamp': result['timestamp'],
                'metrics': json.dumps(result['metrics']),
                'total_cases': result['total_cases'],
                'passed': result['passed'],
                'failed': result['failed'],
                'pass_rate': result['pass_rate'],
                'regressions': json.dumps(result['regressions']),
                'improvements': json.dumps(result['improvements'])
            }).execute()
            print(f"✓ Results stored in database (evaluation_runs table)")
        except Exception as e:
            print(f"✗ Warning: Could not store results in database: {e}")
            print(f"   Please ensure the evaluation_runs table exists.")
            print(f"   Run: python scripts/verify_eval_storage.py")
    
    def _print_summary(self, result: Dict):
        """Print human-readable summary."""
        print("\n" + "="*60)
        print(f"Regression Test Results: {result['test_id']}")
        print("="*60)
        print(f"\nTotal Cases: {result['total_cases']}")
        print(f"Metrics Passed: {result['passed']}")
        print(f"Metrics Failed: {result['failed']}")
        print(f"Pass Rate: {result['pass_rate']*100:.1f}%")
        
        print("\n--- Metrics ---")
        for metric, value in sorted(result['metrics'].items()):
            threshold = self.thresholds.get(metric, 0)
            status = "✓" if value >= threshold else "✗"
            print(f"{status} {metric}: {value:.3f} (threshold: {threshold:.3f})")
        
        if result['regressions']:
            print("\n⚠️  REGRESSIONS DETECTED:")
            for reg in result['regressions']:
                print(f"  - {reg}")
        else:
            print("\n✓ No regressions detected")
        
        if result['improvements']:
            print("\n🎉 IMPROVEMENTS:")
            for imp in result['improvements']:
                print(f"  + {imp}")
        
        print("\n" + "="*60 + "\n")
    
    async def compare_to_baseline(self, test_id: str) -> Dict:
        """Compare a test run to baseline."""
        try:
            # Get baseline (first test run)
            baseline = await self.db.table('evaluation_runs').select('*').order('timestamp').limit(1).execute()
            
            if not baseline.data:
                return {'error': 'No baseline found'}
            
            baseline = baseline.data[0]
            
            # Get current test
            current = await self.db.table('evaluation_runs').select('*').eq('test_id', test_id).execute()
            
            if not current.data:
                return {'error': 'Test not found'}
            
            current = current.data[0]
            
            baseline_metrics = json.loads(baseline['metrics'])
            current_metrics = json.loads(current['metrics'])
            
            comparison = {}
            for metric in baseline_metrics:
                if metric in current_metrics:
                    baseline_val = baseline_metrics[metric]
                    current_val = current_metrics[metric]
                    change = current_val - baseline_val
                    change_percent = (change / baseline_val * 100) if baseline_val != 0 else 0
                    
                    comparison[metric] = {
                        'baseline': baseline_val,
                        'current': current_val,
                        'change': change,
                        'change_percent': change_percent
                    }
            
            return comparison
        except Exception as e:
            return {'error': str(e)}


# Standalone function for scheduled regression
async def run_regression_suite(
    rag_pipeline,
    golden_dataset,
    ragas_evaluator,
    custom_metrics,
    llm_judge,
    db_client
) -> Dict:
    """
    Run full regression test suite (standalone function).
    
    This can be called from scheduled jobs or scripts.
    """
    suite = RegressionTestSuite(
        rag_pipeline,
        golden_dataset,
        ragas_evaluator,
        custom_metrics,
        llm_judge,
        db_client
    )
    
    result = await suite.run_full_suite()
    
    # Alert if regressions detected
    if result['regressions']:
        await send_alert(result)
    
    return result


async def send_alert(result: Dict):
    """Send alert when regressions detected."""
    # Could send to Slack, email, etc.
    print(f"🚨 ALERT: {len(result['regressions'])} regressions detected!")
    for reg in result['regressions']:
        print(f"  - {reg}")


def detect_regressions(current_metrics: Dict, baseline_metrics: Dict) -> list:
    """Detect metric regressions compared to baseline (standalone function)."""
    regressions = []
    
    for metric, baseline_val in baseline_metrics.items():
        if metric in current_metrics:
            current_val = current_metrics[metric]
            change = (current_val - baseline_val) / baseline_val if baseline_val != 0 else 0
            
            # Flag if >5% drop
            if change < -0.05:
                regressions.append({
                    'metric': metric,
                    'baseline': baseline_val,
                    'current': current_val,
                    'change_percent': change * 100
                })
    
    return regressions
