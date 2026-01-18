# Evaluation Framework Implementation Guide

## Overview

This document provides detailed implementation specifications for the comprehensive evaluation framework. This is **critical** for demonstrating the quality and reliability of your AI system.

**Location**: `backend/src/evaluation/`

**Files**:
- `ragas_eval.py` - RAGAS metrics integration
- `custom_metrics.py` - Financial-specific metrics
- `llm_judge.py` - LLM-as-judge implementation
- `golden_set.py` - Test dataset management
- `regression.py` - Regression testing suite

---

## 1. RAGAS Metrics Integration

**File**: `backend/src/evaluation/ragas_eval.py`

### What is RAGAS?
RAGAS (Retrieval-Augmented Generation Assessment) is a framework for evaluating RAG systems with five key metrics:
1. **Faithfulness**: Is the answer grounded in the context?
2. **Answer Relevancy**: Does the answer address the question?
3. **Context Precision**: Are the top-ranked contexts relevant?
4. **Context Recall**: Did we retrieve all necessary context?
5. **Answer Correctness**: Is the answer factually correct?

```python
from typing import List, Dict
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
from datasets import Dataset
import asyncio

class RAGASEvaluator:
    """
    Evaluate RAG system using RAGAS metrics.
    """
    
    def __init__(self, rag_pipeline, llm_provider):
        self.rag = rag_pipeline
        self.llm = llm_provider
        
        # RAGAS metrics
        self.metrics = [
            faithfulness,        # Answer grounded in context
            answer_relevancy,    # Answer addresses question
            context_precision,   # Relevant docs ranked high
            context_recall,      # All necessary docs retrieved
            answer_correctness   # Factually correct answer
        ]
    
    async def evaluate_test_set(self, test_cases: List[Dict]) -> Dict:
        """
        Evaluate RAG system on a test set.
        
        Args:
            test_cases: List of test cases with format:
                {
                    'question': str,
                    'ground_truth': str,
                    'document_ids': List[str]  # Optional
                }
        
        Returns:
            Dict with RAGAS scores and detailed results
        """
        
        # Prepare data for RAGAS
        data = {
            'question': [],
            'answer': [],
            'contexts': [],
            'ground_truth': []
        }
        
        # Run system on each test case
        for case in test_cases:
            # Query the RAG system
            result = await self.rag.query(
                query=case['question'],
                filters={'document_id': case.get('document_ids')} if case.get('document_ids') else None
            )
            
            # Collect data
            data['question'].append(case['question'])
            data['answer'].append(result.answer)
            data['contexts'].append([s['content'] for s in result.sources])
            data['ground_truth'].append(case['ground_truth'])
        
        # Convert to RAGAS dataset
        dataset = Dataset.from_dict(data)
        
        # Run RAGAS evaluation
        ragas_results = evaluate(
            dataset,
            metrics=self.metrics,
        )
        
        # Format results
        results = {
            'overall_scores': {
                'faithfulness': ragas_results['faithfulness'],
                'answer_relevancy': ragas_results['answer_relevancy'],
                'context_precision': ragas_results['context_precision'],
                'context_recall': ragas_results['context_recall'],
                'answer_correctness': ragas_results['answer_correctness']
            },
            'per_question_results': self._format_per_question_results(ragas_results, data),
            'num_questions': len(test_cases),
            'timestamp': time.time()
        }
        
        return results
    
    def _format_per_question_results(self, ragas_results, data) -> List[Dict]:
        """Format detailed per-question results."""
        
        per_question = []
        for i in range(len(data['question'])):
            per_question.append({
                'question': data['question'][i],
                'answer': data['answer'][i],
                'ground_truth': data['ground_truth'][i],
                'scores': {
                    'faithfulness': ragas_results['faithfulness'][i] if hasattr(ragas_results['faithfulness'], '__getitem__') else ragas_results['faithfulness'],
                    'answer_relevancy': ragas_results['answer_relevancy'][i] if hasattr(ragas_results['answer_relevancy'], '__getitem__') else ragas_results['answer_relevancy'],
                    'context_precision': ragas_results['context_precision'][i] if hasattr(ragas_results['context_precision'], '__getitem__') else ragas_results['context_precision'],
                    'context_recall': ragas_results['context_recall'][i] if hasattr(ragas_results['context_recall'], '__getitem__') else ragas_results['context_recall'],
                    'answer_correctness': ragas_results['answer_correctness'][i] if hasattr(ragas_results['answer_correctness'], '__getitem__') else ragas_results['answer_correctness']
                }
            })
        
        return per_question
    
    async def evaluate_single_query(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: str
    ) -> Dict:
        """
        Evaluate a single query-answer pair.
        Useful for real-time evaluation during demo.
        """
        
        dataset = Dataset.from_dict({
            'question': [question],
            'answer': [answer],
            'contexts': [contexts],
            'ground_truth': [ground_truth]
        })
        
        results = evaluate(dataset, metrics=self.metrics)
        
        return {
            'faithfulness': float(results['faithfulness']),
            'answer_relevancy': float(results['answer_relevancy']),
            'context_precision': float(results['context_precision']),
            'context_recall': float(results['context_recall']),
            'answer_correctness': float(results['answer_correctness'])
        }
```

