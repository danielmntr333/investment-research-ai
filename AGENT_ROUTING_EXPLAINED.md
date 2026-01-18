# Agent Routing System Explained

## Overview

The multi-agent system uses a **Supervisor** to analyze each query and route it to the appropriate agent(s). This document explains how routing works and how to optimize it.

## Agent Flow Architecture

```
User Query
    ↓
SUPERVISOR (analyzes & routes)
    ↓
    ├─→ RESEARCH (document-based Q&A)
    ├─→ ANALYSIS (calculations, comparisons)
    ├─→ WEB_SEARCH (real-time external data)
    └─→ MULTI_AGENT (complex, multiple steps)
    ↓
FACT_CHECKER (validates claims)
    ↓
SYNTHESIZER (combines outputs)
    ↓
Final Answer
```

## Current Routing Behavior

### Strategy: `research`
```
SUPERVISOR → RESEARCH → FACT_CHECKER → SYNTHESIZER
```
- Used for: Document-based questions
- Uses: RAG pipeline (retrieval + generation)
- Example: "What was Apple's revenue in 2024?"

### Strategy: `analysis`
```
SUPERVISOR → ANALYSIS → FACT_CHECKER → SYNTHESIZER
```
- Used for: Comparative analysis, calculations
- Uses: LLM + tools (calculator, chart generator)
- Example: "Compare Apple and Microsoft's revenue growth"

### Strategy: `web_search`
```
SUPERVISOR → WEB_SEARCH → RESEARCH → FACT_CHECKER → SYNTHESIZER
```
- Used for: Real-time/current information
- Uses: Tavily API for web search
- **Important**: After web search, it ALWAYS goes to RESEARCH
- Example: "What is Apple's current stock price?"

### Strategy: `multi_agent`
```
SUPERVISOR → RESEARCH → (other agents) → FACT_CHECKER → SYNTHESIZER
```
- Used for: Complex queries needing multiple agents
- Currently starts with RESEARCH

## The Problem You Encountered

### Query
```
"Who is the trustee of the notes in the Apple 10-K?"
```

### What Happened
1. Supervisor incorrectly chose `web_search` strategy
2. System searched web first (unnecessary)
3. Then went to research (correct, but after web search)
4. Found answer in documents (should have gone here directly)

### Why It Happened

**Root Cause**: The supervisor prompt wasn't explicit enough about preferring document-based research when documents are available.

The old prompt said:
```
- WEB_SEARCH: For real-time/current information not in documents
```

But it didn't emphasize:
- ✅ Prefer RESEARCH when documents are available
- ✅ Only use WEB_SEARCH for explicitly time-sensitive queries

## The Fix Applied

### Updated Supervisor Prompt

Added explicit routing rules:

```
IMPORTANT ROUTING RULES:
1. If documents are available and the query asks about information 
   typically found in those documents (financial data, company info, 
   SEC filings, etc.), choose RESEARCH

2. Only choose WEB_SEARCH if:
   - No relevant documents are uploaded, OR
   - Query explicitly asks for current/real-time data 
     (stock prices, today's news, recent events, "current", "today", "latest")

3. Prefer RESEARCH over WEB_SEARCH when documents are available - 
   web search should be the exception, not the default
```

## How Supervisor Makes Decisions

The supervisor uses an LLM call with:

### Inputs
1. **Query text**: The user's question
2. **Available documents**: List of uploaded documents with types
3. **Routing rules**: Guidelines from the prompt

### Process
```python
prompt = SUPERVISOR_PROMPT.format(
    query=user_query,
    document_list=uploaded_documents
)

response = llm.generate(prompt)  # Returns JSON decision
decision = {
    "strategy": "research|analysis|web_search|multi_agent",
    "reasoning": "why this strategy was chosen",
    "needs_web_search": true/false,
    "complexity": 1-5,
    "estimated_steps": number
}
```

### Output
- **strategy**: Which agent path to take
- **reasoning**: Explanation for debugging
- **needs_web_search**: Boolean flag (informational)
- **complexity**: Estimated difficulty (1-5)

## Routing Decision Matrix

| Query Type | Keywords | Has Docs? | Strategy |
|------------|----------|-----------|----------|
| Document fact | "in the 10-K", "according to" | ✅ | `research` |
| Financial data | "revenue", "earnings", "balance sheet" | ✅ | `research` |
| Current price | "current price", "today", "now" | Any | `web_search` |
| Recent news | "latest", "recent", "today's news" | Any | `web_search` |
| Comparison | "compare", "difference between" | ✅ | `analysis` |
| Calculation | "calculate", "what is X% of Y" | ✅ | `analysis` |
| Complex multi-step | Multiple questions | ✅ | `multi_agent` |

## Testing Routing Behavior

### Run Routing Test
```bash
cd backend
poetry run python test_routing.py
```

This tests various query types and shows routing decisions:
```
📚 Query: Who is the trustee of the notes in the Apple 10-K?
   Strategy: RESEARCH
   Reasoning: Document-based question about 10-K filing
   ✅ Correct routing

🌐 Query: What is Apple's current stock price?
   Strategy: WEB_SEARCH
   Reasoning: Requires real-time market data
   ✅ Correct routing
```

### Run Full API Test
```bash
poetry run python test_api_web_search.py
```

## Why Web Search Goes to Research After

