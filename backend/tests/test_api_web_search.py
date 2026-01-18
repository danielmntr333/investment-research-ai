"""
Test web search through the actual API endpoint.

This verifies that the web search works when called through the FastAPI backend,
not just in the isolated test script.
"""
import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/chat"

def test_stock_price_query():
    """Test stock price query through API."""
    print("=" * 70)
    print("Testing Web Search Through API")
    print("=" * 70)
    print()
    
    # Query that should trigger web search
    query = "What is the current stock price of Google?"
    
    payload = {
        "query": query,
        "chat_history": [],
        "use_agents": True,  # Make sure agents are enabled
        "user_id": None,
        "document_ids": []
    }
    
    print(f"Sending query: {query}")
    print(f"To: {API_URL}")
    print()
    
    try:
        # Send request
        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"[ERROR] API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        # Parse response
        result = response.json()
        
        # Print agent trace
        print("Agent Execution Trace:")
        print("-" * 70)
        for i, step in enumerate(result.get('agent_trace', []), 1):
            agent = step.get('agent', 'unknown')
            action = step.get('action', 'unknown')
            duration = step.get('duration', 0)
            print(f"{i}. {agent.upper()}: {action} ({duration:.2f}s)")
        
        # Check if web search was executed
        agent_names = [step.get('agent') for step in result.get('agent_trace', [])]
        web_search_executed = 'web_search' in agent_names
        
        print()
        if web_search_executed:
            print("[OK] Web search agent was executed!")
        else:
            print("[ERROR] Web search agent was NOT executed!")
            print("Agents that ran:", ', '.join(agent_names))
        
        # Print errors if any
        if result.get('errors'):
            print()
            print("Errors:")
            print("-" * 70)
            for error in result['errors']:
                print(f"  - {error}")
        
        # Print final answer
        print()
        print("Final Answer:")
        print("-" * 70)
        print(result.get('answer', 'No answer'))
        
        print()
        print("=" * 70)
        print(f"Execution time: {result.get('execution_time', 0):.2f}s")
        print(f"Confidence: {result.get('confidence_score', 0):.2f}")
        print("=" * 70)
        
        # Verify result
        if web_search_executed and "stock price" in result.get('answer', '').lower():
            print()
            print("[SUCCESS] Web search is working through the API!")
        else:
            print()
            print("[FAILED] Web search is not working properly through the API")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to backend server at", API_URL)
        print()
        print("Make sure the backend is running:")
        print("  cd backend")
        print("  poetry run uvicorn src.api.main:app --reload --port 8000")
        
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out after 60 seconds")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_stock_price_query()