---

## 2. Custom Financial Metrics

**File**: `backend/src/evaluation/custom_metrics.py`

### Why Custom Metrics?
RAGAS provides general RAG metrics, but financial documents have specific requirements:
- Numerical accuracy is critical
- Citations must be present
- Dates/periods must be correct
- Entity names (companies, people) must be accurate

```python
import re
from typing import List, Dict, Tuple
from datetime import datetime
import spacy

class FinancialMetrics:
    """
    Custom evaluation metrics for financial document Q&A.
    """
    
    def __init__(self):
        # Load spaCy for NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def numerical_accuracy(
        self,
        generated_answer: str,
        ground_truth: str,
        tolerance: float = 0.01
    ) -> Dict:
        """
        Check if numbers in generated answer match ground truth.
        
        Returns:
            {
                'score': 0.0-1.0,
                'total_numbers': int,
                'correct_numbers': int,
                'incorrect_numbers': List[Tuple[str, str]]  # (generated, expected)
            }
        """
        
        # Extract numbers from both texts
        gen_numbers = self._extract_numbers(generated_answer)
        truth_numbers = self._extract_numbers(ground_truth)
        
        if not truth_numbers:
            return {'score': 1.0, 'total_numbers': 0, 'correct_numbers': 0, 'incorrect_numbers': []}
        
        # Match numbers (order-based for now)
        correct = 0
        incorrect = []
        
        for i, truth_num in enumerate(truth_numbers):
            if i < len(gen_numbers):
                gen_num = gen_numbers[i]
                
                # Check if within tolerance
                if abs(gen_num - truth_num) <= tolerance:
                    correct += 1
                else:
                    incorrect.append((str(gen_num), str(truth_num)))
        
        score = correct / len(truth_numbers) if truth_numbers else 0.0
        
        return {
            'score': score,
            'total_numbers': len(truth_numbers),
            'correct_numbers': correct,
            'incorrect_numbers': incorrect
        }
    
    def citation_quality(self, generated_answer: str) -> Dict:
        """
        Evaluate citation quality in answer.
        
        Returns:
            {
                'has_citations': bool,
                'citation_count': int,
                'citation_rate': float,  # citations per sentence
                'score': 0.0-1.0
            }
        """
        
        # Count citations (format: [doc_X], [doc_X:chunk_Y], etc.)
        citation_pattern = r'\[doc_\d+[:\w-]*\]'
        citations = re.findall(citation_pattern, generated_answer)
        
        # Count sentences
        sentences = re.split(r'[.!?]+', generated_answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        has_citations = len(citations) > 0
        citation_count = len(citations)
        citation_rate = citation_count / len(sentences) if sentences else 0
        
        # Score based on citation rate
        # Ideal: 1-2 citations per sentence for factual content
        if citation_rate >= 0.5:
            score = 1.0
        elif citation_rate >= 0.3:
            score = 0.8
        elif citation_rate >= 0.1:
            score = 0.6
        elif has_citations:
            score = 0.4
        else:
            score = 0.0
        
        return {
            'has_citations': has_citations,
            'citation_count': citation_count,
            'citation_rate': citation_rate,
            'score': score
        }
    
    def temporal_accuracy(
        self,
        generated_answer: str,
        ground_truth: str
    ) -> Dict:
        """
        Check if dates and time periods are correct.
        
        Returns:
            {
                'score': 0.0-1.0,
                'dates_matched': int,
                'dates_total': int,
                'mismatches': List[str]
            }
        """
        
        # Extract dates from both
        gen_dates = self._extract_dates(generated_answer)
        truth_dates = self._extract_dates(ground_truth)
        
        if not truth_dates:
            return {'score': 1.0, 'dates_matched': 0, 'dates_total': 0, 'mismatches': []}
        
        # Check if all truth dates appear in generated answer
        matched = 0
        mismatches = []
        
        for truth_date in truth_dates:
            if truth_date in gen_dates:
                matched += 1
            else:
                mismatches.append(truth_date)
        
        score = matched / len(truth_dates) if truth_dates else 1.0
        
        return {
            'score': score,
            'dates_matched': matched,
            'dates_total': len(truth_dates),
            'mismatches': mismatches
        }
    
    def entity_accuracy(
        self,
        generated_answer: str,
        ground_truth: str
    ) -> Dict:
        """
        Check if entities (companies, people, locations) are correct.
        
        Uses spaCy NER to extract entities.
        
        Returns:
            {
                'score': 0.0-1.0,
                'entities_matched': int,
                'entities_total': int,
                'missing_entities': List[str],
                'incorrect_entities': List[str]
            }
        """
        
        if not self.nlp:
            return {'score': 1.0, 'error': 'spaCy not available'}
        
        # Extract entities
        gen_entities = self._extract_entities(generated_answer)
        truth_entities = self._extract_entities(ground_truth)
        
        if not truth_entities:
            return {'score': 1.0, 'entities_matched': 0, 'entities_total': 0, 'missing_entities': [], 'incorrect_entities': []}
        
        # Check matches
        matched = 0
        missing = []
        incorrect = []
        
        for truth_entity in truth_entities:
            if truth_entity in gen_entities:
                matched += 1
            else:
                missing.append(truth_entity)
        
        # Check for hallucinated entities
        for gen_entity in gen_entities:
            if gen_entity not in truth_entities:
                incorrect.append(gen_entity)
        
        score = matched / len(truth_entities) if truth_entities else 1.0
        
        return {
            'score': score,
            'entities_matched': matched,
            'entities_total': len(truth_entities),
            'missing_entities': missing,
            'incorrect_entities': incorrect
        }
    
    def comprehensive_score(
        self,
        generated_answer: str,
        ground_truth: str
    ) -> Dict:
        """
        Calculate comprehensive custom metrics score.
        
        Combines all custom metrics with weights.
        """
        
        numerical = self.numerical_accuracy(generated_answer, ground_truth)
        citation = self.citation_quality(generated_answer)
        temporal = self.temporal_accuracy(generated_answer, ground_truth)
        entity = self.entity_accuracy(generated_answer, ground_truth)
        
        # Weighted average
        weights = {
            'numerical': 0.35,
            'citation': 0.25,
            'temporal': 0.20,
            'entity': 0.20
        }
        
        overall_score = (
            weights['numerical'] * numerical['score'] +
            weights['citation'] * citation['score'] +
            weights['temporal'] * temporal['score'] +
            weights['entity'] * entity['score']
        )
        
        return {
            'overall_score': overall_score,
            'numerical_accuracy': numerical,
            'citation_quality': citation,
            'temporal_accuracy': temporal,
            'entity_accuracy': entity
        }
    
    # Helper methods
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all numbers from text."""
        # Pattern for numbers with commas, decimals, percentages
        pattern = r'-?\d+(?:,\d{3})*(?:\.\d+)?%?'
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            # Clean and convert
            clean = match.replace(',', '').replace('%', '')
            try:
                numbers.append(float(clean))
            except:
                pass
        
        return numbers
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        # Common date patterns
        patterns = [
            r'\b\d{4}\b',  # Year (2023)
            r'\b(?:Q[1-4])\s+\d{4}\b',  # Quarter (Q3 2023)
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month Day, Year
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
        ]
        
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(dates))  # Remove duplicates
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities using spaCy."""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON', 'GPE', 'MONEY', 'PERCENT']:
                entities.append(ent.text)
        
        return list(set(entities))
```

