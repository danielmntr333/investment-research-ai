"""Multi-document analysis endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from src.agents.graph import ResearchAgentGraph
from src.db.supabase import get_supabase
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/api/analyze", tags=["analysis"])


class CompareRequest(BaseModel):
    """Multi-document comparison request."""
    query: str = Field(..., description="Comparison query")
    document_ids: List[str] = Field(..., description="List of document IDs to compare")


class CompareResponse(BaseModel):
    """Comparison response."""
    answer: str
    citations: List[Dict]
    confidence_score: float
    documents_analyzed: List[str]
    execution_time: float


class SummarizeRequest(BaseModel):
    """Document summarization request."""
    document_id: str = Field(..., description="Document ID to summarize")
    summary_type: str = Field(default="comprehensive", description="Type: comprehensive, executive, key_points")


class SummarizeResponse(BaseModel):
    """Summarization response."""
    summary: str
    document_id: str
    metadata: Dict


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(request: CompareRequest):
    """
    Multi-document comparison analysis.
    
    Uses the agent system to intelligently compare documents and extract insights.
    """
    try:
        if len(request.document_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 documents are required for comparison"
            )
        
        # Initialize agent system
        db = get_supabase()
        llm = LLMProvider()
        rag = RAGPipeline()
        agent_graph = ResearchAgentGraph(db, llm, rag)
        
        # Execute comparison using agents
        result = await agent_graph.arun(
            query=request.query,
            chat_history=[],
            document_ids=request.document_ids
        )
        
        return CompareResponse(
            answer=result['final_answer'],
            citations=result['citations'],
            confidence_score=result['confidence_score'],
            documents_analyzed=request.document_ids,
            execution_time=result['execution_time']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_document(request: SummarizeRequest):
    """
    Document summarization.
    
    Generates a summary of the specified document.
    """
    try:
        db = get_supabase()
        
        # Check if document exists
        doc_result = db.table('documents').select('*').eq('id', request.document_id).execute()
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_result.data[0]
        
        # Get document chunks
        chunks_result = db.table('document_chunks').select('content').eq('document_id', request.document_id).order('chunk_index').execute()
        
        if not chunks_result.data:
            raise HTTPException(status_code=400, detail="Document has no content")
        
        # Combine chunks
        full_text = "\n\n".join([chunk['content'] for chunk in chunks_result.data])
        
        # Generate summary based on type
        llm = LLMProvider()
        
        if request.summary_type == "executive":
            user_prompt = f"""Provide a brief executive summary (2-3 paragraphs) of the following document:

{full_text[:8000]}

Focus on the most important insights and key takeaways."""
        
        elif request.summary_type == "key_points":
            user_prompt = f"""Extract the key points from the following document as a bulleted list:

{full_text[:8000]}

Provide 5-10 most important points."""
        
        else:  # comprehensive
            user_prompt = f"""Provide a comprehensive summary of the following document:

{full_text[:8000]}

Include:
- Main topic and purpose
- Key findings or insights
- Important data points
- Conclusions"""
        
        messages = [
            {"role": "system", "content": "You are a financial research assistant that provides clear, concise summaries of documents."},
            {"role": "user", "content": user_prompt}
        ]
        
        summary = llm.generate(messages)
        
        return SummarizeResponse(
            summary=summary,
            document_id=request.document_id,
            metadata={
                'filename': document['filename'],
                'summary_type': request.summary_type,
                'chunk_count': len(chunks_result.data)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )
