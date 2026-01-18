"""
Test web search agent routing for stock price queries.

This script tests whether the supervisor correctly routes stock price
queries to the web_search agent.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.graph import ResearchAgentGraph
from src.db.supabase import get_supabase
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_tavily():
    """Check if Tavily API key is set."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        print(f"[OK] TAVILY_API_KEY is set: {tavily_key[:8]}...")
        return True
    else:
        print("[ERROR] TAVILY_API_KEY is NOT set")
        print("\nTo enable web search:")
        print("1. Get API key from https://tavily.com/")
        print("2. Add to backend/.env: TAVILY_API_KEY=your_key_here")
        return False


async def test_stock_price_query():
    """Test a stock price query to see routing behavior."""
    print_section("Testing Stock Price Query Routing")
    
    query = "What is the current stock price of Google?"
    print(f"Query: {query}\n")
    
    try:
        # Initialize components
        db = get_supabase()
        llm = LLMProvider()
        rag = RAGPipeline()
        agent_graph = ResearchAgentGraph(db, llm, rag)
        
        # Execute query
        print("Executing agent graph...\n")
        result = await agent_graph.arun(
            query=query,
            user_id=None,  # No user context
            document_ids=[]
        )
        
        # Print results
        print_section("Supervisor Decision")
        supervisor_analysis = result.get('supervisor_analysis', {})
        print(f"Strategy chosen: {supervisor_analysis.get('strategy', 'UNKNOWN')}")
        print(f"Reasoning: {supervisor_analysis.get('reasoning', 'N/A')}")
        print(f"Needs web search: {supervisor_analysis.get('needs_web_search', False)}")
        print(f"Complexity: {supervisor_analysis.get('complexity', 'N/A')}")
        
        # Print agent trace
        print_section("Agent Execution Trace")
        for i, step in enumerate(result.get('agent_trace', []), 1):
            agent = step.get('agent', 'unknown')
            action = step.get('action', 'unknown')
            duration = step.get('duration', 0)
            print(f"{i}. {agent.upper()}: {action} ({duration:.2f}s)")
        
        # Print web search results
        print_section("Web Search Results")
        web_results = result.get('web_search_results', [])
        if web_results:
            print(f"Found {len(web_results)} results:\n")
            for i, res in enumerate(web_results[:3], 1):
                print(f"{i}. {res.get('title', 'No title')}")
                print(f"   URL: {res.get('url', 'N/A')}")
                print(f"   Score: {res.get('score', 0):.3f}")
                print()
        else:
            print("[ERROR] No web search results found!")
            print("\nPossible reasons:")
            print("- Supervisor didn't route to web_search strategy")
            print("- TAVILY_API_KEY not set")
            print("- Web search node encountered an error")
        
        # Print errors
        if result.get('errors'):
            print_section("Errors")
            for error in result['errors']:
                print(f"[WARNING] {error}")
        
        # Print final answer
        print_section("Final Answer")
        print(result.get('final_answer', 'No answer generated'))
        
        # Print summary
        print_section("Summary")
        print(f"Execution time: {result.get('execution_time', 0):.2f}s")
        print(f"Confidence score: {result.get('confidence_score', 0):.2f}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_supervisor_directly():
    """Test supervisor node directly to see routing decision."""
    print_section("Testing Supervisor Node Directly")
    
    from src.agents.nodes import supervisor_node
    from src.agents.state import AgentState
    
    query = "What is the current stock price of Google?"
    print(f"Query: {query}\n")
    
    try:
        db = get_supabase()
        llm = LLMProvider()
        
        # Create initial state
        state: AgentState = {
            'query': query,
            'chat_history': [],
            'user_id': None,
            'retrieved_docs': [],
            'document_ids': [],
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
        
        # Call supervisor
        print("Calling supervisor node...\n")
        result_state = await supervisor_node(state, llm, db)
        
        # Print decision
        decision = result_state.get('supervisor_analysis', {})
        print(f"Strategy: {decision.get('strategy', 'UNKNOWN')}")
        print(f"Reasoning: {decision.get('reasoning', 'N/A')}")
        print(f"Needs web search: {decision.get('needs_web_search', False)}")
        
        if decision.get('strategy') != 'web_search':
            print("\n[ERROR] PROBLEM: Supervisor chose '{}' instead of 'web_search'".format(decision.get('strategy')))
            print("\nThis is why web search isn't being triggered!")
            print("\nSolutions:")
            print("1. Improve supervisor prompt to better detect stock price queries")
            print("2. Add explicit keywords for web search routing")
            print("3. Use a more powerful LLM model for routing")
        else:
            print("\n[OK] Supervisor correctly chose 'web_search' strategy")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print_section("Web Search Agent Diagnostics")
    print("This script tests whether stock price queries trigger web search.\n")
    
    # Check environment
    has_tavily = check_tavily()
    
    # Test supervisor routing
    await test_supervisor_directly()
    
    # Test full agent graph
    if has_tavily:
        await test_stock_price_query()
    else:
        print("\n[WARNING] Skipping full test - TAVILY_API_KEY not set")
        print("The supervisor routing test above shows the routing behavior.")


if __name__ == "__main__":
    asyncio.run(main())