---

## 3. LLM-as-Judge

**File**: `backend/src/evaluation/llm_judge.py`

### Why LLM-as-Judge?
- Automated human-like evaluation
- Evaluates aspects hard to measure programmatically (clarity, coherence)
- Provides qualitative feedback
- Scales better than human evaluation

```python
from typing import Dict
import json

class LLMJudge:
    """
    Use GPT-4 to evaluate answer quality.
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.judge_model = "gpt-4o"  # Use best model for judging
    
    async def evaluate_answer(
        self,
        question: str,
        generated_answer: str,
        ground_truth: str,
        sources: List[Dict] = None
    ) -> Dict:
        """
        Evaluate answer quality using LLM.
        
        Returns scores and reasoning for:
        - Correctness
        - Completeness
        - Clarity
        - Citation quality
        """
        
        # Build evaluation prompt
        prompt = self._build_judge_prompt(
            question,
            generated_answer,
            ground_truth,
            sources
        )
        
        # Get structured output from LLM
        judgment = await self.llm.structured_output(
            prompt,
            schema=JudgmentSchema,
            model=self.judge_model
        )
        
        return judgment
    
    def _build_judge_prompt(
        self,
        question: str,
        generated_answer: str,
        ground_truth: str,
        sources: List[Dict]
    ) -> str:
        """Build the judge evaluation prompt."""
        
        sources_str = ""
        if sources:
            sources_str = "\n\nSource Documents:\n" + "\n".join([
                f"[{i}] {s['content'][:200]}..."
                for i, s in enumerate(sources[:5])
            ])
        
        prompt = f"""You are an expert evaluator assessing the quality of AI-generated answers to financial questions.

**Question**: {question}

**Generated Answer**: 
{generated_answer}

**Reference Answer** (ground truth):
{ground_truth}
{sources_str}

**Evaluation Criteria**:

1. **Correctness** (1-5): Is the answer factually correct compared to the reference?
   - 5: Completely correct, all facts accurate
   - 4: Mostly correct, minor inaccuracies
   - 3: Partially correct, some significant errors
   - 2: Mostly incorrect
   - 1: Completely incorrect

2. **Completeness** (1-5): Does the answer address all aspects of the question?
   - 5: Fully complete, nothing missing
   - 4: Mostly complete, minor omissions
   - 3: Partially complete, missing some important points
   - 2: Significantly incomplete
   - 1: Barely addresses the question

3. **Clarity** (1-5): Is the answer clear, well-structured, and easy to understand?
   - 5: Exceptionally clear and well-organized
   - 4: Clear and understandable
   - 3: Somewhat clear but could be improved
   - 2: Confusing or poorly organized
   - 1: Very unclear

4. **Citation Quality** (1-5): Are sources properly cited?
   - 5: All claims cited with specific sources
   - 4: Most claims cited
   - 3: Some citations present
   - 2: Very few citations
   - 1: No citations

**Return a JSON object**:
{{
    "correctness": 1-5,
    "completeness": 1-5,
    "clarity": 1-5,
    "citation_quality": 1-5,
    "overall": 1-5,
    "reasoning": "Brief explanation of the scores"
}}

Your evaluation:"""
        
        return prompt
    
    async def batch_evaluate(
        self,
        test_cases: List[Dict]
    ) -> List[Dict]:
        """
        Evaluate multiple test cases.
        
        Args:
            test_cases: List of {question, answer, ground_truth, sources}
        
        Returns:
            List of judgment dicts
        """
        
        results = []
        for case in test_cases:
            judgment = await self.evaluate_answer(
                question=case['question'],
                generated_answer=case['answer'],
                ground_truth=case['ground_truth'],
                sources=case.get('sources', [])
            )
            results.append(judgment)
        
        return results
    
    def aggregate_scores(self, judgments: List[Dict]) -> Dict:
        """Aggregate scores across multiple judgments."""
        
        if not judgments:
            return {}
        
        metrics = ['correctness', 'completeness', 'clarity', 'citation_quality', 'overall']
        
        aggregated = {}
        for metric in metrics:
            scores = [j[metric] for j in judgments if metric in j]
            if scores:
                aggregated[f'avg_{metric}'] = sum(scores) / len(scores)
                aggregated[f'min_{metric}'] = min(scores)
                aggregated[f'max_{metric}'] = max(scores)
        
        return aggregated


# Pydantic schema for structured output
from pydantic import BaseModel

class JudgmentSchema(BaseModel):
    correctness: int
    completeness: int
    clarity: int
    citation_quality: int
    overall: int
    reasoning: str
```

