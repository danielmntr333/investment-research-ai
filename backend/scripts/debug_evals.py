#!/usr/bin/env python3
"""
Debug evaluation results with detailed per-test-case insights.

Usage:
    python scripts/debug_evals.py              # Run and export detailed results
    python scripts/debug_evals.py --recent     # Analyze most recent evaluation from DB
"""
import asyncio
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.db.supabase import get_supabase
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline
from src.evaluation.pipeline import EvaluationPipeline
from src.evaluation.golden_set import GoldenDataset
from src.evaluation.ragas_eval import RAGASEvaluator
from src.evaluation.custom_metrics import FinancialMetrics
from src.evaluation.llm_judge import LLMJudge
from tqdm import tqdm


async def run_detailed_evaluation():
    """Run evaluation and export detailed per-test-case results."""
    print("=" * 80)
    print("Detailed Evaluation Debug")
    print("=" * 80)
    
    # Initialize components
    print("\n1. Initializing components...")
    db = get_supabase()
    llm = LLMProvider()
    rag = RAGPipeline(llm_provider=llm)
    
    ragas = RAGASEvaluator(rag, llm)
    custom = FinancialMetrics()
    judge = LLMJudge(llm)
    golden = GoldenDataset()
    
    print("✓ Components initialized")
    
    # Get test cases
    print("\n2. Loading test cases...")
    test_cases = golden.get_all_cases()
    print(f"✓ Loaded {len(test_cases)} test cases")
    
    # Run detailed evaluation
    print("\n3. Running detailed evaluation...")
    print("   (This will take several minutes...)")
    
    detailed_results = []
    
    for i, case in enumerate(tqdm(test_cases, desc="Evaluating")):
        try:
            # Get RAG response
            result = rag.query(
                question=case['question'],
                document_ids=case.get('document_ids')
            )
            
            answer = result.answer if hasattr(result, 'answer') else result.get('answer', '')
            sources = result.sources if hasattr(result, 'sources') else result.get('sources', [])
            contexts = [s.get('content', '') if isinstance(s, dict) else str(s) for s in sources]
            
            # RAGAS scores
            ragas_scores = await ragas.evaluate_single_query(
                question=case['question'],
                answer=answer,
                contexts=contexts,
                ground_truth=case['expected_answer']
            )
            
            # Custom metrics
            num_result = custom.numerical_accuracy(answer, case['expected_answer'])
            cit_result = custom.citation_quality(answer)
            
            # LLM Judge (optional, to save costs)
            judge_scores = await judge.evaluate_answer(
                question=case['question'],
                generated_answer=answer,
                ground_truth=case['expected_answer'],
                sources=sources
            )
            
            # Compile detailed result
            detailed_result = {
                'test_id': case.get('id', f"test_{i+1}"),
                'question': case['question'],
                'expected_answer': case['expected_answer'],
                'generated_answer': answer,
                'difficulty': case.get('difficulty', 'unknown'),
                'capabilities': case.get('capabilities', []),
                'num_sources': len(sources),
                'sources': [
                    {
                        'content': s.get('content', '')[:200] + '...' if len(s.get('content', '')) > 200 else s.get('content', ''),
                        'relevance_score': s.get('relevance_score', 0)
                    }
                    for s in sources[:3]  # Top 3 sources
                ],
                'ragas_scores': ragas_scores,
                'custom_metrics': {
                    'numerical_accuracy': num_result['score'],
                    'citation_rate': cit_result['citation_rate'],
                    'citation_count': cit_result['citation_count']
                },
                'judge_scores': judge_scores,
                'overall_score': calculate_overall_score(ragas_scores, num_result, cit_result, judge_scores)
            }
            
            detailed_results.append(detailed_result)
            
        except Exception as e:
            print(f"\n✗ Error evaluating test case {case.get('id', i)}: {e}")
            import traceback
            traceback.print_exc()
            
            # Add error result
            detailed_results.append({
                'test_id': case.get('id', f"test_{i+1}"),
                'question': case['question'],
                'error': str(e),
                'status': 'failed'
            })
    
    # Export results
    print("\n4. Exporting results...")
    export_results(detailed_results)
    
    # Print summary
    print("\n5. Summary Analysis")
    print_summary_analysis(detailed_results)
    
    return detailed_results


def calculate_overall_score(ragas_scores: Dict, num_result: Dict, cit_result: Dict, judge_scores: Dict) -> float:
    """Calculate weighted overall score."""
    ragas_avg = sum(ragas_scores.values()) / len(ragas_scores) if ragas_scores else 0
    custom_avg = (num_result['score'] + cit_result['citation_rate']) / 2
    judge_avg = judge_scores.get('overall', 3) / 5.0 if judge_scores else 0.5
    
    return 0.40 * ragas_avg + 0.35 * custom_avg + 0.25 * judge_avg


