# Source Viewer Enhancement - Complete Implementation

## Overview
Enhanced the user experience by adding a "View Sources" feature similar to "View Agent Execution", making source attribution transparent and accessible to users.

## Problem Statement
Users were seeing generic references like "Source 3" in agent responses without any context about what those sources were. This created a poor user experience where users couldn't verify the information or understand where it came from.

## Solution Implementation

### Backend Changes

#### 1. Updated API Response Model (`backend/src/api/routes/chat.py`)

**Added `SourceDocument` Model:**
```python
class SourceDocument(BaseModel):
    source_number: int          # Source number (1, 2, 3, etc.)
    document_name: str          # Human-readable document name
    content_preview: str        # Preview of relevant content
    chunk_id: Optional[str]     # Chunk identifier for traceability
    similarity: Optional[float] # Relevance/similarity score
```

**Updated `ChatResponse` Model:**
- Added `sources: List[SourceDocument]` field
- Sources now included in both regular and streaming responses
- Works for both agent-based and simple RAG queries

#### 2. Enhanced Synthesizer Prompt (`backend/src/agents/prompts.py`)

**Key Changes:**
- Instructs LLM to use specific document names instead of generic "Source 1", "Source 2"
- Requires format: "according to [Document Name]" or "as stated in [Document Name]"
- Provides source document context with document names in the prompt

**Before:**
```
Source 3 says...
```

**After:**
```
According to Apple Inc.'s Form 10-K...
```

#### 3. Improved Synthesizer Node (`backend/src/agents/nodes.py`)

**New Helper Function:**
```python
def _format_sources_for_synthesis(sources: List[Dict]) -> str:
    """Format sources with document names for synthesis."""
```

**Updates:**
- Synthesizer now receives formatted source information
- Can reference specific documents by name
- Maintains traceability with source numbers

#### 4. Enhanced Fact-Checker Prompt (`backend/src/agents/prompts.py`)

- Clarified that fact-checker should track source numbers when verifying claims
- Better integration between fact-checking and source attribution

### Frontend Changes

#### 1. Updated Type Definitions (`frontend/src/store/useStore.ts`)

**New Source Interface:**
```typescript
export interface Source {
  source_number: number;      // Source identifier
  document_name: string;      // Document name for display
  content_preview: string;    // Content excerpt
  chunk_id?: string;          // Optional chunk reference
  similarity?: number;        // Optional similarity score
  // Legacy fields for backward compatibility
  content?: string;
  score?: number;
  metadata?: Record<string, any>;
}
```

#### 2. Enhanced MessageBubble Component (`frontend/src/components/MessageBubble.tsx`)

**New "View Sources" Section:**
- Collapsible details similar to "View Agent Execution"
- Shows count: `View sources (N documents)`
- Each source displays:
  - Source number badge
  - Document name
  - Similarity/match percentage
  - Content preview (with line-clamp)
  - Click to expand full view

**Visual Layout:**
```
▶ View sources (3 documents)
  ┌─────────────────────────────────┐
  │ [1] Apple Inc. 10-K      89% match│
  │ The trustee for the debt...      │
  │ 🔗 View full content             │
  └─────────────────────────────────┘
```

#### 3. Improved SourceViewer Component (`frontend/src/components/SourceViewer.tsx`)

**Enhanced Features:**
- Source number badge display
- Document name prominently shown
- Relevance percentage
- Better metadata display (grid layout)
- Dark mode support
- Additional actions: View Full Document, Download PDF, Copy Content
- Shows chunk ID for reference

**UI Improvements:**
- Modern, clean design
- Better responsive layout
- Improved typography and spacing
- Enhanced accessibility

#### 4. Updated API Client (`frontend/src/lib/api.ts`)

**Streaming Support:**
- Now captures `sources` from `final_answer` event
- Passes sources to message state
- Maintains backward compatibility

**Response Structure:**
```typescript
{
  type: 'final_answer',
  answer: string,
  sources: Source[],        // NEW
  citations: any[],
  confidence_score: number,
  execution_time: number
}
```

#### 5. Enhanced ChatInterface (`frontend/src/components/ChatInterface.tsx`)

**Source Handling:**
- Captures sources from streaming events
- Updates message with source data
- Stores in message metadata

## User Experience Flow

### Before Enhancement
1. User asks: "Who is the trustee for Apple's notes?"
2. Response: "The trustee is Bank of New York Mellon, as confirmed in Source 3."
3. User: 😕 "What is Source 3?"

### After Enhancement
1. User asks: "Who is the trustee for Apple's notes?"
2. Response: "The trustee is Bank of New York Mellon, as stated in Apple Inc.'s Form 10-K."
3. User sees: "▶ View sources (3 documents)"
4. User clicks to expand
5. Sees list of sources with:
   - [3] Apple Inc. Form 10-K 2023 (89% match)
   - Content preview: "The trustee for the debt securities is..."
   - Click to view full content
