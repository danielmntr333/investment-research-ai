# Streaming Implementation Guide

## Overview

This document describes the real-time streaming implementation that provides users with live updates during query processing, similar to ChatGPT and Perplexity.

## Architecture

### Backend Components

#### 1. LLM Provider (`backend/src/llm/provider.py`)

**New Method: `generate_with_context_stream()`**
- Streams tokens as they are generated from OpenAI API
- Yields events: `token`, `sources`, `done`, `error`
- Provides character-by-character response generation

```python
async for event in llm_provider.generate_with_context_stream(query, context_chunks):
    if event['type'] == 'token':
        # Stream individual token
        yield event['content']
```

#### 2. RAG Pipeline (`backend/src/rag/pipeline.py`)

**New Method: `query_stream()`**
- Emits progress events at each pipeline stage:
  - `query_transform` - Query analysis/transformation
  - `retrieval` - Document search
  - `reranking` - Result prioritization
  - `generation` - Answer generation with tokens
- Provides transparency into RAG process

```python
async for event in rag_pipeline.query_stream(question):
    if event['type'] == 'step':
        # Pipeline progress update
        print(f"{event['step']}: {event['status']}")
    elif event['type'] == 'token':
        # Stream answer token
        yield event['content']
```

#### 3. Agent Graph (`backend/src/agents/graph.py`)

**New Method: `arun_stream()`**
- Streams agent execution in real-time using LangGraph's `astream`
- Yields events as each agent starts and completes
- Shows live agent activity instead of batch after completion

```python
async for event in agent_graph.arun_stream(query):
    if event['type'] == 'agent_start':
        # Agent starting execution
        print(f"{event['agent']}: {event['action']}")
```

#### 4. Chat Streaming Endpoint (`backend/src/api/routes/chat.py`)

**Updated: `/api/chat/stream` endpoint**
- Handles both RAG and Agent streaming modes
- Converts internal events to SSE (Server-Sent Events) format
- Event types:
  - `pipeline_step` - RAG pipeline progress
  - `agent_step` - Agent execution updates
  - `content` - Token-by-token text
  - `sources_found` - Source documents found
  - `final_answer` - Complete response with metadata
  - `error` - Error handling

### Frontend Components

#### 1. API Client (`frontend/src/lib/api.ts`)

**Updated: `streamMessage()` method**
- Parses SSE stream from backend
- Handles multiple event types
- Yields events to UI for real-time display

#### 2. Chat Interface (`frontend/src/components/ChatInterface.tsx`)

**New Features:**
- **Pipeline Step Indicator**: Shows current RAG stage (retrieval, reranking, generation)
- **Agent Status Indicator**: Displays active agent and action
- **Token Streaming**: Character-by-character answer display with animated cursor
- **Elapsed Timer**: Shows processing time in real-time
- **Better Error Handling**: User-friendly error messages with recovery hints

**UI States:**
1. Pipeline processing → Blue indicator with stage name
2. Agent execution → Gray indicator with agent name
3. Text streaming → Answer appears character-by-character with cursor
4. Complete → Full answer with sources

## Event Flow

### Simple RAG Query (without agents)

```
User sends query
    ↓
Frontend: POST /api/chat/stream
    ↓
Backend: RAGPipeline.query_stream()
    ↓
[Event: pipeline_step] "Searching through documents..."
    ↓
[Event: pipeline_step] "Found 5 relevant chunks"
    ↓
[Event: pipeline_step] "Generating answer..."
    ↓
[Event: token] "Apple"
[Event: token] "'s"
[Event: token] " revenue"
... (continues character by character)
    ↓
[Event: done] Complete answer + sources + metadata
```

### Agent Query (with multi-agent system)

```
User sends query
    ↓
Frontend: POST /api/chat/stream (use_agents: true)
    ↓
Backend: AgentGraph.arun_stream()
    ↓
[Event: agent_step] "supervisor: analyzing query"
    ↓
[Event: agent_step] "research: searching documents"
    ↓
[Event: agent_step] "fact_checker: verifying facts"
    ↓
[Event: agent_step] "synthesizer: generating answer"
    ↓
[Event: final_answer] Complete response
```

## Configuration

### Enable/Disable Agent Mode

