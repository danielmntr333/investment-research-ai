# Web Search Agent Fix

## Problem

When asking about stock prices (e.g., "What is the current stock price of Google?"), the web search agent was not being triggered, resulting in a generic response telling the user to check external websites.

## Root Cause

The issue was **NOT with the routing logic** - the supervisor was correctly identifying that the query needed web search. The problem was:

1. **Missing dependency**: The `tavily-python` package was listed in `pyproject.toml` but not installed in the Poetry environment
2. **Silent failure**: When the web_search node tried to import tavily and failed, it caught the exception and continued without web search results

## Agent Flow Before Fix

```
SUPERVISOR → RESEARCH → FACT_CHECKER → SYNTHESIZER
         ↓
  (chose web_search strategy correctly)
  (but web_search node failed silently)
```

## Agent Flow After Fix

```
SUPERVISOR → WEB_SEARCH → RESEARCH → FACT_CHECKER → SYNTHESIZER
         ↓           ↓
  web_search    Tavily API search
   strategy      (real-time data)
```

## Solution Applied

1. **Updated Poetry lock file**:
   ```bash
   cd backend
   poetry lock
   ```

2. **Installed missing dependency**:
   ```bash
   poetry install
   ```
   
   This installed:
   - `tavily-python` (0.5.4) - Web search client
   - Related dependencies (matplotlib, etc.)

3. **Fixed emoji encoding issues** in:
   - `test_web_search.py` - Diagnostic script
   - `src/db/supabase.py` - Database connection

## Verification

Created and ran `backend/test_web_search.py` which tests:
- ✅ Supervisor routing decision
- ✅ Web search node execution
- ✅ Tavily API integration
- ✅ Real-time data retrieval

### Test Results

```
Query: "What is the current stock price of Google?"

Supervisor Decision:
- Strategy: web_search ✓
- Reasoning: Query requires real-time data ✓

Agent Execution:
1. SUPERVISOR: query_analysis (2.59s)
2. WEB_SEARCH: external_search (5.23s) ← Now working!
3. RESEARCH: rag_query (5.72s)
4. FACT_CHECKER: claim_verification (4.52s)
5. SYNTHESIZER: final_synthesis (7.58s)

Web Search Results: 5 sources found
- WallStreetZen
- TradingView  
- Investing.com
- Robinhood
- Macrotrends

Final Answer: "The current stock price of Google is approximately $329.55 to $330.34..." with citations
```

## Configuration Required

For web search to work, you need:

1. **TAVILY_API_KEY** in `backend/.env`:
   ```env
   TAVILY_API_KEY=tvly-xxxxxxxxxx
   ```

2. **Get API key from**: https://tavily.com/

## How the System Works

### 1. Supervisor Routing
The supervisor analyzes queries and routes them based on:
- **research**: Document-based questions (RAG)
- **analysis**: Comparative analysis, calculations
- **web_search**: Real-time/current information
- **multi_agent**: Complex queries needing multiple agents

Defined in: `backend/src/agents/prompts.py`

### 2. Web Search Triggers
Automatically triggered for queries about:
- Current stock prices, market data
- Recent news or events
- Real-time information
- Data not in uploaded documents

### 3. Web Search Node
Located in: `backend/src/agents/nodes.py`

Uses Tavily API to:
1. Search the web for current information
2. Return top 5 results with titles, URLs, content, scores
3. Pass results to research agent for synthesis

### 4. Synthesis
The synthesizer combines:
- Web search results (real-time data)
- Document retrieval results (user's documents)
- Fact-checking verification
- Proper citations for all sources

## Testing Web Search

Run the diagnostic script:
```bash
cd backend
poetry run python test_web_search.py
```

This will:
1. Check if TAVILY_API_KEY is configured
2. Test supervisor routing for stock price queries
3. Execute full agent graph with web search
4. Display detailed trace and results

## Common Issues

### "No module named 'tavily'"
**Solution**: Run `poetry install` in backend directory

### "TAVILY_API_KEY not set"
**Solution**: Get API key from https://tavily.com/ and add to `.env`

### "Supervisor chose 'research' instead of 'web_search'"
**Solution**: Improve prompt or add explicit keywords. Current supervisor prompt already handles stock prices correctly.

### Unicode/Emoji encoding errors on Windows
**Solution**: Already fixed - removed emoji characters from print statements

## Related Files

- `backend/src/agents/nodes.py` - Web search node implementation
- `backend/src/agents/graph.py` - Agent orchestration and routing
- `backend/src/agents/prompts.py` - Supervisor routing prompt
- `backend/test_web_search.py` - Diagnostic test script
- `backend/pyproject.toml` - Dependencies including tavily-python

## Routing Optimization

After fixing web search, you may notice it triggers even for document-based queries. See `AGENT_ROUTING_EXPLAINED.md` for:
- How the supervisor decides routing
- Why web_search goes to research after
- How to optimize routing decisions
- Testing routing behavior

## Future Enhancements

1. **Add web search caching** - Cache recent searches to reduce API calls
2. **Configurable search depth** - Allow "basic" vs "advanced" Tavily searches
3. **Result reranking** - Use Cohere to rerank web search results by relevance
4. **Source diversity** - Ensure results come from multiple domains
5. **Fallback strategies** - Try alternative search APIs if Tavily fails
6. **Smart routing** - Better supervisor prompt to avoid unnecessary web searches
