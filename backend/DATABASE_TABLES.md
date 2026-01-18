# Database Tables Overview

This document explains the purpose of each table in the database.

## Core Tables

### users
Stores user accounts for OAuth authentication (future enhancement).

**Status**: ⚠️ Reserved (OAuth implementation pending)  
**Used by**: Future authentication middleware, user-specific features

---

### documents
Stores uploaded financial documents metadata.

**Status**: ✅ Active  
**Used by**: Document upload API, RAG pipeline

---

### document_chunks
Stores document chunks with embeddings for vector search.

**Status**: ✅ Active  
**Used by**: RAG retrieval, semantic search

---

### conversations
Stores chat conversation metadata.

**Status**: ✅ Active  
**Used by**: Chat API

---

### messages
Stores individual chat messages (user and assistant).

**Status**: ✅ Active  
**Used by**: Chat API, conversation history

---

### citations
Links messages to the document chunks used as sources.

**Status**: ✅ Active  
**Used by**: Chat API (source tracking)

---

## Evaluation Tables

### evaluation_runs
Stores batch evaluation results from regression test suites.

**Status**: ✅ Active  
**Used by**: 
- `scripts/run_evals.py`
- `scripts/debug_evals.py`
- `src/evaluation/regression.py`
- `src/evaluation/pipeline.py`
- `src/api/routes/evals.py`

**Purpose**: Track performance over time, detect regressions, store metrics from automated testing.

**Schema**:
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| test_id | TEXT | Unique identifier (e.g., regression_20260118_193408) |
| timestamp | DOUBLE PRECISION | Unix timestamp |
| metrics | JSONB | All metrics (faithfulness, relevancy, etc.) |
| total_cases | INTEGER | Number of test cases |
| passed | INTEGER | Metrics above threshold |
| failed | INTEGER | Metrics below threshold |
| pass_rate | DOUBLE PRECISION | Success rate (0.0-1.0) |
| regressions | JSONB | List of regressed metrics |
| improvements | JSONB | List of improved metrics |
| created_at | TIMESTAMP | Record creation time |

---

### evaluations
Originally designed for per-message evaluation of chat responses.

**Status**: ⚠️ Unused (Reserved for future feature)  
**Used by**: Nothing currently

**Purpose**: Would store real-time evaluation metrics for individual chat messages to track answer quality.

**Schema**:
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| message_id | UUID | Foreign key to messages |
| metrics | JSONB | Evaluation metrics for that message |
| eval_type | TEXT | Type of evaluation |
| created_at | TIMESTAMP | Record creation time |

**Options**:
1. **Keep it**: If you plan to implement per-message evaluation in the future
2. **Remove it**: Run `migrations/remove_unused_evaluations_table.sql` to clean up

---

## Utility Tables

### prompt_versions
Tracks different versions of prompts for A/B testing and rollback.

**Status**: ✅ Active (Infrastructure)  
**Used by**: Future prompt management features

---

## Table Relationship Diagram

```
users
  └── documents
       └── document_chunks
  └── conversations
       └── messages
            ├── citations → document_chunks
            └── evaluations (unused)

evaluation_runs (standalone, for batch testing)
```

## When to Use Which Table

### For Chat Message Evaluation (Future)
Use `evaluations` table - links to specific messages

### For Batch Testing / Regression Testing
Use `evaluation_runs` table - aggregate metrics from test suites

### Example:
```python
# Batch evaluation (currently implemented)
result = await eval_pipeline.run_full_evaluation()
# Stores in: evaluation_runs

# Per-message evaluation (future feature)
metrics = await evaluate_message(message_id, answer, sources)
# Would store in: evaluations
```

## Maintenance

### Check Table Usage
```sql
-- See evaluation runs over time
SELECT test_id, pass_rate, total_cases, created_at 
FROM evaluation_runs 
ORDER BY created_at DESC 
LIMIT 10;

-- Check if evaluations table is used
SELECT COUNT(*) FROM evaluations;
-- If returns 0, the table is unused
```

### Cleanup Old Evaluation Runs
```sql
-- Delete evaluation runs older than 90 days
DELETE FROM evaluation_runs 
WHERE created_at < NOW() - INTERVAL '90 days';
```
