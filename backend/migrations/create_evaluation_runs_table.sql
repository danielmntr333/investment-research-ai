-- Migration: Create evaluation_runs table for storing regression test results
-- This table stores the results of automated evaluation runs

-- Create evaluation_runs table
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

-- Add comment for documentation
COMMENT ON TABLE evaluation_runs IS 'Stores automated regression test results from the evaluation pipeline';
COMMENT ON COLUMN evaluation_runs.test_id IS 'Unique identifier for the test run (e.g., regression_20260118_193408)';
COMMENT ON COLUMN evaluation_runs.metrics IS 'JSON object containing all evaluation metrics (faithfulness, relevancy, etc.)';
COMMENT ON COLUMN evaluation_runs.regressions IS 'JSON array of metrics that dropped below threshold';
COMMENT ON COLUMN evaluation_runs.improvements IS 'JSON array of metrics that improved significantly';

-- Grant permissions if using RLS (Row Level Security)
-- Uncomment and adjust based on your Supabase security setup
-- ALTER TABLE evaluation_runs ENABLE ROW LEVEL SECURITY;
-- 
-- CREATE POLICY "Allow service role full access" ON evaluation_runs
--     FOR ALL
--     TO service_role
--     USING (true)
--     WITH CHECK (true);
