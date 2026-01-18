# Agent System Integration Test - REAL VERSION

This test file **actually connects to all services** and runs real queries through the system.

⚠️ **This makes REAL API calls** - costs approximately $0.01-0.05 per test run.

## Quick Start

```bash
# From the backend directory
cd backend

# Make sure dependencies are installed
poetry install

# Run the integration test
poetry run python test_agents_integration.py
```

## What It Tests (All REAL, No Mocks)

### 1. **Environment Check**
- Verifies all API keys are set and masked for security
- Tests: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY

### 2. **Basic Imports**
- All modules can be imported
- No circular dependency issues

### 3. **Tools Test**
- Calculator with real math operations
- Financial metrics calculations
- Tool registry

### 4. **LLM Provider** ⚡ REAL API CALL
- Connects to OpenAI
- Makes a test completion call
- Tracks token usage

### 5. **Supabase Connection** ⚡ REAL DATABASE CALL
- Connects to your Supabase instance
- Queries documents table
- Lists available documents

### 6. **RAG Pipeline** ⚡ REAL RETRIEVAL
- Tests vector search (if documents exist)
- Retrieves relevant chunks
- Generates answer

### 7. **Agent Graph** ⚡ FULL EXECUTION
- **Runs the entire agent system end-to-end**
- Real supervisor routing
- Real LLM calls for all agents
- Real agent trace
- Shows execution time, tokens, cost

### 8. **API Endpoint Structure**
- Validates request/response models
- Ready for live server testing

## Expected Output

If everything is working, you should see:

```
============================================================
  AGENT SYSTEM INTEGRATION TEST
============================================================

✅ All dependencies installed
✅ All required environment variables set
✅ All tools working
✅ All nodes functioning
✅ Graph created successfully
✅ Execution completed
✅ API integration verified

8/8 test groups passed

🎉 All tests passed! The agent system is ready to use.
```

## Troubleshooting

### Missing Dependencies
```bash
poetry install
```

### Missing Environment Variables
Create a `.env` file in the backend directory:
```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=eyJ...
TAVILY_API_KEY=tvly-...  # Optional
COHERE_API_KEY=...       # Optional
```

### Import Errors
Make sure you're in the `backend` directory when running the test.

### Graph Execution Fails
This usually means:
- LangGraph not installed correctly
- State definition issues
- Node function errors

Check the specific error message in the output.

## What's Next?

Once all tests pass:

1. **Test with real data**: Start the FastAPI server and make real API calls
2. **Test individual agents**: Try queries that trigger different routing strategies
3. **Monitor agent trace**: Check that the right agents are being called for different query types
4. **Performance testing**: Monitor execution times and token usage

## Running the Full Server

```bash
# Start the API server
poetry run uvicorn src.api.main:app --reload --port 8000

# Test the agent endpoint (in another terminal)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Apple'\''s revenue?",
    "use_agents": true
  }'
```

## Test Coverage

This integration test makes REAL calls to:
- ✅ OpenAI API (LLM generation)
- ✅ Supabase database (document queries)
- ✅ RAG pipeline (vector search & retrieval)
- ✅ Full agent graph execution
- ✅ All 6 agents with real routing

### Cost & Performance
- **Cost**: ~$0.01-0.05 per test run (OpenAI API)
- **Duration**: 15-45 seconds depending on query complexity
- **Rate limits**: Be aware of OpenAI rate limits

### What You'll See
The test query is: "What is 100 + 250 divided by 2?"

This will:
1. Route through supervisor (detects math query)
2. Execute research or analysis agent
3. Run fact checker
4. Synthesize final answer
5. Show complete trace with timing
