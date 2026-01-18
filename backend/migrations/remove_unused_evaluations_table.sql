-- Optional Migration: Remove unused evaluations table
-- 
-- This migration removes the 'evaluations' table which was originally designed
-- for per-message evaluation but is not currently used in the codebase.
--
-- ⚠️  WARNING: Only run this if you're sure you don't need per-message evaluation
-- ⚠️  This will delete the table and all its data permanently
--
-- The 'evaluation_runs' table is still used for batch regression testing and
-- should NOT be removed.

-- Drop the index first
DROP INDEX IF EXISTS idx_evaluations_message;

-- Drop the evaluations table
DROP TABLE IF EXISTS evaluations;

-- Confirmation message
-- Run this in Supabase SQL Editor to remove the unused table
