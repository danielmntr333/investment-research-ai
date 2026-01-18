# Evaluation System

## Overview

A comprehensive evaluation framework for the Investment Research AI system, featuring:

- **RAGAS Metrics**: Industry-standard RAG evaluation metrics
- **Custom Financial Metrics**: Domain-specific metrics for financial accuracy
- **LLM-as-Judge**: Automated qualitative evaluation using GPT-4
- **Golden Dataset**: Curated test cases with ground truth answers
- **Regression Testing**: Automated quality monitoring and alerting
- **Metrics Dashboard**: Visual tracking of performance over time

## Architecture

```
evaluation/
├── pipeline.py         # Main orchestrator
├── ragas_eval.py       # RAGAS metrics integration
├── custom_metrics.py   # Financial-specific metrics
├── llm_judge.py        # LLM-as-judge implementation
├── golden_set.py       # Golden dataset management
└── regression.py       # Regression testing suite
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
poetry install
poetry run python -m spacy download en_core_web_sm
```

### 2. Set Up Golden Dataset

The golden dataset is located at `data/golden_dataset/questions.json`. It contains 15 example test cases covering various difficulty levels and capabilities.

You can add more test cases following the format:

```json
{
  "id": "unique_id",
  "question": "Your question here",
  "expected_answer": "Expected answer with citations",
  "ground_truth_numbers": {
    "key": value
  },
  "documents_needed": ["doc1.pdf"],
  "difficulty": "easy|medium|hard",
  "required_capabilities": ["factual_retrieval", "calculation", etc.]
}
```

### 3. Run Evaluation

```bash
# Full evaluation suite
poetry run python scripts/run_evals.py

# Quick evaluation (sample of 5 cases)
poetry run python scripts/run_evals.py --quick

# Set new baseline thresholds
poetry run python scripts/run_evals.py --baseline
```

### 4. View Results via API

```bash
# Get current metrics
curl http://localhost:8000/api/evals/metrics

# Get evaluation history
curl http://localhost:8000/api/evals/history

# Get dashboard data
curl http://localhost:8000/api/evals/dashboard

# Run evaluation via API
curl -X POST http://localhost:8000/api/evals/run
```

## Metrics Explained

### RAGAS Metrics

1. **Faithfulness** (0-1): Is the answer grounded in the retrieved context?
   - High score = answer uses only information from sources
   - Low score = answer contains hallucinations

2. **Answer Relevancy** (0-1): Does the answer address the question?
   - High score = answer directly addresses the query
   - Low score = answer is off-topic or irrelevant

3. **Context Precision** (0-1): Are relevant documents ranked highly?
   - High score = most relevant docs retrieved first
   - Low score = relevant docs buried in results

4. **Context Recall** (0-1): Were all necessary documents retrieved?
   - High score = all relevant info retrieved
   - Low score = missing important context

5. **Answer Correctness** (0-1): Is the answer factually correct?
   - Compares generated answer to ground truth
   - Considers both semantic and factual accuracy

### Custom Financial Metrics

1. **Numerical Accuracy** (0-1): Are numbers correct?
   - Extracts all numbers from answer and ground truth
   - Checks if they match within tolerance (default 1%)
   - Critical for financial accuracy

2. **Citation Quality** (0-1): Are sources properly cited?
   - Counts citations per sentence
   - Ideal: 0.5-1 citations per sentence
   - Format: `[doc_X]` or `[doc_X:chunk_Y]`

3. **Temporal Accuracy** (0-1): Are dates/periods correct?
   - Extracts dates (2023, Q3 2023, Jan 2024, etc.)
   - Checks if all ground truth dates appear in answer
   - Important for time-sensitive financial data

4. **Entity Accuracy** (0-1): Are entity names correct?
   - Uses spaCy NER to extract entities (companies, people, etc.)
   - Checks for missing or hallucinated entities
   - Prevents incorrect company/person names

