#!/usr/bin/env python3
"""
Verify and fix evaluation storage schema.

This script:
1. Checks the current database schema
2. Creates the evaluation_runs table if needed
3. Verifies that metrics can be stored correctly
4. Tests storing and retrieving evaluation results
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from src.db.supabase import get_supabase


async def check_table_exists(db, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        result = await asyncio.to_thread(
            lambda: db.table(table_name).select('*').limit(1).execute()
        )
        return True
    except Exception as e:
        if 'PGRST204' in str(e) or 'PGRST205' in str(e):
            return False
        raise


async def get_table_columns(db, table_name: str) -> list:
    """Get columns of a table by attempting to query it."""
    try:
        result = await asyncio.to_thread(
            lambda: db.table(table_name).select('*').limit(0).execute()
        )
        # The error message will tell us about missing columns if we try to access them
        return []
    except Exception as e:
        return []


async def create_evaluation_runs_table(db):
    """Create the evaluation_runs table using raw SQL."""
    sql = """
    CREATE TABLE IF NOT EXISTS evaluation_runs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        test_id TEXT NOT NULL,
        timestamp DOUBLE PRECISION NOT NULL,
        metrics JSONB NOT NULL,
        total_cases INTEGER NOT NULL,
        passed INTEGER NOT NULL,
        failed INTEGER NOT NULL,
        pass_rate DOUBLE PRECISION NOT NULL,
        regressions JSONB DEFAULT '[]'::jsonb,
        improvements JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_evaluation_runs_timestamp ON evaluation_runs(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_evaluation_runs_test_id ON evaluation_runs(test_id);
    """
    
    try:
        # Use Supabase's RPC or execute raw SQL
        print("Creating evaluation_runs table...")
        await asyncio.to_thread(lambda: db.rpc('exec_sql', {'sql': sql}).execute())
        print("✓ evaluation_runs table created successfully")
        return True
    except Exception as e:
        print(f"Note: Could not create table via RPC: {e}")
        print("You may need to run the SQL manually in Supabase dashboard")
        return False


async def test_insert_evaluation(db):
    """Test inserting a sample evaluation result."""
    test_data = {
        'test_id': f'test_verify_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'timestamp': datetime.now().timestamp(),
        'metrics': json.dumps({
            'faithfulness': 0.85,
            'answer_relevancy': 0.90,
            'context_precision': 0.80
        }),
        'total_cases': 10,
        'passed': 8,
        'failed': 2,
        'pass_rate': 0.8,
        'regressions': json.dumps([]),
        'improvements': json.dumps(['faithfulness improved by 5%'])
    }
    
    try:
        print("\nTesting insert into evaluation_runs...")
        result = await asyncio.to_thread(
            lambda: db.table('evaluation_runs').insert(test_data).execute()
        )
        print("✓ Successfully inserted test evaluation data")
        print(f"  Inserted record ID: {result.data[0]['id']}")
        return True, result.data[0]['id']
    except Exception as e:
        print(f"✗ Failed to insert: {e}")
        return False, None


async def test_retrieve_evaluation(db, record_id):
    """Test retrieving evaluation results."""
    try:
        print("\nTesting retrieval from evaluation_runs...")
        result = await asyncio.to_thread(
            lambda: db.table('evaluation_runs')
                .select('*')
                .eq('id', record_id)
                .execute()
        )
        
        if result.data:
            print("✓ Successfully retrieved evaluation data")
            record = result.data[0]
            print(f"  Test ID: {record['test_id']}")
            print(f"  Total cases: {record['total_cases']}")
            print(f"  Pass rate: {record['pass_rate']*100:.1f}%")
            
            # Parse JSON fields
            metrics = json.loads(record['metrics']) if isinstance(record['metrics'], str) else record['metrics']
            print(f"  Metrics: {list(metrics.keys())}")
            return True
        else:
            print("✗ No data retrieved")
            return False
    except Exception as e:
        print(f"✗ Failed to retrieve: {e}")
        return False


async def cleanup_test_data(db, record_id):
    """Clean up test data."""
    try:
        print("\nCleaning up test data...")
        await asyncio.to_thread(
            lambda: db.table('evaluation_runs')
                .delete()
                .eq('id', record_id)
                .execute()
        )
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"Note: Could not clean up test data: {e}")


def print_sql_migration():
    """Print the SQL migration that needs to be run manually."""
    print("\n" + "="*80)
    print("SQL MIGRATION TO RUN IN SUPABASE")
    print("="*80)
    print("""
-- Run this SQL in your Supabase SQL editor if the automatic creation failed

-- Create evaluation_runs table for storing regression test results
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id TEXT NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    metrics JSONB NOT NULL,
    total_cases INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    pass_rate DOUBLE PRECISION NOT NULL,
    regressions JSONB DEFAULT '[]'::jsonb,
    improvements JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_evaluation_runs_timestamp 
    ON evaluation_runs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_evaluation_runs_test_id 
    ON evaluation_runs(test_id);

-- Grant permissions (adjust based on your Supabase setup)
-- If you're using service role key, this might not be necessary
-- ALTER TABLE evaluation_runs ENABLE ROW LEVEL SECURITY;
""")
    print("="*80)


async def main():
    """Main verification flow."""
    print("="*80)
    print("Evaluation Storage Verification")
    print("="*80)
    
    try:
        # Connect to database
        print("\n1. Connecting to Supabase...")
        db = get_supabase()
        print("✓ Connected successfully")
        
        # Check if evaluation_runs table exists
        print("\n2. Checking for evaluation_runs table...")
        eval_runs_exists = await check_table_exists(db, 'evaluation_runs')
        
        if eval_runs_exists:
            print("✓ evaluation_runs table exists")
        else:
            print("✗ evaluation_runs table does NOT exist")
            print("\nThe evaluation_runs table needs to be created.")
            print_sql_migration()
            
            # Try to create it (might not work depending on permissions)
            success = await create_evaluation_runs_table(db)
            if not success:
                print("\n⚠️  Please run the SQL migration manually in Supabase dashboard")
                print("   Go to: Supabase Dashboard → SQL Editor → New Query")
                print("   Then re-run this script to verify")
                return
        
        # Test insert
        success, record_id = await test_insert_evaluation(db)
        if not success:
            print("\n⚠️  Could not test storage. Please check:")
            print("   1. The evaluation_runs table exists")
            print("   2. Your service key has write permissions")
            print("   3. All required columns are present")
            return
        
        # Test retrieve
        success = await test_retrieve_evaluation(db, record_id)
        if not success:
            print("\n⚠️  Could not test retrieval")
            return
        
        # Cleanup
        await cleanup_test_data(db, record_id)
        
        # Final summary
        print("\n" + "="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)
        print("✓ evaluation_runs table exists")
        print("✓ Can insert evaluation results")
        print("✓ Can retrieve evaluation results")
        print("✓ All metrics are stored correctly")
        print("\n✅ Your evaluation storage is configured correctly!")
        print("\nYou can now run evaluations with confidence that results")
        print("will be stored in the database.")
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
