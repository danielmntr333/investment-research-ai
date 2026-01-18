"""Chat endpoints with streaming support."""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
import asyncio

from src.agents.graph import ResearchAgentGraph
from src.db.supabase import get_supabase
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/api/chat", tags=["chat"])


# Request/Response models
class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request model."""
    query: str = Field(..., description="User's question")
    chat_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous chat messages")
    document_ids: Optional[List[str]] = Field(default=None, description="Filter by specific documents")
    use_agents: bool = Field(default=True, description="Use multi-agent system (vs simple RAG)")
    user_id: Optional[str] = Field(default=None, description="User ID for personalization")


class AgentTraceStep(BaseModel):
    """Single step in agent execution trace."""
    agent: str
    action: str
    duration: float
    result: Optional[Dict] = None


class SourceDocument(BaseModel):
    """Source document reference."""
    source_number: int = Field(..., description="Source number (e.g., 1, 2, 3)")
    document_name: str = Field(..., description="Name of the source document")
    content_preview: str = Field(..., description="Preview of the relevant content")
    chunk_id: Optional[str] = Field(default=None, description="Chunk identifier")
    similarity: Optional[float] = Field(default=None, description="Similarity score")


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str = Field(..., description="Final answer")
    sources: List[SourceDocument] = Field(default=[], description="Source documents used")
    citations: List[Dict] = Field(default=[], description="Source citations")
    confidence_score: float = Field(..., description="Confidence score 0-1")
    agent_trace: List[AgentTraceStep] = Field(default=[], description="Agent execution trace")
    execution_time: float = Field(..., description="Total execution time in seconds")
    errors: List[str] = Field(default=[], description="Any errors encountered")


# Initialize components (in production, use dependency injection)
_agent_graph = None


def get_agent_graph() -> ResearchAgentGraph:
    """Get or create agent graph instance."""
    global _agent_graph
    
    if _agent_graph is None:
        db = get_supabase()
        llm = LLMProvider()
        rag = RAGPipeline()
        _agent_graph = ResearchAgentGraph(db, llm, rag)
    
    return _agent_graph


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and get response.
    
    This endpoint uses the multi-agent system by default for intelligent query routing.
    """
    print(f"\n[CHAT ENDPOINT] Received request")
    print(f"Query: {request.query}")
    print(f"Use agents: {request.use_agents}")
    print(f"User ID: {request.user_id}")
    print("-" * 60)
    
    try:
        if request.use_agents:
            # Use multi-agent system
            agent_graph = get_agent_graph()
            
            # Convert chat history to required format
            chat_history = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
            
            # Execute agent graph
            result = await agent_graph.arun(
                query=request.query,
                chat_history=chat_history,
                user_id=request.user_id,
                document_ids=request.document_ids
            )
            
            # Format response with sources
            sources = result.get('research_output', {}).get('sources', [])
            source_documents = [
                SourceDocument(
                    source_number=src.get('source_number', idx + 1),
                    document_name=src.get('metadata', {}).get('document_name', 'Unknown Document'),
                    content_preview=src.get('content', '')[:200],
                    chunk_id=src.get('chunk_id'),
                    similarity=src.get('similarity')
                )
                for idx, src in enumerate(sources)
            ]
            
            return ChatResponse(
                answer=result['final_answer'],
                sources=source_documents,
                citations=result['citations'],
                confidence_score=result['confidence_score'],
                agent_trace=[AgentTraceStep(**step) for step in result['agent_trace']],
                execution_time=result['execution_time'],
                errors=result['errors']
            )
        
        else:
            # Simple RAG without agents
            rag = RAGPipeline()
            result = rag.query(
                question=request.query,
                document_ids=request.document_ids,
                strategy='hybrid',
                use_reranking=True
            )
            
            # Format sources for simple RAG
            sources = result.get('sources', [])
            source_documents = [
                SourceDocument(
                    source_number=src.get('source_number', idx + 1),
                    document_name=src.get('metadata', {}).get('document_name', 'Unknown Document'),
                    content_preview=src.get('content', '')[:200],
                    chunk_id=src.get('chunk_id'),
                    similarity=src.get('similarity')
                )
                for idx, src in enumerate(sources)
            ]
            
            return ChatResponse(
                answer=result['answer'],
                sources=source_documents,
                citations=result.get('sources', []),
                confidence_score=0.8,
                agent_trace=[],
                execution_time=result.get('metadata', {}).get('retrieval_time', 0),
                errors=[]
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a chat message with Server-Sent Events (SSE) streaming.
    
    Streams real-time updates:
    - Pipeline progress (retrieval, reranking, etc.)
    - Token-by-token answer generation
    - Agent execution steps
    """
    print(f"\n[CHAT STREAM ENDPOINT] Received request")
    print(f"Query: {request.query}")
    print(f"Use agents: {request.use_agents}")
    print(f"User ID: {request.user_id}")
    print("-" * 60)
    
    async def generate():
        """Generate SSE events for streaming."""
        try:
            print(f"[STREAM] Starting generation, use_agents={request.use_agents}")
            
            if request.use_agents:
                print("[STREAM] Using agent system with real-time streaming")
                agent_graph = get_agent_graph()
                
                # Convert chat history
                chat_history = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
                
                # Stream agent execution in real-time
                final_state = None
                async for event in agent_graph.arun_stream(
                    query=request.query,
                    chat_history=chat_history,
                    user_id=request.user_id,
                    document_ids=request.document_ids
                ):
                    if event['type'] == 'agent_start':
                        # Agent starting
                        yield f"data: {json.dumps({'type': 'agent_step', 'data': {'agent': event['agent'], 'action': event['action'], 'status': 'start'}})}\n\n"
                        await asyncio.sleep(0.05)  # Small delay for UI
                        
                    elif event['type'] == 'agent_complete':
                        # Agent completed
                        yield f"data: {json.dumps({'type': 'agent_step', 'data': {'agent': event['agent'], 'action': event['action'], 'status': 'complete', 'duration': event['duration']}})}\n\n"
                        await asyncio.sleep(0.05)
                        
                    elif event['type'] == 'done':
                        final_state = event['final_state']
                        
                    elif event['type'] == 'error':
                        yield f"data: {json.dumps({'type': 'error', 'data': {'message': event['message']}})}\n\n"
                        return
                
                # Stream final answer if we got final state
                if final_state:
                    # Format sources
                    sources = final_state.get('research_output', {}).get('sources', [])
                    source_list = [
                        {
                            'source_number': src.get('source_number', idx + 1),
                            'document_name': src.get('metadata', {}).get('document_name', 'Unknown Document'),
                            'content_preview': src.get('content', '')[:200],
                            'chunk_id': src.get('chunk_id'),
                            'similarity': src.get('similarity')
                        }
                        for idx, src in enumerate(sources)
                    ]
                    
                    # Stream final answer
                    final_event = {
                        'type': 'final_answer',
                        'data': {
                            'answer': final_state['final_answer'],
                            'sources': source_list,
                            'citations': final_state['citations'],
                            'confidence_score': final_state['confidence_score'],
                            'execution_time': final_state['execution_time'],
                            'errors': final_state['errors']
                        }
                    }
                    yield f"data: {json.dumps(final_event)}\n\n"
                
            else:
                # Simple RAG with streaming
                print("[STREAM] Using RAG pipeline with streaming")
                rag = RAGPipeline()
                
                async for event in rag.query_stream(
                    question=request.query,
                    document_ids=request.document_ids,
                    strategy='hybrid',
                    use_reranking=True
                ):
                    # Forward all events from RAG pipeline
                    if event['type'] == 'step':
                        # Pipeline progress event
                        step_event = {
                            'type': 'pipeline_step',
                            'data': {
                                'step': event['step'],
                                'status': event['status'],
                                'message': event.get('message', ''),
                                'data': event.get('data', {})
                            }
                        }
                        yield f"data: {json.dumps(step_event)}\n\n"
                        
                    elif event['type'] == 'token':
                        # Token streaming
                        token_event = {
                            'type': 'content',
                            'content': event['content']
                        }
                        yield f"data: {json.dumps(token_event)}\n\n"
                        
                    elif event['type'] == 'sources':
                        # Sources found
                        sources_event = {
                            'type': 'sources_found',
                            'data': {
                                'sources': event['sources']
                            }
                        }
                        yield f"data: {json.dumps(sources_event)}\n\n"
                        
                    elif event['type'] == 'done':
                        # Final answer with metadata
                        final_event = {
                            'type': 'final_answer',
                            'data': {
                                'answer': event['answer'],
                                'sources': event['sources'],
                                'citations': event['sources'],
                                'confidence_score': 0.85,
                                'execution_time': event['metadata']['processing_time'],
                                'metadata': event['metadata']
                            }
                        }
                        yield f"data: {json.dumps(final_event)}\n\n"
                        
                    elif event['type'] == 'error':
                        # Error event
                        error_event = {
                            'type': 'error',
                            'data': {'message': event['message']}
                        }
                        yield f"data: {json.dumps(error_event)}\n\n"
                        return
            
            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        except Exception as e:
            print(f"[STREAM] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            error_event = {
                'type': 'error',
                'data': {'message': str(e)}
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations():
    """List all conversations for the current user."""
    # To be implemented with proper user auth
    return []


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """Get conversation history."""
    # To be implemented with proper storage
    return {"conversation": {}}
