#!/usr/bin/env python3
"""
Script to run evaluation suite manually.

Usage:
    python scripts/run_evals.py              # Run full evaluation suite
    python scripts/run_evals.py --quick      # Run on subset of test cases
    python scripts/run_evals.py --baseline   # Set new baseline thresholds
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from src.db.supabase import get_supabase
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline
from src.evaluation.pipeline import EvaluationPipeline
from src.evaluation.golden_set import GoldenDataset


async def run_full_evaluation():
    """Run full evaluation suite."""
    print("=" * 60)
    print("Starting Full Evaluation Suite")
    print("=" * 60)
    
    # Initialize components
    print("\n1. Initializing components...")
    try:
        db = get_supabase()
        llm = LLMProvider()
        rag = RAGPipeline(llm_provider=llm)
        
        eval_pipeline = EvaluationPipeline(rag, db, llm)
        print("✓ Components initialized")
    except Exception as e:
        print(f"✗ Failed to initialize components: {e}")
        return
    
    # Check golden dataset
    print("\n2. Checking golden dataset...")
    stats = eval_pipeline.get_statistics()
    golden_stats = stats['golden_dataset']
    
    if golden_stats['total_cases'] == 0:
        print("✗ No test cases found in golden dataset!")
        print("  Add test cases to data/golden_dataset/questions.json")
        return
    
    print(f"✓ Found {golden_stats['total_cases']} test cases")
    print(f"  By difficulty: {golden_stats['by_difficulty']}")
    print(f"  By capability: {golden_stats['by_capability']}")
    
    # Run evaluation
    print("\n3. Running evaluation suite...")
    print("   This may take several minutes...")
    
    try:
        result = await eval_pipeline.run_full_evaluation()
        
        # Print results summary
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        print(f"\nTest ID: {result['test_id']}")
        print(f"Total Test Cases: {result['total_cases']}")
        print(f"Metrics Passed: {result['passed']}")
        print(f"Metrics Failed: {result['failed']}")
        print(f"Pass Rate: {result['pass_rate']*100:.1f}%")
        
        print("\n--- Metrics ---")
        for metric, value in sorted(result['metrics'].items()):
            print(f"  {metric}: {value:.3f}")
        
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
        
        print("\n" + "=" * 60)
        print(f"✓ Evaluation complete!")
        print(f"  Results stored in database with ID: {result['test_id']}")
        
        return result
        
    except Exception as e:
        print(f"\n✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_quick_evaluation():
    """Run evaluation on a small subset for quick testing."""
    print("=" * 60)
    print("Starting Quick Evaluation (Sample)")
    print("=" * 60)
    
    # Initialize components
    print("\n1. Initializing components...")
    try:
        db = get_supabase()
        llm = LLMProvider()
        rag = RAGPipeline(llm_provider=llm)
        
        eval_pipeline = EvaluationPipeline(rag, db, llm)
        print("✓ Components initialized")
    except Exception as e:
        print(f"✗ Failed to initialize components: {e}")
        return
    
    # Get sample test cases
    print("\n2. Loading sample test cases...")
    golden = GoldenDataset()
    all_cases = golden.get_all_cases()
    
    if not all_cases:
        print("✗ No test cases found!")
        return
    
    # Take first 5 cases
    sample_cases = all_cases[:5]
    print(f"✓ Running on {len(sample_cases)} test cases")
    
    # Run RAGAS evaluation
    print("\n3. Running RAGAS evaluation...")
    try:
        ragas_result = await eval_pipeline.ragas.evaluate_test_set(sample_cases)
        
        print("\n--- RAGAS Metrics ---")
        for metric, value in ragas_result['overall_scores'].items():
            print(f"  {metric}: {value:.3f}")
        
        print("\n✓ Quick evaluation complete!")
        
    except Exception as e:
        print(f"\n✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


async def set_baseline():
    """Run evaluation and set as baseline thresholds."""
    print("=" * 60)
    print("Setting Baseline Thresholds")
    print("=" * 60)
    
    print("\nThis will:")
    print("1. Run full evaluation")
    print("2. Use results as baseline thresholds")
    print("3. Future evaluations will compare against this baseline")
    
    confirm = input("\nContinue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Run evaluation
    result = await run_full_evaluation()
    
    if result:
        print("\n" + "=" * 60)
        print("Baseline set successfully!")
        print("\nNew thresholds:")
        for metric, value in sorted(result['metrics'].items()):
            print(f"  {metric}: {value:.3f}")
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run evaluation suite")
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick evaluation on sample test cases'
    )
    parser.add_argument(
        '--baseline',
        action='store_true',
        help='Set new baseline thresholds from evaluation results'
    )
    
    args = parser.parse_args()
    
    if args.baseline:
        asyncio.run(set_baseline())
    elif args.quick:
        asyncio.run(run_quick_evaluation())
    else:
        asyncio.run(run_full_evaluation())


if __name__ == "__main__":
    main()