You might wonder: **Why does `web_search` route to `research` after getting web results?**

### Design Rationale

```python
workflow.add_edge("web_search", "research")
```

**Purpose**: Combine external web data with internal documents

**Example Flow**:
1. Query: "What is Apple's current stock price and how does it compare to last quarter?"
2. **WEB_SEARCH**: Fetches current price ($175.43)
3. **RESEARCH**: Retrieves last quarter's data from documents
4. **SYNTHESIZER**: Combines both to answer fully

**Benefits**:
- Enriches document answers with real-time data
- Provides context from both sources
- More comprehensive responses

**Tradeoff**:
- Adds extra step even when not needed
- If routing is wrong, does unnecessary work

## Optimizing Routing

### 1. **Improve Prompt Engineering** (Done ✅)
- Added explicit routing rules
- Emphasized document preference
- Clear keywords for each strategy

### 2. **Use Better LLM for Supervisor**
Current: GPT-4o-mini (fast, cheap, sometimes wrong)

Consider: GPT-4o (slower, costs more, more accurate)

Change in `src/llm/provider.py`:
```python
# For supervisor calls, use better model
if is_routing_decision:
    model = "gpt-4o"  # More accurate routing
else:
    model = "gpt-4o-mini"  # Fast for other tasks
```

### 3. **Add Keyword-Based Pre-Routing**

Before LLM call, check for obvious patterns:

```python
# Pseudo-code
if "current" in query or "today" in query or "stock price" in query:
    strategy = "web_search"
elif "compare" in query or "calculate" in query:
    strategy = "analysis"
elif has_documents:
    strategy = "research"
else:
    strategy = llm_routing_decision()
```

### 4. **Add Routing Confidence Score**

Ask supervisor to include confidence:
```json
{
    "strategy": "research",
    "confidence": 0.95,
    "reasoning": "..."
}
```

If confidence < 0.8, could ask user or try multiple strategies.

### 5. **Separate Web Search from Research Path**

Change graph so `web_search` doesn't always go to research:

```python
# Current
workflow.add_edge("web_search", "research")

# Alternative: conditional routing
workflow.add_conditional_edges(
    "web_search",
    self._route_after_web_search,
    {
        "research": "research",      # If docs might help
        "synthesizer": "synthesizer"  # If web search is enough
    }
)
```

## Common Routing Issues

### Issue 1: Documents Ignored
**Symptom**: Has docs but routes to `web_search`

**Fix**: Improve supervisor prompt (already done ✅)

### Issue 2: Missing Real-Time Data
**Symptom**: Routes to `research` for current data

**Fix**: Add keywords like "current", "today", "latest" to query

### Issue 3: Slow Responses
**Symptom**: Every query does web search + research

**Fix**: Check supervisor decisions in agent_trace

### Issue 4: Incorrect Strategy
**Symptom**: Comparison routed to `research` instead of `analysis`

**Fix**: Make strategy keywords more explicit in prompt

## Monitoring Routing Decisions

### Check Agent Trace in Response

```javascript
// Frontend: Display agent trace
response.agent_trace.forEach(step => {
    console.log(`${step.agent}: ${step.action} (${step.duration}s)`);
});
```

### Example Trace (Good Routing)
```
1. supervisor: query_analysis (2.1s)
2. research: rag_query (4.5s)
3. fact_checker: claim_verification (3.2s)
4. synthesizer: final_synthesis (2.8s)
```

### Example Trace (Bad Routing)
```
1. supervisor: query_analysis (2.1s)
2. web_search: external_search (5.0s)  ← Unnecessary!
3. research: rag_query (4.5s)
4. fact_checker: claim_verification (3.2s)
5. synthesizer: final_synthesis (2.8s)
```

## Configuration Files

- **Supervisor Prompt**: `backend/src/agents/prompts.py` (SUPERVISOR_PROMPT)
- **Agent Graph**: `backend/src/agents/graph.py` (_build_graph method)
- **Routing Logic**: `backend/src/agents/graph.py` (_route_query method)
- **Node Implementations**: `backend/src/agents/nodes.py`

## Future Enhancements

### 1. **Learning-Based Routing**
- Track routing success rate
- Learn which queries work best with which strategy
- Auto-adjust routing over time

### 2. **User Feedback Loop**
- "Was this answer helpful?" button
- If no → log query + routing decision
- Improve prompt based on patterns

### 3. **Multi-Strategy Parallel Execution**
- For ambiguous queries, run research + web_search in parallel
- Synthesizer picks best answer
- Slower but more comprehensive

### 4. **Cost-Aware Routing**
- web_search costs money (Tavily API)
- Could have "budget" mode that avoids web search
- Or require user confirmation for expensive operations

### 5. **Query Classification Model**
- Train a lightweight classifier for common query types
- Fast pre-routing before LLM supervisor
- Falls back to LLM for edge cases

## Summary

**Your original question**: "Who is the trustee of the notes in the Apple 10-K?"

- ❌ **Before**: Routed to `web_search` → unnecessary web API call
- ✅ **After**: Should route to `research` → direct document lookup

**Key Takeaway**: The supervisor uses an LLM to make routing decisions. Better prompts = better routing. We've now improved the prompt to strongly prefer document-based research when documents are available.

**Test It**: The backend should auto-reload with the new prompt. Try your query again and check the agent_trace - you should see `research` instead of `web_search`.