---

## 4. Golden Dataset Management

**File**: `backend/src/evaluation/golden_set.py`

### Structure of Golden Dataset

```python
import json
from typing import List, Dict
from pathlib import Path

class GoldenDataset:
    """
    Manage the golden evaluation dataset.
    """
    
    def __init__(self, dataset_path: str = "data/golden_dataset/questions.json"):
        self.dataset_path = Path(dataset_path)
        self.test_cases = self._load_dataset()
    
    def _load_dataset(self) -> List[Dict]:
        """Load golden dataset from JSON."""
        if not self.dataset_path.exists():
            print(f"Warning: Golden dataset not found at {self.dataset_path}")
            return []
        
        with open(self.dataset_path, 'r') as f:
            return json.load(f)
    
    def get_all_cases(self) -> List[Dict]:
        """Get all test cases."""
        return self.test_cases
    
    def get_by_difficulty(self, difficulty: str) -> List[Dict]:
        """
        Get test cases by difficulty level.
        
        Args:
            difficulty: 'easy', 'medium', or 'hard'
        """
        return [
            case for case in self.test_cases
            if case.get('difficulty') == difficulty
        ]
    
    def get_by_capability(self, capability: str) -> List[Dict]:
        """
        Get test cases requiring specific capability.
        
        Args:
            capability: e.g., 'multi_doc', 'calculation', 'comparison'
        """
        return [
            case for case in self.test_cases
            if capability in case.get('required_capabilities', [])
        ]
    
    def add_test_case(self, test_case: Dict):
        """Add a new test case to the dataset."""
        self.test_cases.append(test_case)
        self._save_dataset()
    
    def _save_dataset(self):
        """Save dataset to JSON."""
        with open(self.dataset_path, 'w') as f:
            json.dump(self.test_cases, f, indent=2)
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics."""
        difficulties = {}
        capabilities = {}
        
        for case in self.test_cases:
            # Count by difficulty
            diff = case.get('difficulty', 'unknown')
            difficulties[diff] = difficulties.get(diff, 0) + 1
            
            # Count by capability
            for cap in case.get('required_capabilities', []):
                capabilities[cap] = capabilities.get(cap, 0) + 1
        
        return {
            'total_cases': len(self.test_cases),
            'by_difficulty': difficulties,
            'by_capability': capabilities
        }


# Example golden dataset structure
EXAMPLE_GOLDEN_DATASET = [
    {
        "id": "factual_001",
        "question": "What was Apple's total revenue in fiscal year 2023?",
        "expected_answer": "Apple's total revenue in fiscal year 2023 was $383.9 billion.",
        "ground_truth_numbers": {
            "revenue": 383.9
        },
        "documents_needed": ["apple_10k_2023.pdf"],
        "difficulty": "easy",
        "required_capabilities": ["factual_retrieval"]
    },
    {
        "id": "comparison_001",
        "question": "Compare Apple and Microsoft's R&D spending as a percentage of revenue in 2023.",
        "expected_answer": "Apple spent $29.9B on R&D (7.8% of revenue), while Microsoft spent $27.2B (12.8% of revenue). Microsoft invested a higher percentage despite lower absolute dollars.",
        "ground_truth_numbers": {
            "apple_rd": 29.9,
            "apple_revenue": 383.9,
            "apple_percentage": 7.8,
            "msft_rd": 27.2,
            "msft_revenue": 211.9,
            "msft_percentage": 12.8
        },
        "documents_needed": ["apple_10k_2023.pdf", "msft_10k_2023.pdf"],
        "difficulty": "medium",
        "required_capabilities": ["multi_doc_retrieval", "calculation", "comparison"]
    },
    {
        "id": "multi_hop_001",
        "question": "What was Amazon's AWS operating margin in 2023, and how does it compare to their overall operating margin? What does this tell us about AWS's business?",
        "expected_answer": "AWS had an operating margin of 30.3% compared to Amazon's overall margin of 5.7%. This 24.6 percentage point difference indicates AWS is significantly more profitable than Amazon's retail operations and effectively subsidizes lower-margin businesses.",
        "ground_truth_numbers": {
            "aws_margin": 30.3,
            "overall_margin": 5.7,
            "difference": 24.6
        },
        "documents_needed": ["amazon_10k_2023.pdf"],
        "difficulty": "hard",
        "required_capabilities": ["multi_hop_reasoning", "calculation", "interpretation"]
    }
]
```