In `frontend/src/lib/api.ts`:
```typescript
// Line 117
use_agents: false,  // Set to false for RAG streaming, true for agent streaming
```

### Adjust Streaming Speed

In `backend/src/api/routes/chat.py`:
```python
await asyncio.sleep(0.05)  # Adjust delay between events (in seconds)
```

### Token Streaming Batch Size

OpenAI's API streams tokens as they're generated. No configuration needed - it's handled automatically.

## Benefits

### User Experience
- ✅ **Transparency**: Users see what's happening behind the scenes
- ✅ **Perceived Speed**: Character-by-character display feels faster
- ✅ **Engagement**: Live updates keep users engaged during wait time
- ✅ **Trust**: Showing process steps builds confidence in the system

### Technical
- ✅ **Non-blocking**: UI remains responsive during processing
- ✅ **Efficient**: Streams data as it's available (no buffering)
- ✅ **Error Recovery**: Can handle partial failures gracefully
- ✅ **Debuggability**: Easy to see where processing takes time

## Testing

### Test RAG Streaming
1. Upload a document
2. Ask a question (agents disabled)
3. Observe:
   - "🔍 Searching through documents..."
   - "📊 Prioritizing most relevant information..."
   - "✨ Generating answer..."
   - Answer streams character-by-character

### Test Agent Streaming
1. Enable agents in `api.ts` (`use_agents: true`)
2. Ask a complex question
3. Observe:
   - "🧭 supervisor analyzing query..."
   - "🔍 research searching documents..."
   - "✅ fact_checker verifying facts..."
   - "🔄 synthesizer generating answer..."

### Test Error Handling
1. Disconnect network mid-stream
2. Should show user-friendly error message
3. UI should reset properly

## Performance

### Metrics
- **First Token Latency**: Time until first character appears (~500ms-1s)
- **Token Throughput**: ~20-50 tokens/second (OpenAI GPT-4o-mini)
- **Pipeline Overhead**: ~50-100ms per event emission

### Optimization Tips
1. **Reduce Event Frequency**: Batch multiple tokens together
2. **Minimize Sleep Delays**: Reduce `asyncio.sleep()` durations
3. **Enable Caching**: Cache embeddings and repeated queries
4. **Parallel Retrieval**: Retrieve from multiple sources simultaneously

## Future Enhancements

### Planned
- [ ] Progress bars for each stage
- [ ] Estimated time remaining
- [ ] Pause/Resume streaming
- [ ] Token-level markdown rendering (bold/italic in real-time)
- [ ] Streaming citations (highlight sources as they're referenced)

### Advanced
- [ ] WebSocket support for lower latency
- [ ] Streaming embeddings during document upload
- [ ] Multi-user streaming (show "User X is typing...")
- [ ] Voice output streaming (TTS integration)

## Troubleshooting

### Issue: No streaming, answer appears all at once
**Cause**: Events are being buffered
**Solution**: Check that middleware isn't buffering SSE responses. Ensure `StreamingResponse` has correct media type.

### Issue: Stream cuts off mid-answer
**Cause**: Timeout or connection dropped
**Solution**: Increase timeout, add reconnection logic, implement stream resumption.

### Issue: Events arrive out of order
**Cause**: Race condition in async processing
**Solution**: Add sequence numbers to events, implement ordering buffer on frontend.

### Issue: UI freezes during streaming
**Cause**: Blocking main thread
**Solution**: Ensure async operations don't block. Use proper React state updates.

## Code Locations

### Backend
- `backend/src/llm/provider.py` - LLM streaming
- `backend/src/rag/pipeline.py` - RAG pipeline streaming
- `backend/src/agents/graph.py` - Agent execution streaming
- `backend/src/api/routes/chat.py` - HTTP endpoint

### Frontend
- `frontend/src/lib/api.ts` - SSE client
- `frontend/src/components/ChatInterface.tsx` - UI rendering

## Support

For issues or questions about streaming implementation:
1. Check console logs for event types
2. Verify SSE connection in Network tab
3. Test with simple query first
4. Review error messages in UI

## Version History

- **v1.0** (2026-01-18): Initial streaming implementation
  - Token-by-token LLM streaming
  - RAG pipeline progress events
  - Real-time agent execution
  - Visual progress indicators
  - Elapsed time tracking
  - Error handling