### LLM Judge Scores

GPT-4 evaluates answers on 1-5 scale for:

1. **Correctness**: Factual accuracy vs. reference
2. **Completeness**: Addresses all aspects of question
3. **Clarity**: Well-structured and understandable
4. **Citation Quality**: Proper source attribution
5. **Overall**: Holistic quality assessment

## Thresholds

Default baseline thresholds (adjust based on your system):

```python
{
    'faithfulness': 0.85,
    'answer_relevancy': 0.90,
    'context_precision': 0.80,
    'numerical_accuracy': 0.95,  # Critical for finance
    'citation_rate': 0.80,
    'llm_judge_overall': 4.0
}
```

## Usage Examples

### Evaluate Single Query (Real-time)

```python
from src.evaluation.pipeline import EvaluationPipeline

eval_pipeline = EvaluationPipeline(rag, db, llm)

result = await eval_pipeline.evaluate_single_query(
    question="What was the revenue in Q3 2023?",
    answer="The revenue in Q3 2023 was $50 billion [doc_1].",
    ground_truth="Revenue was $50 billion in Q3 2023.",
    sources=[{"content": "Q3 2023 revenue: $50B"}]
)

print(result['overall_score'])  # 0.87
print(result['ragas'])          # RAGAS scores
print(result['custom'])         # Custom metrics
print(result['judge'])          # LLM judge scores
```

### Run Full Evaluation Suite

```python
from src.evaluation.pipeline import EvaluationPipeline

eval_pipeline = EvaluationPipeline(rag, db, llm)

result = await eval_pipeline.run_full_evaluation()

print(f"Test ID: {result['test_id']}")
print(f"Pass Rate: {result['pass_rate']*100:.1f}%")
print(f"Metrics: {result['metrics']}")
print(f"Regressions: {result['regressions']}")
```

### Add Test Cases Programmatically

```python
from src.evaluation.golden_set import GoldenDataset

golden = GoldenDataset()

golden.add_test_case({
    "id": "custom_001",
    "question": "What is the P/E ratio?",
    "expected_answer": "The P/E ratio is 25.3x.",
    "ground_truth_numbers": {"pe_ratio": 25.3},
    "difficulty": "medium",
    "required_capabilities": ["calculation"]
})
```

### Get Dataset Statistics

```python
from src.evaluation.golden_set import GoldenDataset

golden = GoldenDataset()
stats = golden.get_statistics()

print(f"Total cases: {stats['total_cases']}")
print(f"By difficulty: {stats['by_difficulty']}")
print(f"By capability: {stats['by_capability']}")
```

## Database Schema

Evaluation results are stored in `evaluation_runs` table:

```sql
CREATE TABLE evaluation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_id TEXT NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    metrics JSONB NOT NULL,
    total_cases INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    pass_rate DOUBLE PRECISION NOT NULL,
    regressions JSONB,
    improvements JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_evaluation_runs_timestamp ON evaluation_runs(timestamp DESC);
CREATE INDEX idx_evaluation_runs_test_id ON evaluation_runs(test_id);
```

## Best Practices

### 1. Start Small, Grow Dataset
- Begin with 10-20 high-quality test cases
- Add more as you discover edge cases
- Aim for 50-100 eventually

### 2. Diverse Test Cases
```python
# Cover all difficulty levels
easy_cases = golden.get_by_difficulty('easy')      # 30%
medium_cases = golden.get_by_difficulty('medium')  # 50%
hard_cases = golden.get_by_difficulty('hard')      # 20%

# Cover all capabilities
factual = golden.get_by_capability('factual_retrieval')
comparison = golden.get_by_capability('comparison')
calculation = golden.get_by_capability('calculation')
multi_hop = golden.get_by_capability('multi_hop_reasoning')
```

### 3. Balance Cost and Coverage
- Full evaluation on golden dataset: Run daily/weekly
- LLM judge on subset: Run on sample to save costs (default: 20 cases)
- Real-time eval on user queries: Track key metrics only