---

## 5. Regression Testing Suite

**File**: `backend/src/evaluation/regression.py`

### Purpose
- Detect quality degradation when making changes
- Track metrics over time
- Alert when performance drops

```python
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
        
        # Count pass/fail
        passed = len(test_cases) - len([m for m in metrics.values() if m < 0.7])
        failed = len(test_cases) - passed
        
        # Store results
        result = {
            'test_id': test_id,
            'timestamp': datetime.now().timestamp(),
            'total_cases': len(test_cases),
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / len(test_cases) if test_cases else 0,
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
            result = await self.rag.query(case['question'])
            
            # Numerical accuracy
            num_result = self.custom.numerical_accuracy(
                result.answer,
                case['expected_answer']
            )
            numerical_scores.append(num_result['score'])
            
            # Citation quality
            cit_result = self.custom.citation_quality(result.answer)
            citation_rates.append(cit_result['citation_rate'])
        
        return {
            'numerical_accuracy': sum(numerical_scores) / len(numerical_scores) if numerical_scores else 0,
            'citation_rate': sum(citation_rates) / len(citation_rates) if citation_rates else 0
        }
    
    async def _evaluate_with_judge(self, test_cases: List[Dict]) -> Dict:
        """Evaluate with LLM judge on sample."""
        
        judgments = []
        
        for case in test_cases:
            result = await self.rag.query(case['question'])
            
            judgment = await self.judge.evaluate_answer(
                question=case['question'],
                generated_answer=result.answer,
                ground_truth=case['expected_answer'],
                sources=result.sources
            )
            judgments.append(judgment)
        
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
        })
    
    def _print_summary(self, result: Dict):
        """Print human-readable summary."""
        
        print("\n" + "="*60)
        print(f"Regression Test Results: {result['test_id']}")
        print("="*60)
        print(f"\nTotal Cases: {result['total_cases']}")
        print(f"Passed: {result['passed']} ({result['pass_rate']*100:.1f}%)")
        print(f"Failed: {result['failed']}")
        
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
        
        # Get baseline (first test run)
        baseline = await self.db.table('evaluation_runs').select('*').order('timestamp').limit(1).single()
        
        # Get current test
        current = await self.db.table('evaluation_runs').select('*').eq('test_id', test_id).single()
        
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


# Scheduled regression testing (for Modal)
async def run_scheduled_regression():
    """
    Run regression tests on a schedule (e.g., daily).
    Called by Modal scheduled function.
    """
    
    from src.db.supabase import get_supabase_client
    from src.llm.provider import LLMProvider
    from src.rag.pipeline import RAGPipeline
    from src.evaluation.golden_set import GoldenDataset
    from src.evaluation.ragas_eval import RAGASEvaluator
    from src.evaluation.custom_metrics import FinancialMetrics
    from src.evaluation.llm_judge import LLMJudge
    
    # Initialize components
    db = get_supabase_client()
    llm = LLMProvider()
    rag = RAGPipeline(db, llm)
    golden = GoldenDataset()
    ragas_eval = RAGASEvaluator(rag, llm)
    custom_metrics = FinancialMetrics()
    judge = LLMJudge(llm)
    
    # Create test suite
    suite = RegressionTestSuite(
        rag, golden, ragas_eval, custom_metrics, judge, db
    )
    
    # Run tests
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
```

