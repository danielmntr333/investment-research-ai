"""Agent state definitions for LangGraph."""
from typing import TypedDict, List, Dict, Annotated, Literal, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State passed between agent nodes.
    
    This is the complete context that flows through the graph.
    Each agent reads from and writes to this state.
    """
    
    # User input
    query: str
    chat_history: Annotated[List[Dict], add_messages]
    user_id: Optional[str]
    
    # Document context
    retrieved_docs: List[Dict]  # From RAG retrieval
    document_ids: List[str]  # Available documents
    
    # Agent outputs
    supervisor_analysis: Dict  # Supervisor's query analysis
    research_output: Dict  # Research agent results
    analysis_output: Dict  # Analysis agent results
    fact_check_results: Dict  # Fact checker results
    web_search_results: List[Dict]  # Web search results
    
    # Final output
    final_answer: str
    citations: List[Dict]
    confidence_score: float
    
    # Execution trace (for UI visualization)
    agent_trace: List[Dict]
    
    # Error handling
    errors: List[str]
    retry_count: int
    
    # Metadata
    total_tokens: int
    total_cost: float
    execution_time: float


# Helper for specific agent outputs
class SupervisorDecision(TypedDict):
    """Supervisor's routing decision."""
    strategy: Literal["research", "analysis", "web_search", "multi_agent"]
    reasoning: str
    needs_web_search: bool
    complexity: int  # 1-5
    estimated_steps: int


class ResearchResult(TypedDict):
    """Research agent output."""
    answer: str
    sources: List[Dict]
    confidence: float


class AnalysisResult(TypedDict):
    """Analysis agent output."""
    answer: str
    calculations: List[Dict]
    charts: List[Dict]
    tools_used: List[str]


class FactCheckResult(TypedDict):
    """Fact checker output."""
    verified_claims: List[Dict]
    unverified_claims: List[Dict]
    overall_confidence: float


class WebSearchResult(TypedDict):
    """Web search result."""
    title: str
    url: str
    content: str
    score: float