### 4. Monitor Trends
- Set up alerts for regressions (>5% drop in metrics)
- Track metrics over time to identify patterns
- Use dashboard to visualize performance

### 5. Iterate on Test Cases
- Add cases that expose system weaknesses
- Update ground truth as system improves
- Remove outdated or invalid test cases

## Scheduled Evaluation (Modal)

For production deployment with Modal:

```python
@stub.function(
    schedule=modal.Period(days=1),  # Run daily
    secrets=secrets
)
async def daily_regression():
    from src.evaluation.regression import run_scheduled_regression
    
    result = await run_scheduled_regression()
    
    if result['regressions']:
        # Send alert to Slack, email, etc.
        await send_alert(result)
    
    return result
```

## Troubleshooting

### No Test Cases Found
- Check that `data/golden_dataset/questions.json` exists and contains valid JSON
- Verify file path is correct (relative to backend directory)

### RAGAS Errors
- Ensure RAGAS is installed: `poetry install`
- Check that you have valid OpenAI API key for RAGAS metrics
- RAGAS requires context to be provided as list of strings

### spaCy Not Available
- Install model: `python -m spacy download en_core_web_sm`
- Entity accuracy will be disabled if spaCy is not available

### Database Connection Issues
- Verify Supabase credentials in `.env`
- Check that `evaluation_runs` table exists
- Results will still print to console if DB storage fails

## API Reference

### GET /api/evals/metrics
Get current evaluation metrics from latest run.

**Response:**
```json
{
  "overall_score": 0.87,
  "faithfulness": 0.89,
  "answer_relevancy": 0.91,
  "context_precision": 0.84,
  "context_recall": 0.82,
  "answer_correctness": 0.88,
  "retrieval_time_avg": 2.3,
  "total_queries": 150,
  "timestamp": "2024-01-18T10:00:00Z"
}
```

### POST /api/evals/run
Trigger a new evaluation run.

**Response:**
```json
{
  "id": "eval_20240118_100000",
  "status": "running",
  "started_at": "2024-01-18T10:00:00Z",
  "test_cases_count": 15,
  "message": "Evaluation started with 15 test cases..."
}
```

### GET /api/evals/history
Get historical evaluation results.

**Query Parameters:**
- `limit` (default: 10): Number of results to return

**Response:**
```json
{
  "evaluations": [
    {
      "id": "eval_20240118_100000",
      "metrics": {...},
      "test_cases_count": 15,
      "created_at": "2024-01-18T10:00:00Z"
    }
  ],
  "total": 5
}
```

### GET /api/evals/dashboard
Get comprehensive dashboard data.

**Response:**
```json
{
  "latest_metrics": {...},
  "trends": {
    "faithfulness": {
      "current": 0.89,
      "change": 0.02,
      "direction": "up"
    }
  },
  "history": {...},
  "pass_rate": 0.87,
  "last_updated": 1705574400.0
}
```

### GET /api/evals/golden-dataset/stats
Get golden dataset statistics.

**Response:**
```json
{
  "golden_dataset": {
    "total_cases": 15,
    "by_difficulty": {
      "easy": 5,
      "medium": 7,
      "hard": 3
    },
    "by_capability": {
      "factual_retrieval": 8,
      "calculation": 5,
      "comparison": 4
    }
  },
  "thresholds": {...}
}
```

## Contributing

To add new metrics:

1. Add metric calculation to appropriate evaluator class
2. Update `comprehensive_score()` in `custom_metrics.py`
3. Add threshold to `RegressionTestSuite.thresholds`
4. Update test cases to include ground truth for new metric
5. Add documentation to this README

## References

- [RAGAS Documentation](https://docs.ragas.io/)
- [Evaluation Guide](../docs/evaluation_implementation_guide.md)
- [Testing Guide](../docs/testing_guide.md)
