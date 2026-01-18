"""
Test supervisor routing decisions for different query types.

This helps verify that the supervisor correctly routes queries to
the appropriate agent strategy.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.nodes import supervisor_node
from src.agents.state import AgentState
from src.db.supabase import get_supabase
from src.llm.provider import LLMProvider


def print_result(query, strategy, reasoning):
    """Print routing result."""
    strategy_color = {
        'research': '📚',
        'analysis': '📊',
        'web_search': '🌐',
        'multi_agent': '🤖'
    }
    icon = strategy_color.get(strategy, '❓')
    print(f"\n{icon} Query: {query}")
    print(f"   Strategy: {strategy.upper()}")
    print(f"   Reasoning: {reasoning}")


async def test_routing():
    """Test routing for various query types."""
    print("=" * 70)
    print("Testing Supervisor Routing Logic")
    print("=" * 70)
    
    # Initialize components
    db = get_supabase()
    llm = LLMProvider()
    
    # Test queries
    test_cases = [
        # Document-based queries (should route to RESEARCH)
        ("Who is the trustee of the notes in the Apple 10-K?", "research"),
        ("What was Apple's revenue in 2024?", "research"),
        ("What are the key risk factors mentioned in the document?", "research"),
        
        # Real-time queries (should route to WEB_SEARCH)
        ("What is the current stock price of Apple?", "web_search"),
        ("What is Apple's stock price today?", "web_search"),
        ("Latest news about Apple stock", "web_search"),
        
        # Analysis queries (should route to ANALYSIS)
        ("Compare Apple and Microsoft's revenue growth", "analysis"),
        ("Calculate the year-over-year revenue increase", "analysis"),
        
        # General queries when no docs (might route to WEB_SEARCH)
        ("Who is the CEO of Apple?", "research"),  # Could be in docs or web
    ]
    
    correct = 0
    total = len(test_cases)
    
    for query, expected_strategy in test_cases:
        # Create state
        state: AgentState = {
            'query': query,
            'chat_history': [],
            'user_id': 'test_user',  # Simulating user with documents
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
        result_state = await supervisor_node(state, llm, db)
        decision = result_state.get('supervisor_analysis', {})
        
        actual_strategy = decision.get('strategy', 'unknown')
        reasoning = decision.get('reasoning', 'N/A')
        
        print_result(query, actual_strategy, reasoning)
        
        # Check if correct
        if actual_strategy == expected_strategy:
            print("   ✅ Correct routing")
            correct += 1
        else:
            print(f"   ❌ Expected: {expected_strategy.upper()}")
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"Routing Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")
    print("=" * 70)
    
    if correct < total:
        print("\n💡 Tips to improve routing:")
        print("- Adjust SUPERVISOR_PROMPT in src/agents/prompts.py")
        print("- Add more explicit keywords for each strategy")
        print("- Use a more capable LLM model for routing (e.g., GPT-4)")


if __name__ == "__main__":
    asyncio.run(test_routing())