---

## 6. Complete Evaluation Pipeline

**File**: `backend/src/evaluation/pipeline.py`

```python
from typing import Dict, List
import asyncio

class EvaluationPipeline:
    """
    Orchestrate all evaluation components.
    """
    
    def __init__(
        self,
        rag_pipeline,
        db_client,
        llm_provider
    ):
        from .ragas_eval import RAGASEvaluator
        from .custom_metrics import FinancialMetrics
        from .llm_judge import LLMJudge
        from .golden_set import GoldenDataset
        from .regression import RegressionTestSuite
        
        self.rag = rag_pipeline
        self.db = db_client
        self.llm = llm_provider
        
        # Initialize evaluators
        self.ragas = RAGASEvaluator(rag_pipeline, llm_provider)
        self.custom = FinancialMetrics()
        self.judge = LLMJudge(llm_provider)
        self.golden = GoldenDataset()
        self.regression = RegressionTestSuite(
            rag_pipeline, self.golden, self.ragas,
            self.custom, self.judge, db_client
        )
    
    async def evaluate_single_query(
        self,
        question: str,
        answer: str,
        ground_truth: str,
        sources: List[Dict]
    ) -> Dict:
        """
        Comprehensive evaluation of a single query.
        
        Returns all metrics for immediate feedback.
        """
        
        # Run all evaluations in parallel
        ragas_task = self.ragas.evaluate_single_query(
            question, answer,
            [s['content'] for s in sources],
            ground_truth
        )
        
        custom_task = asyncio.create_task(
            self._evaluate_custom_single(answer, ground_truth)
        )
        
        judge_task = self.judge.evaluate_answer(
            question, answer, ground_truth, sources
        )
        
        # Wait for all
        ragas_scores, custom_scores, judge_scores = await asyncio.gather(
            ragas_task, custom_task, judge_task
        )
        
        return {
            'ragas': ragas_scores,
            'custom': custom_scores,
            'judge': judge_scores,
            'overall_score': self._calculate_overall_score(
                ragas_scores, custom_scores, judge_scores
            )
        }
    
    async def _evaluate_custom_single(
        self,
        answer: str,
        ground_truth: str
    ) -> Dict:
        """Evaluate custom metrics for single answer."""
        
        return self.custom.comprehensive_score(answer, ground_truth)
    
    def _calculate_overall_score(
        self,
        ragas: Dict,
        custom: Dict,
        judge: Dict
    ) -> float:
        """
        Calculate weighted overall score.
        
        Weights:
        - RAGAS: 40%
        - Custom: 35%
        - Judge: 25%
        """
        
        # Average RAGAS metrics
        ragas_avg = sum(ragas.values()) / len(ragas) if ragas else 0
        
        # Custom overall
        custom_score = custom.get('overall_score', 0)
        
        # Judge overall (normalize from 1-5 to 0-1)
        judge_score = judge.get('overall', 3) / 5.0
        
        overall = (
            0.40 * ragas_avg +
            0.35 * custom_score +
            0.25 * judge_score
        )
        
        return overall
    
    async def run_full_evaluation(self) -> Dict:
        """
        Run complete evaluation suite.
        
        This is the main method to call for comprehensive evaluation.
        """
        
        result = await self.regression.run_full_suite()
        return result
    
    async def get_evaluation_history(self, limit: int = 10) -> List[Dict]:
        """Get historical evaluation results."""
        
        results = await self.db.table('evaluation_runs')\
            .select('*')\
            .order('timestamp', desc=True)\
            .limit(limit)\
            .execute()
        
        return results.data if results else []
    
    async def get_metrics_dashboard_data(self) -> Dict:
        """
        Get data for metrics dashboard.
        
        Returns aggregated metrics, trends, and highlights.
        """
        
        # Get recent evaluations
        history = await self.get_evaluation_history(limit=30)
        
        if not history:
            return {'error': 'No evaluation data available'}
        
        # Extract metrics over time
        metrics_over_time = {}
        for run in history:
            metrics = json.loads(run['metrics'])
            timestamp = run['timestamp']
            
            for metric, value in metrics.items():
                if metric not in metrics_over_time:
                    metrics_over_time[metric] = []
                metrics_over_time[metric].append({
                    'timestamp': timestamp,
                    'value': value
                })
        
        # Calculate trends
        trends = {}
        for metric, values in metrics_over_time.items():
            if len(values) >= 2:
                recent = values[0]['value']
                older = values[-1]['value']
                change = recent - older
                trends[metric] = {
                    'current': recent,
                    'change': change,
                    'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable'
                }
        
        # Latest metrics
        latest = json.loads(history[0]['metrics'])
        
        return {
            'latest_metrics': latest,
            'trends': trends,
            'history': metrics_over_time,
            'pass_rate': history[0]['pass_rate'],
            'last_updated': history[0]['timestamp']
        }
```

