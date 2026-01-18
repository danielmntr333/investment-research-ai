"""LangGraph orchestrator for multi-agent system."""
from langgraph.graph import StateGraph, END
from typing import Literal, Dict, List, Optional
import time

from .state import AgentState
from .nodes import (
    supervisor_node,
    research_node,
    analysis_node,
    fact_checker_node,
    web_search_node,
    synthesizer_node
)
from .tools import get_tools


class ResearchAgentGraph:
    """
    Multi-agent orchestration system using LangGraph.
    
    Flow:
        User Query → Supervisor (routing) → Agent(s) → Fact Checker → Synthesizer → Final Answer
    
    The supervisor determines which agent(s) to call based on the query:
    - RESEARCH: Factual questions from documents (RAG)
    - ANALYSIS: Comparative analysis, calculations
    - WEB_SEARCH: Real-time data not in documents
    - MULTI_AGENT: Complex queries requiring multiple agents
    
    Example:
        graph = ResearchAgentGraph(supabase_client, llm_provider, rag_pipeline)
        result = await graph.arun("Compare Apple and Microsoft's revenue")
    """
    
    def __init__(self, supabase_client, llm_provider, rag_pipeline):
        """
        Initialize the agent graph.
        
        Args:
            supabase_client: Supabase client for database access
            llm_provider: LLM provider for text generation
            rag_pipeline: RAG pipeline for document retrieval
        """
        self.db = supabase_client
        self.llm = llm_provider
        self.rag = rag_pipeline
        
        # Build the graph
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()
    
    def _build_graph(self) -> StateGraph:
        """Construct the agent execution graph."""
        
        # Initialize graph with state schema
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("supervisor", self._supervisor_wrapper)
        workflow.add_node("research", self._research_wrapper)
        workflow.add_node("analysis", self._analysis_wrapper)
        workflow.add_node("fact_checker", self._fact_checker_wrapper)
        workflow.add_node("web_search", self._web_search_wrapper)
        workflow.add_node("synthesizer", self._synthesizer_wrapper)
        
        # Define entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional routing from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_query,
            {
                "research": "research",
                "analysis": "analysis",
                "web_search": "web_search",
                "multi_agent": "research",  # Start multi-agent flow with research
            }
        )
        
        # Define edges between nodes
        workflow.add_edge("research", "fact_checker")
        workflow.add_edge("analysis", "fact_checker")
        
        # Web search can either go to research or fact checker
        workflow.add_edge("web_search", "research")
        
        # Fact checker always goes to synthesizer
        workflow.add_edge("fact_checker", "synthesizer")
        
        # Synthesizer is the end
        workflow.add_edge("synthesizer", END)
        
        return workflow
    
    def _route_query(self, state: AgentState) -> Literal["research", "analysis", "web_search", "multi_agent"]:
        """
        Routing logic based on supervisor's decision.
        
        Returns the next node to execute.
        """
        decision = state.get("supervisor_analysis", {})
        strategy = decision.get("strategy", "research")
        
        # Ensure valid strategy
        if strategy not in ["research", "analysis", "web_search", "multi_agent"]:
            strategy = "research"
        
        return strategy
    
    # Node wrappers that inject dependencies
    async def _supervisor_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for supervisor node."""
        return await supervisor_node(state, self.llm, self.db)
    
    async def _research_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for research node."""
        return await research_node(state, self.rag, self.llm)
    
    async def _analysis_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for analysis node."""
        tools = get_tools()
        return await analysis_node(state, self.llm, tools)
    
    async def _fact_checker_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for fact checker node."""
        return await fact_checker_node(state, self.llm)
    
    async def _web_search_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for web search node."""
        return await web_search_node(state, self.llm)
    
    async def _synthesizer_wrapper(self, state: AgentState) -> AgentState:
        """Wrapper for synthesizer node."""
        return await synthesizer_node(state, self.llm)
    
    async def arun(
        self, 
        query: str, 
        chat_history: Optional[List[Dict]] = None,
        user_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Execute the agent graph asynchronously.
        
        Args:
            query: User's question
            chat_history: Previous conversation messages
            user_id: User ID for document access
            document_ids: Optional list of specific document IDs to search
        
        Returns:
            Final state with answer and metadata
        """
        print(f"\n[AGENT GRAPH] Starting arun()")
        print(f"  - query: {query}")
        print(f"  - user_id: {user_id}")
        print(f"  - document_ids: {document_ids}")
        
        start_time = time.time()
        
        # Initialize state
        print("[AGENT GRAPH] Initializing state...")
        initial_state: AgentState = {
            'query': query,
            'chat_history': chat_history or [],
            'user_id': user_id,
            'retrieved_docs': [],
            'document_ids': document_ids or [],
            'supervisor_analysis': {},
            'research_output': {},
            'analysis_output': {},
            'fact_check_results': {},
            'web_search_results': [],
            'final_answer': "",
            'citations': [],
            'confidence_score': 0.0,
            'agent_trace': [],
            'errors': [],
            'retry_count': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'execution_time': 0.0
        }
        
        # Execute graph
        try:
            print("[AGENT GRAPH] Calling app.ainvoke()...")
            final_state = await self.app.ainvoke(initial_state)
            print(f"[AGENT GRAPH] app.ainvoke() completed")
            
            # Calculate execution time
            final_state['execution_time'] = time.time() - start_time
            
            print(f"[AGENT GRAPH] Execution complete")
            print(f"  - execution_time: {final_state['execution_time']:.2f}s")
            print(f"  - agent_trace length: {len(final_state.get('agent_trace', []))}")
            print(f"  - errors: {final_state.get('errors', [])}")
            
            # Calculate tokens and cost (if LLM provider tracks it)
            if hasattr(self.llm, 'total_prompt_tokens'):
                final_state['total_tokens'] = (
                    self.llm.total_prompt_tokens + 
                    self.llm.total_completion_tokens
                )
                # Simple cost estimation (adjust rates as needed)
                # GPT-4o-mini: ~$0.15 per 1M input, ~$0.60 per 1M output
                final_state['total_cost'] = (
                    (self.llm.total_prompt_tokens / 1_000_000 * 0.15) +
                    (self.llm.total_completion_tokens / 1_000_000 * 0.60)
                )
            
            return final_state
            
        except Exception as e:
            # Handle execution errors
            print(f"[AGENT GRAPH] ERROR during execution: {e}")
            import traceback
            traceback.print_exc()
            
            initial_state['errors'].append(f"Graph execution error: {str(e)}")
            initial_state['final_answer'] = f"An error occurred during processing: {str(e)}"
            initial_state['execution_time'] = time.time() - start_time
            return initial_state
    
    def visualize(self, output_path: str = "agent_graph.png"):
        """
        Generate a visualization of the agent graph.
        Useful for documentation and debugging.
        
        Args:
            output_path: Path to save the graph visualization
        """
        try:
            from IPython.display import Image, display
            
            # Get mermaid PNG
            png_data = self.app.get_graph().draw_mermaid_png()
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(png_data)
            
            print(f"Graph visualization saved to {output_path}")
            
        except Exception as e:
            print(f"Could not generate visualization: {str(e)}")
            print("Install graphviz and pygraphviz for visualization support")
