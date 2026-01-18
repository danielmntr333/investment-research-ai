"""Evaluation endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

from src.db.supabase import get_supabase
from src.evaluation.pipeline import EvaluationPipeline
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/api/evals", tags=["evaluation"])


# Dependency to get evaluation pipeline
async def get_eval_pipeline() -> EvaluationPipeline:
    """Get evaluation pipeline instance."""
    try:
        db = get_supabase()
        llm = LLMProvider()
        rag = RAGPipeline(llm_provider=llm)
        
        return EvaluationPipeline(rag, db, llm)
    except Exception as e:
        print(f"Error initializing evaluation pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize evaluation pipeline: {str(e)}"
        )


class MetricsResponse(BaseModel):
    """Evaluation metrics response."""
    overall_score: float
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    answer_correctness: float
    retrieval_time_avg: float
    total_queries: int
    timestamp: str


class EvaluationRunResponse(BaseModel):
    """Evaluation run response."""
    id: str
    status: str
    started_at: str
    test_cases_count: int
    message: str


class EvaluationHistoryItem(BaseModel):
    """Single evaluation history item."""
    id: str
    metrics: Dict
    test_cases_count: int
    created_at: str


class EvaluationHistoryResponse(BaseModel):
    """Evaluation history response."""
    evaluations: List[EvaluationHistoryItem]
    total: int


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
):
    """
    Get current evaluation metrics.
    
    This returns aggregated metrics from recent evaluation runs.
    """
    try:
        # Get dashboard data from evaluation pipeline
        dashboard_data = await eval_pipeline.get_metrics_dashboard_data()
        
        if 'error' in dashboard_data:
            # Return default metrics if no data available
            return MetricsResponse(
                overall_score=0.0,
                faithfulness=0.0,
                answer_relevancy=0.0,
                context_precision=0.0,
                context_recall=0.0,
                answer_correctness=0.0,
                retrieval_time_avg=0.0,
                total_queries=0,
                timestamp=datetime.utcnow().isoformat()
            )
        
        latest = dashboard_data['latest_metrics']
        
        # Build metrics response
        metrics = MetricsResponse(
            overall_score=latest.get('faithfulness', 0.0),  # Use faithfulness as proxy for overall
            faithfulness=latest.get('faithfulness', 0.0),
            answer_relevancy=latest.get('answer_relevancy', 0.0),
            context_precision=latest.get('context_precision', 0.0),
            context_recall=latest.get('context_recall', 0.0),
            answer_correctness=latest.get('answer_correctness', 0.0),
            retrieval_time_avg=latest.get('retrieval_time_avg', 0.0),
            total_queries=latest.get('total_queries', 0),
            timestamp=datetime.utcnow().isoformat()
        )
        
        return metrics
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.post("/run", response_model=EvaluationRunResponse)
async def run_evaluation(
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
):
    """
    Run evaluation on test set.
    
    This triggers a full evaluation run on the golden dataset.
    """
    try:
        # Get test case count
        stats = eval_pipeline.get_statistics()
        test_cases_count = stats['golden_dataset']['total_cases']
        
        eval_id = f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Run evaluation asynchronously (in background)
        # For now, we'll queue it and return immediately
        # In production, use background tasks or celery
        import asyncio
        asyncio.create_task(eval_pipeline.run_full_evaluation())
        
        return EvaluationRunResponse(
            id=eval_id,
            status="running",
            started_at=datetime.utcnow().isoformat(),
            test_cases_count=test_cases_count,
            message=f"Evaluation started with {test_cases_count} test cases. Check /api/evals/history for results."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start evaluation: {str(e)}"
        )


@router.get("/history", response_model=EvaluationHistoryResponse)
async def get_evaluation_history(
    limit: int = Query(default=10, ge=1, le=100, description="Number of evaluations to return"),
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
):
    """
    Get evaluation history.
    
    Returns past evaluation runs with their metrics.
    """
    try:
        # Get history from evaluation pipeline
        history = await eval_pipeline.get_evaluation_history(limit=limit)
        
        if history:
            evaluations = [
                EvaluationHistoryItem(
                    id=eval_data.get('test_id', str(eval_data.get('id', ''))),
                    metrics=eval_data.get('metrics', {}),
                    test_cases_count=eval_data.get('total_cases', 0),
                    created_at=datetime.fromtimestamp(eval_data.get('timestamp', 0)).isoformat() if eval_data.get('timestamp') else ''
                )
                for eval_data in history
            ]
            
            return EvaluationHistoryResponse(
                evaluations=evaluations,
                total=len(evaluations)
            )
        
        # Return empty if no data
        return EvaluationHistoryResponse(
            evaluations=[],
            total=0
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get evaluation history: {str(e)}"
        )


@router.get("/golden-dataset/stats")
async def get_golden_dataset_stats(
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
):
    """Get statistics about the golden dataset."""
    try:
        stats = eval_pipeline.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get golden dataset stats: {str(e)}"
        )


@router.get("/dashboard")
async def get_dashboard_data(
    eval_pipeline: EvaluationPipeline = Depends(get_eval_pipeline)
):
    """
    Get comprehensive dashboard data including metrics, trends, and history.
    """
    try:
        dashboard_data = await eval_pipeline.get_metrics_dashboard_data()
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard data: {str(e)}"
        )