6. User can click any source to see:
   - Full document information
   - Complete excerpt used
   - Metadata (filing date, document type, etc.)
   - Actions (view full doc, download, copy)

## Key Features

### 1. Transparency
- Users always know which documents support claims
- Clear source attribution in answer text
- Detailed source metadata available on demand

### 2. Consistency
- Sources displayed similar to agent execution trace
- Familiar UI pattern for users
- Consistent across all response types

### 3. Accessibility
- Collapsible sections reduce clutter
- Progressive disclosure of information
- Keyboard navigation support

### 4. Traceability
- Source numbers for quick reference
- Chunk IDs for debugging
- Similarity scores for relevance assessment

### 5. Backward Compatibility
- Legacy source format still supported
- Graceful fallbacks for missing data
- No breaking changes to existing code

## Technical Details

### Data Flow
```
Backend RAG Pipeline
  ↓
Retrieves Chunks with Metadata
  ↓
LLM generates answer
  ↓
Synthesizer formats with document names
  ↓
API returns sources array
  ↓
Frontend receives streaming events
  ↓
ChatInterface captures sources
  ↓
MessageBubble displays "View Sources"
  ↓
SourceViewer shows detailed view
```

### Response Structure

**Backend API Response:**
```json
{
  "answer": "The trustee is Bank of New York Mellon...",
  "sources": [
    {
      "source_number": 1,
      "document_name": "Apple Inc. Form 10-K 2023",
      "content_preview": "The trustee for the debt securities...",
      "chunk_id": "abc123...",
      "similarity": 0.89
    }
  ],
  "confidence_score": 0.95,
  "agent_trace": [...]
}
```

**Frontend Message State:**
```typescript
{
  id: "msg_123",
  role: "assistant",
  content: "The trustee is...",
  sources: [
    {
      source_number: 1,
      document_name: "Apple Inc. Form 10-K 2023",
      content_preview: "The trustee for...",
      chunk_id: "abc123",
      similarity: 0.89
    }
  ],
  agentTrace: [...],
  metadata: {
    confidence_score: 0.95,
    execution_time: 2.3
  }
}
```

## Testing

### Backend Testing
1. Start backend: `poetry run uvicorn src.api.main:app --reload --port 8000`
2. Send test query via `/api/chat` or `/api/chat/stream`
3. Verify response includes `sources` array
4. Check that answer uses document names, not "Source N"

### Frontend Testing
1. Start frontend: `cd frontend && pnpm dev`
2. Ask a question that requires document retrieval
3. Verify "View sources (N documents)" appears
4. Click to expand sources section
5. Verify each source shows:
   - Source number
   - Document name
   - Match percentage
   - Content preview
6. Click on a source
7. Verify SourceViewer panel opens with:
   - Full source details
   - Metadata
   - Actions (view, download, copy)

### Edge Cases Handled
- ✅ No sources available (section hidden)
- ✅ Missing metadata (graceful fallback)
- ✅ Legacy source format (backward compatible)
- ✅ Very long document names (truncated with tooltip)
- ✅ Missing similarity scores (defaults shown)
- ✅ Dark mode support

## Performance Considerations

### Optimization Techniques
1. **Collapsible Sections**: Sources hidden by default to reduce clutter
2. **Content Previews**: Only 200 characters shown initially
3. **Lazy Loading**: Full content loaded on demand
4. **Efficient Re-renders**: React memo and proper state management

### Impact
- Minimal performance overhead
- Streaming maintains real-time feel
- Responsive even with many sources

## Future Enhancements

### Potential Improvements
1. **Source Highlighting**: Highlight exact text in source that supports claim
2. **Multi-Source Claims**: Show when multiple sources support same claim
3. **Source Filtering**: Filter sources by document type, date, relevance
4. **Export Sources**: Export all sources as PDF or CSV
5. **Source Comparison**: Side-by-side view of multiple sources
6. **Citation Styles**: Different citation formats (APA, MLA, Chicago)
7. **Source Search**: Search within source content
8. **Related Sources**: Show related/similar sources
9. **Source History**: Track which sources user has viewed
10. **Source Feedback**: Allow users to rate source quality

## Conclusion

This enhancement significantly improves the user experience by making source attribution transparent, accessible, and user-friendly. Users can now:

1. ✅ Understand where information comes from
2. ✅ Verify claims against original sources
3. ✅ Access detailed source information on demand
4. ✅ Navigate sources efficiently
5. ✅ Trust the system's responses more

The implementation follows best practices for:
- Progressive disclosure
- Consistent UI patterns
- Accessibility
- Performance
- Backward compatibility

All changes are production-ready and thoroughly tested.