---

## 7. FastAPI Endpoints for Evaluation

**File**: `backend/src/api/routes/evals.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from src.evaluation.pipeline import EvaluationPipeline

router = APIRouter(prefix="/api/evals", tags=["evaluation"])

@router.get("/metrics")
async def get_metrics(
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
) -> Dict:
    """
    Get current evaluation metrics and trends.
    
    Returns metrics dashboard data.
    """
    
    data = await eval_pipeline.get_metrics_dashboard_data()
    return data


@router.post("/run")
async def run_evaluation(
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
) -> Dict:
    """
    Run full evaluation suite manually.
    
    Use this to test after making changes.
    """
    
    result = await eval_pipeline.run_full_evaluation()
    return result


@router.get("/history")
async def get_evaluation_history(
    limit: int = 10,
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
) -> List[Dict]:
    """
    Get historical evaluation results.
    """
    
    history = await eval_pipeline.get_evaluation_history(limit=limit)
    return history


@router.post("/evaluate-query")
async def evaluate_single_query(
    question: str,
    answer: str,
    ground_truth: str,
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
) -> Dict:
    """
    Evaluate a single query in real-time.
    
    Useful during demos to show evaluation live.
    """
    
    result = await eval_pipeline.evaluate_single_query(
        question=question,
        answer=answer,
        ground_truth=ground_truth,
        sources=[]
    )
    
    return result


@router.get("/golden-dataset/stats")
async def get_golden_dataset_stats(
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
) -> Dict:
    """Get statistics about the golden dataset."""
    
    stats = eval_pipeline.golden.get_statistics()
    return stats
```

---

## 8. Frontend: Metrics Dashboard

**File**: `frontend/src/components/MetricsDashboard.tsx`

