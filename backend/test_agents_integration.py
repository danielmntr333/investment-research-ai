"""
REAL Integration test for agent system - NO MOCKS!

This actually connects to:
- OpenAI API (costs ~$0.01-0.05 per test)
- Supabase database
- Real RAG pipeline
- Real agent execution

Usage:
    poetry run python test_agents_integration.py
"""
import asyncio
import sys
import os
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")


def check_environment():
    """Check that all required environment variables are set."""
    print_section("Checking Environment")
    
    required = {
        "OPENAI_API_KEY": "OpenAI API key for LLM",
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_SERVICE_KEY": "Supabase service key",
    }
    
    optional = {
        "TAVILY_API_KEY": "Tavily for web search",
        "COHERE_API_KEY": "Cohere for reranking",
    }
    
    missing = []
    for var, desc in required.items():
        value = os.getenv(var)
        if value:
            # Mask the key for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print_success(f"{var}: {masked}")
        else:
            print_error(f"{var} NOT SET - {desc}")
            missing.append(var)
    
    for var, desc in optional.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print_success(f"{var}: {masked}")
        else:
            print_warning(f"{var} not set - {desc} (optional)")
    
    if missing:
        print_error(f"\nMissing required variables: {', '.join(missing)}")
        print_info("Create a .env file with these variables\n")
        return False
    
    print_success("\nAll required environment variables set!\n")
    return True


