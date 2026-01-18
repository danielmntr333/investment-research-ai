"""Agent node implementations."""
from typing import Dict, List
import json
import time
import re
import os

from .state import AgentState, SupervisorDecision, ResearchResult, AnalysisResult
from .prompts import (
    SUPERVISOR_PROMPT,
    RESEARCH_AGENT_PROMPT,
    ANALYSIS_AGENT_PROMPT,
    FACT_CHECKER_PROMPT,
    WEB_SEARCH_AGENT_PROMPT,
    SYNTHESIZER_PROMPT
)
from src.utils.config import settings


async def supervisor_node(
    state: AgentState, 
    llm, 
    db
) -> AgentState:
    """
    Supervisor agent: Analyzes query and determines routing strategy.
    
    Args:
        state: Current agent state
        llm: LLM provider instance
        db: Database client
    
    Returns:
        Updated state with supervisor_analysis
    """
    start_time = time.time()
    
    try:
        # Get list of available documents
        user_id = state.get('user_id')
        docs = []
        
        # For demo purposes, get all documents (not filtering by user_id)
        # In production, you'd filter by user_id or implement proper auth
        try:
            result = db.table('documents').select('filename, file_type').execute()
            docs = result.data if result.data else []
        except Exception as e:
            print(f"[SUPERVISOR] Error fetching documents: {e}")
            docs = []
        
        doc_list = [f"- {d['filename']} ({d.get('file_type', 'unknown')})" for d in docs]
        
        # LOGGING: Show what documents the supervisor sees
        print(f"\n[SUPERVISOR ROUTING DEBUG]")
        print(f"Query: {state['query']}")
        print(f"User ID: {user_id}")
        print(f"Documents found: {len(docs)}")
        if docs:
            print("Document list:")
            for doc in docs:
                print(f"  - {doc.get('filename')} ({doc.get('document_type', 'unknown')})")
        else:
            print("  (No documents available)")
        print("-" * 60)
        
        # Format prompt
        prompt = SUPERVISOR_PROMPT.format(
            query=state['query'],
            document_list="\n".join(doc_list) if doc_list else "No documents uploaded"
        )
        
        # Call LLM for structured output
        messages = [
            {"role": "system", "content": "You are a routing supervisor. Respond ONLY with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = llm.generate(messages, temperature=0.0, max_tokens=500)
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle cases where LLM adds markdown)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            decision = json.loads(response)
        except json.JSONDecodeError:
            # Fallback to research strategy
            decision = {
                "strategy": "research",
                "reasoning": "Failed to parse supervisor response, defaulting to research",
                "needs_web_search": False,
                "complexity": 2,
                "estimated_steps": 2
            }
        
        # Update state
        state['supervisor_analysis'] = decision
        
        # LOGGING: Show routing decision
        print(f"[SUPERVISOR DECISION]")
        print(f"Strategy: {decision.get('strategy', 'UNKNOWN')}")
        print(f"Reasoning: {decision.get('reasoning', 'N/A')}")
        print(f"Needs web search: {decision.get('needs_web_search', False)}")
        print("=" * 60 + "\n")
        
        state['agent_trace'].append({
            'agent': 'supervisor',
            'action': 'query_analysis',
            'result': decision,
            'timestamp': time.time(),
            'duration': time.time() - start_time
        })
        
    except Exception as e:
        state['errors'].append(f"Supervisor error: {str(e)}")
        # Default to research
        state['supervisor_analysis'] = {
            "strategy": "research",
            "reasoning": f"Error in supervisor: {str(e)}",
            "needs_web_search": False,
            "complexity": 2,
            "estimated_steps": 2
        }
    
    return state


async def research_node(
    state: AgentState,
    rag_pipeline,
    llm
) -> AgentState:
    """
    Research agent: RAG-based question answering.
    
    Args:
        state: Current agent state
        rag_pipeline: RAG pipeline instance
        llm: LLM provider instance
    
    Returns:
        Updated state with research_output
    """
    start_time = time.time()
    query = state['query']
    
    try:
        # Use RAG pipeline to retrieve and generate answer
        result = rag_pipeline.query(
            question=query,
            document_ids=state.get('document_ids', None),
            top_k=10,
            strategy='hybrid',
            use_reranking=True
        )
        
        # Extract data from result
        retrieved = result.get('sources', [])
        answer = result.get('answer', '')
        
        state['retrieved_docs'] = retrieved
        
        # Extract citations
        citations = _extract_citations(answer, retrieved)
        
        # Calculate confidence
        confidence = _calculate_confidence(answer, retrieved)
        
        # Update state
        state['research_output'] = {
            'answer': answer,
            'sources': retrieved,
            'confidence': confidence
        }
        state['citations'].extend(citations)
        state['agent_trace'].append({
            'agent': 'research',
            'action': 'rag_query',
            'docs_retrieved': len(retrieved),
            'citations_found': len(citations),
            'duration': time.time() - start_time
        })
        
    except Exception as e:
        state['errors'].append(f"Research error: {str(e)}")
        state['research_output'] = {
            'answer': f"Error during research: {str(e)}",
            'sources': [],
            'confidence': 0.0
        }
    
    return state


async def analysis_node(
    state: AgentState,
    llm,
    tools: List
) -> AgentState:
    """
    Analysis agent: Comparative analysis with tool usage.
    
    Args:
        state: Current agent state
        llm: LLM provider instance
        tools: List of available tools
    
    Returns:
        Updated state with analysis_output
    """
    start_time = time.time()
    query = state['query']
    context = state.get('retrieved_docs', [])
    
    try:
        # Format context
        context_str = "\n\n".join([
            f"Document {i}: {doc.get('content', '')[:500]}..."
            for i, doc in enumerate(context)
        ])
        
        # Analysis prompt
        prompt = ANALYSIS_AGENT_PROMPT.format(
            query=query,
            context=context_str if context_str else "No documents provided"
        )
        
        # For now, simple LLM call (can be enhanced with LangChain agent later)
        messages = [
            {"role": "system", "content": "You are an analysis agent with access to calculation and visualization tools."},
            {"role": "user", "content": prompt}
        ]
        
        answer = llm.generate(messages, temperature=0.2, max_tokens=2000)
        
        # Update state
        state['analysis_output'] = {
            'answer': answer,
            'calculations': [],  # Would extract from tool calls
            'charts': [],  # Would extract chart data
            'tools_used': []
        }
        state['agent_trace'].append({
            'agent': 'analysis',
            'action': 'comparative_analysis',
            'tools_used': state['analysis_output']['tools_used'],
            'duration': time.time() - start_time
        })
        
    except Exception as e:
        state['errors'].append(f"Analysis error: {str(e)}")
        state['analysis_output'] = {
            'answer': f"Error during analysis: {str(e)}",
            'calculations': [],
            'charts': [],
            'tools_used': []
        }
    
    return state


async def fact_checker_node(
    state: AgentState,
    llm
) -> AgentState:
    """
    Fact checker: Validates claims against sources.
    
    Args:
        state: Current agent state
        llm: LLM provider instance
    
    Returns:
        Updated state with fact_check_results
    """
    start_time = time.time()
    
    try:
        # Get answer to fact-check
        answer = state.get('research_output', {}).get('answer', '')
        if not answer:
            answer = state.get('analysis_output', {}).get('answer', '')
        
        sources = state.get('retrieved_docs', [])
        
        if not answer or not sources:
            # Nothing to fact-check
            state['fact_check_results'] = {
                'verified_claims': [],
                'unverified_claims': [],
                'overall_confidence': 0.8
            }
            return state
        
        # Format sources
        sources_str = "\n\n".join([
            f"Source {i}:\n{doc.get('content', '')[:300]}..."
            for i, doc in enumerate(sources[:5])  # Limit to top 5 sources
        ])
        
        # Fact-check prompt
        prompt = FACT_CHECKER_PROMPT.format(
            answer=answer,
            sources=sources_str
        )
        
        messages = [
            {"role": "system", "content": "You are a fact-checker. Respond ONLY with valid JSON array."},
            {"role": "user", "content": prompt}
        ]
        
        response = llm.generate(messages, temperature=0.0, max_tokens=1000)
        
        # Parse JSON response
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                response = json_match.group()
            result = json.loads(response)
        except json.JSONDecodeError:
            # If parsing fails, assume medium confidence
            result = []
        
        # Separate verified and unverified
        verified = [c for c in result if c.get('supported', False)]
        unverified = [c for c in result if not c.get('supported', False)]
        
        # Calculate overall confidence
        if result:
            overall_confidence = sum(c.get('confidence', 0.5) for c in verified) / len(result)
        else:
            overall_confidence = 0.7  # Default if no claims extracted
        
        # Update state
        state['fact_check_results'] = {
            'verified_claims': verified,
            'unverified_claims': unverified,
            'overall_confidence': overall_confidence
        }
        
        # Add warnings for unverified claims
        if unverified:
            state['errors'].append(
                f"Warning: {len(unverified)} claims could not be verified"
            )
        
        state['agent_trace'].append({
            'agent': 'fact_checker',
            'action': 'claim_verification',
            'claims_checked': len(result),
            'verified': len(verified),
            'unverified': len(unverified),
            'confidence': overall_confidence,
            'duration': time.time() - start_time
        })
        
    except Exception as e:
        state['errors'].append(f"Fact checker error: {str(e)}")
        state['fact_check_results'] = {
            'verified_claims': [],
            'unverified_claims': [],
            'overall_confidence': 0.5
        }
    
    return state


async def web_search_node(
    state: AgentState,
    llm
) -> AgentState:
    """
    Web search agent: Fetches real-time external data.
    
    Args:
        state: Current agent state
        llm: LLM provider instance
    
    Returns:
        Updated state with web_search_results
    """
    start_time = time.time()
    query = state['query']
    
    try:
        # Use Tavily for web search
        from tavily import TavilyClient
        
        tavily_api_key = settings.tavily_api_key
        if not tavily_api_key:
            state['errors'].append("Warning: TAVILY_API_KEY not set, skipping web search")
            state['web_search_results'] = []
            return state
        
        tavily = TavilyClient(api_key=tavily_api_key)
        
        # Search (use synchronous method for now)
        results = tavily.search(
            query=query,
            max_results=5,
            search_depth="basic"
        )
        
        # Format results
        search_results = [
            {
                'title': r.get('title', ''),
                'url': r.get('url', ''),
                'content': r.get('content', ''),
                'score': r.get('score', 0.0)
            }
            for r in results.get('results', [])
        ]
        
        # Update state
        state['web_search_results'] = search_results
        state['agent_trace'].append({
            'agent': 'web_search',
            'action': 'external_search',
            'results_found': len(search_results),
            'duration': time.time() - start_time
        })
        
    except Exception as e:
        state['errors'].append(f"Web search error: {str(e)}")
        state['web_search_results'] = []
    
    return state


async def synthesizer_node(
    state: AgentState,
    llm
) -> AgentState:
    """
    Synthesizer: Combines all agent outputs into final answer.
    
    Args:
        state: Current agent state
        llm: LLM provider instance
    
    Returns:
        Updated state with final_answer
    """
    start_time = time.time()
    
    try:
        # Collect all outputs
        agent_outputs = {
            'research': state.get('research_output', {}),
            'analysis': state.get('analysis_output', {}),
            'fact_check': state.get('fact_check_results', {}),
            'web_search': state.get('web_search_results', [])
        }
        
        # Format for prompt
        outputs_str = json.dumps(agent_outputs, indent=2)
        
        # Format source documents for citation
        sources = state.get('research_output', {}).get('sources', [])
        sources_str = _format_sources_for_synthesis(sources)
        
        # Synthesis prompt
        prompt = SYNTHESIZER_PROMPT.format(
            query=state['query'],
            agent_outputs=outputs_str,
            sources=sources_str
        )
        
        messages = [
            {"role": "system", "content": "You are a synthesizer that combines multiple sources into a coherent answer with specific document citations."},
            {"role": "user", "content": prompt}
        ]
        
        # Generate final answer
        final_answer = llm.generate(messages, temperature=0.1, max_tokens=2000)
        
        # Update state
        state['final_answer'] = final_answer
        state['confidence_score'] = state.get('fact_check_results', {}).get('overall_confidence', 0.8)
        state['agent_trace'].append({
            'agent': 'synthesizer',
            'action': 'final_synthesis',
            'duration': time.time() - start_time
        })
        
    except Exception as e:
        state['errors'].append(f"Synthesizer error: {str(e)}")
        # Fallback to research output
        state['final_answer'] = state.get('research_output', {}).get('answer', f"Error: {str(e)}")
        state['confidence_score'] = 0.5
    
    return state


# Helper functions
def _extract_citations(answer: str, documents: List[Dict]) -> List[Dict]:
    """Extract citation markers from answer and link to documents."""
    citations = []
    pattern = r'\[doc_(\d+):chunk_([a-f0-9-]+)\]'
    
    for match in re.finditer(pattern, answer):
        doc_idx = int(match.group(1))
        chunk_id = match.group(2)
        
        if doc_idx < len(documents):
            citations.append({
                'doc_id': documents[doc_idx].get('document_id', ''),
                'chunk_id': chunk_id,
                'content': documents[doc_idx].get('content', '')[:200] + '...'
            })
    
    return citations


def _calculate_confidence(answer: str, sources: List[Dict]) -> float:
    """Calculate confidence score based on citations and source quality."""
    
    # Count citations
    citation_count = len(re.findall(r'\[doc_\d+:chunk_[a-f0-9-]+\]', answer))
    
    # Baseline confidence
    if citation_count == 0:
        return 0.3
    elif citation_count < 3:
        return 0.6
    else:
        return 0.9


def _format_sources_for_synthesis(sources: List[Dict]) -> str:
    """
    Format sources with document names for the synthesizer to reference.
    
    Args:
        sources: List of source dictionaries with metadata
        
    Returns:
        Formatted string with source numbers and document names
    """
    if not sources:
        return "No sources available"
    
    formatted = []
    for source in sources:
        source_num = source.get('source_number', 'Unknown')
        doc_name = source.get('metadata', {}).get('document_name', 'Unknown Document')
        content_preview = source.get('content', '')[:150]
        
        formatted.append(
            f"Source {source_num}: {doc_name}\n"
            f"Preview: {content_preview}..."
        )
    
    return "\n\n".join(formatted)