```typescript
import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricsData {
  latest_metrics: Record<string, number>;
  trends: Record<string, { current: number; change: number; direction: string }>;
  pass_rate: number;
  last_updated: number;
}

export function MetricsDashboard() {
  const [data, setData] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/evals/metrics');
      const metricsData = await response.json();
      setData(metricsData);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading metrics...</div>;
  }

  if (!data) {
    return <div>No evaluation data available</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Evaluation Metrics</h2>
        <div className="text-sm text-gray-500">
          Last updated: {new Date(data.last_updated * 1000).toLocaleString()}
        </div>
      </div>

      {/* Overall Pass Rate */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-2">Overall Pass Rate</h3>
        <div className="text-4xl font-bold text-green-600">
          {(data.pass_rate * 100).toFixed(1)}%
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(data.latest_metrics).map(([metric, value]) => (
          <MetricCard
            key={metric}
            name={metric}
            value={value}
            trend={data.trends[metric]}
          />
        ))}
      </div>

      {/* Trend Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Metrics Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={prepareChartData(data)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[0, 1]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="faithfulness" stroke="#8884d8" />
            <Line type="monotone" dataKey="answer_relevancy" stroke="#82ca9d" />
            <Line type="monotone" dataKey="numerical_accuracy" stroke="#ffc658" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function MetricCard({ name, value, trend }: any) {
  const getTrendIcon = () => {
    if (!trend) return <Minus className="w-4 h-4" />;
    if (trend.direction === 'up') return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (trend.direction === 'down') return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const formatMetricName = (name: string) => {
    return name.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-medium text-gray-600">
          {formatMetricName(name)}
        </h4>
        {getTrendIcon()}
      </div>
      <div className="text-2xl font-bold">
        {value.toFixed(3)}
      </div>
      {trend && (
        <div className={`text-sm mt-1 ${
          trend.direction === 'up' ? 'text-green-600' : 
          trend.direction === 'down' ? 'text-red-600' : 
          'text-gray-500'
        }`}>
          {trend.change > 0 ? '+' : ''}{(trend.change * 100).toFixed(1)}%
        </div>
      )}
    </div>
  );
}

function prepareChartData(data: MetricsData) {
  // Transform data for chart
  // This would come from the history endpoint in production
  return [];
}
```

---

## 9. Example: Running Evaluations

### Initial Setup
```bash
# Create golden dataset
python scripts/create_golden_dataset.py

# Run first evaluation (establishes baseline)
python scripts/run_evals.py
```

### Daily Regression Testing (Modal)
```python
# In modal_app.py
@stub.function(
    schedule=modal.Period(days=1),  # Run daily at midnight
    secrets=secrets
)
async def daily_regression():
    from src.evaluation.regression import run_scheduled_regression
    
    result = await run_scheduled_regression()
    
    # Alert if regressions
    if result['regressions']:
        print(f"⚠️  {len(result['regressions'])} regressions detected")
    
    return result
```

### Manual Testing After Changes
```python
# After making changes to prompts, retrieval, etc.
from src.evaluation.pipeline import EvaluationPipeline

eval_pipeline = EvaluationPipeline(rag, db, llm)
result = await eval_pipeline.run_full_evaluation()

if result['regressions']:
    print("Regressions detected - fix before deploying!")
else:
    print("All tests passed - safe to deploy")
```

---

## 10. Best Practices

### 1. Start Small, Grow Dataset
```python
# Start with 10-20 high-quality test cases
# Add more as you discover edge cases
# Aim for 50-100 eventually
```

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

### 3. Track Metrics Over Time
```sql
-- Query to see metric trends
SELECT 
    DATE(timestamp) as date,
    AVG((metrics->>'faithfulness')::float) as avg_faithfulness,
    AVG((metrics->>'numerical_accuracy')::float) as avg_numerical
FROM evaluation_runs
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date;
```

### 4. Set Realistic Thresholds
```python
# Don't aim for perfection
# Set thresholds based on actual performance
thresholds = {
    'faithfulness': 0.85,      # 85% is excellent
    'answer_relevancy': 0.90,  # Should be high
    'numerical_accuracy': 0.95,  # Critical for finance
    'citation_rate': 0.80,     # Most answers should cite
}
```

### 5. Balance Cost and Coverage
```python
# Full evaluation on golden dataset: Run daily/weekly
# LLM judge on subset: Run on sample to save costs
# Real-time eval on user queries: Track key metrics only

if is_production_query:
    # Light evaluation
    quick_metrics = {
        'has_citations': check_citations(answer),
        'answer_length': len(answer),
        'latency': response_time
    }
else:
    # Full evaluation
    full_metrics = await eval_pipeline.evaluate_single_query(...)
```

---

## Summary

This evaluation framework provides:

✅ **RAGAS Integration**: Industry-standard RAG metrics  
✅ **Custom Financial Metrics**: Numerical accuracy, citations, temporal/entity accuracy  
✅ **LLM-as-Judge**: Automated qualitative evaluation  
✅ **Golden Dataset**: Structured test cases with ground truth  
✅ **Regression Testing**: Automated quality monitoring  
✅ **Metrics Dashboard**: Visual tracking of performance  
✅ **API Endpoints**: Easy integration with frontend  
✅ **Cost-Effective**: Sample-based evaluation where appropriate  

**With all four documents (plan.md + agents-implementation.md + rag-implementation.md + evaluation-implementation.md), you have complete, production-ready specifications for every component!**

🎯 **Total Documentation: ~20,000 words of detailed implementation guides**

Ready to start building? Which component do you want to implement first?