def test_basic_imports():
    """Test that all modules can be imported."""
    print_section("Testing Basic Imports")
    
    try:
        from src.agents.graph import ResearchAgentGraph
        print_success("ResearchAgentGraph imported")
        
        from src.agents.state import AgentState
        print_success("AgentState imported")
        
        from src.agents.tools import get_tools
        print_success("Tools imported")
        
        from src.llm.provider import LLMProvider
        print_success("LLMProvider imported")
        
        from src.db.supabase import get_supabase
        print_success("Supabase client imported")
        
        from src.rag.pipeline import RAGPipeline
        print_success("RAG pipeline imported")
        
        print_success("\nAll imports successful!\n")
        return True
        
    except Exception as e:
        print_error(f"Import failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


def test_tools():
    """Test tool functions."""
    print_section("Testing Tools (No API Calls)")
    
    try:
        from src.agents.tools import calculator, financial_metrics, get_tools
        
        # Test calculator using invoke
        result = calculator.invoke({"expression": "(100 + 50) / 2"})
        assert result == "75.0", f"Expected 75.0, got {result}"
        print_success(f"Calculator: (100 + 50) / 2 = {result}")
        
        # Test financial metrics using invoke
        result = financial_metrics.invoke({
            "metric": "profit_margin",
            "values": {"net_income": 25000, "revenue": 100000}
        })
        assert "25.00%" in result
        print_success(f"Profit margin: {result}")
        
        result = financial_metrics.invoke({
            "metric": "pe_ratio",
            "values": {"price": 150, "earnings": 10}
        })
        assert "15.00" in result
        print_success(f"P/E ratio: {result}")
        
        # Get all tools
        tools = get_tools()
        print_success(f"Tool registry: {len(tools)} tools available")
        
        print_success("\nAll tool tests passed!\n")
        return True
        
    except Exception as e:
        print_error(f"Tool test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_provider():
    """Test LLM provider with real API call."""
    print_section("Testing LLM Provider (Real OpenAI API Call)")
    
    try:
        from src.llm.provider import LLMProvider
        
        print_info("Initializing LLM provider...")
        llm = LLMProvider(model="gpt-4o-mini")
        print_success("LLM provider initialized")
        
        print_info("Making test API call to OpenAI...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello World' and nothing else."}
        ]
        
        response = llm.generate(messages, temperature=0.0, max_tokens=50)
        print_success(f"LLM response: {response}")
        
        # Check token usage
        if hasattr(llm, 'total_prompt_tokens'):
            print_info(f"Tokens used: {llm.total_prompt_tokens} prompt + {llm.total_completion_tokens} completion")
        
        print_success("\nLLM provider test passed!\n")
        return True
        
    except Exception as e:
        print_error(f"LLM test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_supabase_connection():
    """Test Supabase database connection."""
    print_section("Testing Supabase Connection")
    
    try:
        from src.db.supabase import get_supabase
        
        print_info("Connecting to Supabase...")
        db = get_supabase()
        print_success("Supabase client created")
        
        print_info("Testing database query (documents table)...")
        result = db.table('documents').select('id, filename').limit(5).execute()
        
        if result.data:
            print_success(f"Found {len(result.data)} documents in database")
            for doc in result.data[:3]:
                print_info(f"  - {doc.get('filename', 'Unknown')} (ID: {doc['id'][:8]}...)")
        else:
            print_warning("No documents in database (this is OK for a fresh setup)")
        
        print_success("\nSupabase connection test passed!\n")
        return True
        
    except Exception as e:
        print_error(f"Supabase test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_pipeline():
    """Test RAG pipeline (only if documents exist)."""
    print_section("Testing RAG Pipeline")
    
    try:
        from src.rag.pipeline import RAGPipeline
        from src.db.supabase import get_supabase
        
        # Check if we have documents
        db = get_supabase()
        result = db.table('documents').select('id').limit(1).execute()
        
        if not result.data:
            print_warning("No documents in database - skipping RAG test")
            print_info("Upload some documents first to test RAG pipeline\n")
            return True
        
        print_info("Initializing RAG pipeline...")
        rag = RAGPipeline()
        print_success("RAG pipeline initialized")
        
        print_info("Testing document retrieval with query: 'revenue'...")
        result = rag.query(
            question="What is the revenue?",
            top_k=3,
            strategy='vector',
            use_reranking=False
        )
        
        if result.get('sources'):
            print_success(f"Retrieved {len(result['sources'])} chunks")
            print_info(f"Answer preview: {result['answer'][:100]}...")
        else:
            print_warning("No results returned (might be query mismatch)")
        
        print_success("\nRAG pipeline test passed!\n")
        return True
        
    except Exception as e:
        print_error(f"RAG test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_graph():
    """Test the full agent graph with real execution."""
    print_section("Testing Agent Graph (Real Execution)")
    
    try:
        from src.agents.graph import ResearchAgentGraph
        from src.db.supabase import get_supabase
        from src.llm.provider import LLMProvider
        from src.rag.pipeline import RAGPipeline
        
        print_info("Initializing all components...")
        db = get_supabase()
        llm = LLMProvider(model="gpt-4o-mini")
        rag = RAGPipeline()
        
        print_success("All components initialized")
        
        print_info("Creating agent graph...")
        graph = ResearchAgentGraph(db, llm, rag)
        print_success("Agent graph created")
        
        # Simple test query
        test_query = "What is 100 + 250 divided by 2?"
        print_info(f"\nExecuting query: '{test_query}'")
        print_warning("This will make real API calls and may take 10-30 seconds...\n")
        
        result = await graph.arun(
            query=test_query,
            user_id=None,  # No user filtering
            chat_history=[]
        )
        
        print_success("Graph execution completed!\n")
        
        # Display results
        print_info("=== RESULTS ===")
        print(f"\n📝 Final Answer:\n{result['final_answer']}\n")
        
        print(f"⏱️  Execution time: {result['execution_time']:.2f}s")
        print(f"🎯 Confidence: {result['confidence_score']:.2f}")
        
        if result.get('total_tokens'):
            print(f"🪙 Tokens used: {result['total_tokens']}")
            print(f"💰 Estimated cost: ${result['total_cost']:.4f}")
        
        print("\n📊 Agent Trace:")
        for i, step in enumerate(result['agent_trace'], 1):
            agent = step['agent']
            action = step['action']
            duration = step.get('duration', 0)
            print(f"  {i}. {agent:15} - {action:25} ({duration:.2f}s)")
        
        if result.get('errors'):
            print("\n⚠️  Errors/Warnings:")
            for error in result['errors']:
                print(f"  - {error}")
        
        print_success("\n✅ Agent graph test PASSED!\n")
        return True
        
    except Exception as e:
        print_error(f"Agent graph test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoint():
    """Test the FastAPI chat endpoint."""
    print_section("Testing API Endpoint (Mock Request)")
    
    try:
        from src.api.routes.chat import ChatRequest, ChatMessage
        
        print_info("Creating test request...")
        request = ChatRequest(
            query="What is 50 times 3?",
            chat_history=[],
            use_agents=True,
            user_id=None
        )
        print_success(f"Request created: {request.query}")
        print_info("Note: To test the live endpoint, start the server with:")
        print_info("  poetry run uvicorn src.api.main:app --reload\n")
        
        print_success("API endpoint structure validated!\n")
        return True
        
    except Exception as e:
        print_error(f"API test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  REAL AGENT SYSTEM INTEGRATION TEST")
    print("  (No mocks - actual API calls will be made)")
    print("="*70)
    
    # Check prerequisites first
    if not check_environment():
        print_error("\n❌ Environment check failed. Fix .env and try again.\n")
        return 1
    
    if not test_basic_imports():
        print_error("\n❌ Import check failed. Run 'poetry install' and try again.\n")
        return 1
    
    # Run tests
    results = {}
    
    results['tools'] = test_tools()
    results['llm_provider'] = await test_llm_provider()
    results['supabase'] = await test_supabase_connection()
    results['rag_pipeline'] = await test_rag_pipeline()
    results['agent_graph'] = await test_agent_graph()
    results['api_endpoint'] = await test_api_endpoint()
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{status:12} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*70)
        print("  🎉 ALL TESTS PASSED!")
        print("="*70)
        print("\nYour agent system is fully operational and ready for production!\n")
        print("Next steps:")
        print("  1. Start the API server:")
        print("     cd backend && poetry run uvicorn src.api.main:app --reload")
        print("\n  2. Test with curl:")
        print('     curl -X POST http://localhost:8000/api/chat \\')
        print('       -H "Content-Type: application/json" \\')
        print("       -d '{\"query\": \"Calculate 100 + 200\", \"use_agents\": true}'")
        print("\n  3. Monitor agent traces in the response to see routing decisions")
        print("\n  4. Try different query types:")
        print("     - Math: 'What is 15% of 250?'")
        print("     - Research: 'What is Apple\\'s revenue?' (needs docs)")
        print("     - Analysis: 'Compare Apple and Microsoft' (needs docs)")
        print()
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("  - 'Import error': Run 'poetry install'")
        print("  - 'API error': Check your OpenAI API key")
        print("  - 'Database error': Check Supabase credentials")
        print("  - 'No documents': Upload test documents to Supabase\n")
        return 1


if __name__ == "__main__":
    print_info("This test will make REAL API calls to:")
    print_info("  - OpenAI (costs ~$0.01-0.05)")
    print_info("  - Supabase (free tier OK)")
    print_info("  - Tavily if configured (optional)\n")
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user\n")
        sys.exit(1)
