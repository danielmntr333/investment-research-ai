# Evaluation Storage Fix

## Problem

The evaluation system was failing to store metrics in the database with errors like:
- `"Could not find the table 'public.evaluation_runs'"`
- `"Could not find the 'failed' column of 'evaluations'"`

## Root Cause

There was a schema mismatch between what the code expected and what existed in the database:

1. **Code expected**: `evaluation_runs` table with columns for regression test results
2. **Database had**: `evaluations` table designed for individual message evaluations
3. **Result**: Metrics from evaluation runs were not being stored

## Solution

### Files Changed

#### 1. Database Migration
- **Created**: `backend/migrations/create_evaluation_runs_table.sql`
  - Defines the proper schema for storing evaluation run results
  - Includes all required columns: test_id, timestamp, metrics, total_cases, passed, failed, pass_rate, regressions, improvements

#### 2. Code Updates
- **Updated**: `backend/src/evaluation/regression.py`
  - Changed `table('evaluations')` → `table('evaluation_runs')` in `_store_results()`
  - Changed `table('evaluations')` → `table('evaluation_runs')` in `compare_to_baseline()`
  - Added better error messages with troubleshooting hints

- **Updated**: `backend/src/evaluation/pipeline.py`
  - Changed `table('evaluations')` → `table('evaluation_runs')` in `get_evaluation_history()`

- **Updated**: `backend/scripts/debug_evals.py`
  - Changed `table('evaluations')` → `table('evaluation_runs')` when fetching recent results

#### 3. Verification Script
- **Created**: `backend/scripts/verify_eval_storage.py`
  - Checks if `evaluation_runs` table exists
  - Tests insert and retrieval of evaluation data
  - Provides SQL migration if table is missing
  - Validates the complete storage workflow

#### 4. Documentation
- **Created**: `backend/migrations/README.md`
  - Documents all migrations
  - Provides troubleshooting guide
  - Explains table schemas

## How to Apply the Fix

### Step 1: Run the SQL Migration

**Option A: Via Supabase Dashboard (Recommended)**
1. Go to your Supabase project: https://supabase.com/dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy the contents of `backend/migrations/create_evaluation_runs_table.sql`
5. Execute the query
6. Verify in **Table Editor** that `evaluation_runs` table exists

**Option B: Copy-paste this SQL directly:**

```sql
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

CREATE INDEX IF NOT EXISTS idx_evaluation_runs_timestamp 
    ON evaluation_runs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_evaluation_runs_test_id 
    ON evaluation_runs(test_id);
```

### Step 2: Verify the Fix

Run the verification script to confirm everything is working:

```bash
cd backend
poetry run python scripts/verify_eval_storage.py
```

Expected output:
```
================================================================================
Evaluation Storage Verification
================================================================================

1. Connecting to Supabase...
✓ Connected successfully

2. Checking for evaluation_runs table...
✓ evaluation_runs table exists

Testing insert into evaluation_runs...
✓ Successfully inserted test evaluation data

Testing retrieval from evaluation_runs...
✓ Successfully retrieved evaluation data

Cleaning up test data...
✓ Test data cleaned up

================================================================================
VERIFICATION COMPLETE
================================================================================
✓ evaluation_runs table exists
✓ Can insert evaluation results
✓ Can retrieve evaluation results
✓ All metrics are stored correctly

✅ Your evaluation storage is configured correctly!
```

### Step 3: Run Evaluations

Now you can run evaluations and metrics will be stored properly:

```bash
# Run full evaluation
poetry run python scripts/run_evals.py

# Run quick evaluation (5 test cases)
poetry run python scripts/run_evals.py --quick

# Run detailed debug evaluation
poetry run python scripts/debug_evals.py
```

## What Gets Stored

When you run evaluations, the following data is stored in `evaluation_runs`:

```json
{
  "test_id": "regression_20260118_193408",
  "timestamp": 1737245648.123,
  "metrics": {
    "faithfulness": 0.794,
    "answer_relevancy": 0.467,
    "context_precision": 0.417,
    "context_recall": 0.282,
    "answer_correctness": 0.457,
    "numerical_accuracy": 0.185,
    "citation_rate": 0.000,
    "llm_judge_overall": 3.0
  },
  "total_cases": 21,
  "passed": 2,
  "failed": 6,
  "pass_rate": 0.25,
  "regressions": [
    "faithfulness: 0.794 < 0.850 (6.6% below threshold)",
    "answer_relevancy: 0.467 < 0.900 (48.1% below threshold)"
  ],
  "improvements": []
}
```

## Verification Checklist

- [ ] Run SQL migration in Supabase dashboard
- [ ] Verify `evaluation_runs` table exists in Supabase Table Editor
- [ ] Run `verify_eval_storage.py` script - all checks should pass
- [ ] Run `run_evals.py` - should see "✓ Results stored in database"
- [ ] Check Supabase Table Editor - should see new records in `evaluation_runs`

## Troubleshooting

### Error: "Could not find the table 'evaluation_runs'"
**Solution**: Run the SQL migration in Supabase dashboard.

### Error: "Could not store results in database"
**Solution**: 
1. Check that `SUPABASE_SERVICE_KEY` (not anon key) is in your `.env`
2. Verify the `evaluation_runs` table exists
3. Run `verify_eval_storage.py` for detailed diagnostics

### Verification script says table doesn't exist
**Solution**: The script will print the SQL you need to run. Copy it and execute in Supabase SQL Editor.

### Want to view stored results
**Solution**: 
```bash
# Via Supabase dashboard
# Go to: Table Editor → evaluation_runs → View data

# Or query programmatically:
poetry run python scripts/debug_evals.py
```

## Benefits

✅ **Proper tracking**: All evaluation metrics are now stored permanently  
✅ **Historical analysis**: Can compare performance over time  
✅ **Regression detection**: Stored regressions and improvements for each run  
✅ **Debugging**: Can retrieve and analyze past evaluation results  
✅ **Dashboard ready**: Data structure supports building metrics dashboards  

## Next Steps

After applying this fix:
1. Run baseline evaluation to establish thresholds
2. Set up regular evaluation runs (e.g., after code changes)
3. Build dashboards to visualize metric trends over time
4. Set up alerts for regressions (already implemented in code)
