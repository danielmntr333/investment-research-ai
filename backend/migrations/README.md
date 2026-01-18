# Database Migrations

This directory contains SQL migration scripts for the Investment Research AI database.

## How to Apply Migrations

### Option 1: Via Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy the contents of the migration file
5. Execute the query
6. Verify the changes in the **Table Editor**

### Option 2: Via Supabase CLI

```bash
# If you have Supabase CLI installed
supabase db push
```

### Option 3: Via the Verification Script

```bash
# Run the verification script which will guide you through the process
poetry run python scripts/verify_eval_storage.py
```

## Migration Files

### create_evaluation_runs_table.sql

**Purpose**: Creates the `evaluation_runs` table for storing automated regression test results.

**When to run**: 
- Before running evaluation scripts (`scripts/run_evals.py`)
- If you see errors like "Could not find the 'failed' column of 'evaluations'"

**What it does**:
- Creates `evaluation_runs` table with proper schema
- Adds indexes for performance (timestamp, test_id)
- Includes columns: test_id, timestamp, metrics, total_cases, passed, failed, pass_rate, regressions, improvements

**How to verify**:
```bash
poetry run python scripts/verify_eval_storage.py
```

### remove_unused_evaluations_table.sql (Optional)

**Purpose**: Removes the unused `evaluations` table to clean up the database.

**When to run**: 
- Only if you want to remove the unused table
- The `evaluations` table is not currently used by any code
- It was designed for per-message evaluation (future feature)

**⚠️ Warning**: This permanently deletes the table. Only run if you're sure you don't need it.

**What it does**:
- Drops the `evaluations` table
- Removes the associated index

**Note**: The `evaluation_runs` table is different and actively used. Do NOT remove it.

## Troubleshooting

### Error: "Could not find the table 'evaluation_runs'"

**Solution**: Run the `create_evaluation_runs_table.sql` migration in your Supabase dashboard.

### Error: "Could not find the 'failed' column"

**Solution**: This means you're using the old `evaluations` table instead of `evaluation_runs`. Run the migration to create the correct table.

### Error: Permission denied

**Solution**: Make sure you're using the service role key (not anon key) in your `.env` file:
```
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

## Table Schemas

### evaluation_runs
Stores automated regression test results from the evaluation pipeline.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| test_id | TEXT | Unique identifier for test run (e.g., regression_20260118_193408) |
| timestamp | DOUBLE PRECISION | Unix timestamp of when test was run |
| metrics | JSONB | All evaluation metrics (faithfulness, relevancy, etc.) |
| total_cases | INTEGER | Number of test cases evaluated |
| passed | INTEGER | Number of metrics that passed thresholds |
| failed | INTEGER | Number of metrics that failed thresholds |
| pass_rate | DOUBLE PRECISION | Percentage of passed metrics (0.0-1.0) |
| regressions | JSONB | Array of metrics that dropped below threshold |
| improvements | JSONB | Array of metrics that improved significantly |
| created_at | TIMESTAMP | When the record was created |

### evaluations
Stores evaluation metrics for individual chat messages (different purpose than evaluation_runs).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| message_id | UUID | Foreign key to messages table |
| metrics | JSONB | Evaluation metrics for the message |
| eval_type | TEXT | Type of evaluation performed |
| created_at | TIMESTAMP | When the record was created |