def export_results(results: List[Dict]):
    """Export results to JSON and CSV files."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent.parent / "data" / "eval_debug"
    output_dir.mkdir(exist_ok=True)
    
    # JSON export (full details)
    json_file = output_dir / f"detailed_results_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ Exported detailed JSON: {json_file}")
    
    # CSV export (summary)
    csv_file = output_dir / f"summary_results_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Test ID', 'Question', 'Difficulty', 'Capabilities',
            'Faithfulness', 'Answer Relevancy', 'Context Precision', 'Context Recall', 'Answer Correctness',
            'Numerical Accuracy', 'Citation Rate', 'Judge Overall',
            'Overall Score', 'Status'
        ])
        
        # Data
        for r in results:
            if r.get('status') == 'failed':
                writer.writerow([
                    r.get('test_id', ''),
                    r.get('question', ''),
                    'ERROR',
                    '',
                    '', '', '', '', '', '', '', '', '', 'FAILED'
                ])
            else:
                writer.writerow([
                    r.get('test_id', ''),
                    r.get('question', '')[:100],  # Truncate for CSV
                    r.get('difficulty', ''),
                    ','.join(r.get('capabilities', [])),
                    r['ragas_scores'].get('faithfulness', 0),
                    r['ragas_scores'].get('answer_relevancy', 0),
                    r['ragas_scores'].get('context_precision', 0),
                    r['ragas_scores'].get('context_recall', 0),
                    r['ragas_scores'].get('answer_correctness', 0),
                    r['custom_metrics'].get('numerical_accuracy', 0),
                    r['custom_metrics'].get('citation_rate', 0),
                    r['judge_scores'].get('overall', 0) if r.get('judge_scores') else 0,
                    r.get('overall_score', 0),
                    'PASS' if r.get('overall_score', 0) > 0.5 else 'FAIL'
                ])
    
    print(f"✓ Exported summary CSV: {csv_file}")
    
    # Also create a human-readable report
    report_file = output_dir / f"report_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Evaluation Debug Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Test Cases:** {len(results)}\n\n")
        
        # Group by status
        passed = [r for r in results if r.get('status') != 'failed' and r.get('overall_score', 0) > 0.5]
        failed = [r for r in results if r.get('status') != 'failed' and r.get('overall_score', 0) <= 0.5]
        errors = [r for r in results if r.get('status') == 'failed']
        
        f.write(f"- **Passed:** {len(passed)}\n")
        f.write(f"- **Failed:** {len(failed)}\n")
        f.write(f"- **Errors:** {len(errors)}\n\n")
        
        # Worst performing cases
        f.write("## Worst Performing Cases\n\n")
        sorted_results = sorted(
            [r for r in results if r.get('status') != 'failed'],
            key=lambda x: x.get('overall_score', 0)
        )
        
        for r in sorted_results[:10]:  # Top 10 worst
            f.write(f"### {r.get('test_id', 'Unknown')}\n\n")
            f.write(f"**Question:** {r.get('question', '')}\n\n")
            f.write(f"**Difficulty:** {r.get('difficulty', 'unknown')}\n\n")
            f.write(f"**Overall Score:** {r.get('overall_score', 0):.3f}\n\n")
            f.write("**RAGAS Scores:**\n")
            for metric, score in r.get('ragas_scores', {}).items():
                f.write(f"- {metric}: {score:.3f}\n")
            f.write("\n")
            f.write(f"**Expected:** {r.get('expected_answer', '')[:200]}...\n\n")
            f.write(f"**Generated:** {r.get('generated_answer', '')[:200]}...\n\n")
            f.write("---\n\n")
    
    print(f"✓ Exported readable report: {report_file}")


def print_summary_analysis(results: List[Dict]):
    """Print detailed summary analysis."""
    print("=" * 80)
    
    # Filter out errors
    valid_results = [r for r in results if r.get('status') != 'failed']
    
    if not valid_results:
        print("✗ No valid results to analyze")
        return
    
    # Overall stats
    avg_overall = sum(r.get('overall_score', 0) for r in valid_results) / len(valid_results)
    print(f"\n📊 Overall Average Score: {avg_overall:.3f}")
    
    # Metric averages
    print("\n📈 Average Scores by Metric:")
    
    # RAGAS metrics
    ragas_metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness']
    for metric in ragas_metrics:
        scores = [r['ragas_scores'].get(metric, 0) for r in valid_results if 'ragas_scores' in r]
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {metric:20s}: {avg:.3f}")
    
    # Custom metrics
    custom_metrics = ['numerical_accuracy', 'citation_rate']
    for metric in custom_metrics:
        scores = [r.get('custom_metrics', {}).get(metric, 0) for r in valid_results if 'custom_metrics' in r]
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {metric:20s}: {avg:.3f}")
    
    # By difficulty
    print("\n📊 Performance by Difficulty:")
    for difficulty in ['easy', 'medium', 'hard']:
        difficulty_results = [r for r in valid_results if r.get('difficulty') == difficulty]
        if difficulty_results:
            avg = sum(r.get('overall_score', 0) for r in difficulty_results) / len(difficulty_results)
            print(f"  {difficulty.capitalize():10s}: {avg:.3f} ({len(difficulty_results)} cases)")
    
    # Top failures
    print("\n❌ Top 5 Failing Cases:")
    sorted_results = sorted(valid_results, key=lambda x: x.get('overall_score', 0))
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"\n  {i}. {r.get('test_id', 'Unknown')} (Score: {r.get('overall_score', 0):.3f})")
        print(f"     Question: {r.get('question', '')[:80]}...")
        print(f"     Worst metrics:")
        
        # Find worst metrics for this case
        all_scores = {
            **r.get('ragas_scores', {}),
            'numerical_accuracy': r.get('custom_metrics', {}).get('numerical_accuracy', 0),
            'citation_rate': r.get('custom_metrics', {}).get('citation_rate', 0)
        }
        worst_metrics = sorted(all_scores.items(), key=lambda x: x[1])[:3]
        for metric, score in worst_metrics:
            print(f"       - {metric}: {score:.3f}")
    
    # Common issues
    print("\n⚠️  Common Issues Detected:")
    
    # Low faithfulness
    low_faith = [r for r in valid_results if r.get('ragas_scores', {}).get('faithfulness', 0) < 0.5]
    if low_faith:
        print(f"  - {len(low_faith)} cases with low faithfulness (<0.5)")
        print(f"    → Answers may not be grounded in retrieved context")
    
    # Low context precision
    low_precision = [r for r in valid_results if r.get('ragas_scores', {}).get('context_precision', 0) < 0.5]
    if low_precision:
        print(f"  - {len(low_precision)} cases with low context precision (<0.5)")
        print(f"    → Retrieved documents may not be relevant")
    
    # Low citation rate
    low_citations = [r for r in valid_results if r.get('custom_metrics', {}).get('citation_rate', 0) < 0.5]
    if low_citations:
        print(f"  - {len(low_citations)} cases with low citation rate (<0.5)")
        print(f"    → Answers missing proper citations")
    
    # Few sources
    few_sources = [r for r in valid_results if r.get('num_sources', 0) < 2]
    if few_sources:
        print(f"  - {len(few_sources)} cases with <2 sources retrieved")
        print(f"    → May need to improve retrieval")
    
    print("\n" + "=" * 80)


async def analyze_recent_run():
    """Analyze the most recent evaluation from database."""
    print("=" * 80)
    print("Analyzing Recent Evaluation Run")
    print("=" * 80)
    
    db = get_supabase()
    
    # Get most recent evaluation
    print("\n1. Fetching most recent evaluation from database...")
    try:
        result = db.table('evaluation_runs')\
            .select('*')\
            .order('timestamp', desc=True)\
            .limit(1)\
            .execute()
        
        if not result.data or len(result.data) == 0:
            print("✗ No evaluation results found in database")
            return
        
        recent = result.data[0]
        print(f"✓ Found evaluation: {recent['test_id']}")
        print(f"  Timestamp: {datetime.fromtimestamp(recent['timestamp'])}")
        
        # Parse metrics
        metrics = json.loads(recent['metrics']) if isinstance(recent['metrics'], str) else recent['metrics']
        
        print("\n2. Metrics Summary:")
        print(f"  Total Cases: {recent['total_cases']}")
        print(f"  Pass Rate: {recent['pass_rate']*100:.1f}%")
        
        print("\n  Metrics:")
        for metric, value in sorted(metrics.items()):
            print(f"    {metric:20s}: {value:.3f}")
        
        # Regressions
        regressions = json.loads(recent['regressions']) if isinstance(recent['regressions'], str) else recent['regressions']
        if regressions:
            print("\n  ⚠️  Regressions:")
            for reg in regressions:
                print(f"    - {reg}")
        
        print("\n💡 To get detailed per-test-case analysis, run:")
        print("   python scripts/debug_evals.py")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug evaluation results")
    parser.add_argument(
        '--recent',
        action='store_true',
        help='Analyze most recent evaluation from database'
    )
    
    args = parser.parse_args()
    
    if args.recent:
        asyncio.run(analyze_recent_run())
    else:
        asyncio.run(run_detailed_evaluation())


if __name__ == "__main__":
    main()
