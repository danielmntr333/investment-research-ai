    state['web_search_results'] = results
    state['agent_trace'].append({
        'agent': 'web_search',
        'action': 'external_search',
        'results_found': len(results),
        'duration': 0.8
    })
    
    return state
```

**Research Agent Gets Historical Data**:
```python
# Retrieve Q4 earnings data from uploaded documents
q4_data = await rag_pipeline.retrieve(
    "Apple Q4 2023 earnings stock price performance",
    filters={"document_id": "apple_10k_id"}
)

# Found: 
# "Q4 2023 financial results... EPS $1.46, revenue $89.5B, 
#  stock closed at $178 on earnings day..."
```

**Synthesizer Combines Web + Document Data**:
```python
# agents/nodes.py - synthesizer_node()

synthesis_prompt = f"""
Combine real-time and historical data:

Real-time (Web):
{web_search_results}

Historical (Documents):
{document_data}

Create comprehensive answer showing:
1. Current stock price
2. Historical earnings context
3. Performance comparison
"""

final_answer = await llm.generate(synthesis_prompt)
```

**Agent Trace**:
```
┌─────────────────────────────────────────────────────────┐
│  🧭 Supervisor (0.6s)                                   │
│  └─ Detected need for real-time data                    │
│     Routed to: Web Search + Research + Synthesizer      │
│                                                          │
│  🌐 Web Search Agent (0.8s)                             │
│  └─ Searched: "Apple stock price today"                 │
│     Found: 5 results (Yahoo Finance, Bloomberg, etc.)   │
│     Current price: $195.42 (+2.3%)                      │
│                                                          │
│  🔍 Research Agent (1.2s)                               │
│  └─ Retrieved Q4 2023 earnings data                     │
│     Found: EPS $1.46, Revenue $89.5B, Price ~$178       │
│                                                          │
│  🔄 Synthesizer (1.2s)                                  │
│  └─ Combined web + document data                        │
│     Calculated: 9.8% gain since earnings               │
│     Added market context and interpretation             │
│                                                          │
│  ⚡ Total: 3.8 seconds                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Viewing Evaluation Metrics

### What the User Sees

Sarah clicks on "Metrics" tab to check system quality:

```
┌─────────────────────────────────────────────────────────┐
│  📊 Evaluation Metrics                                   │
│                                         [🔄 Refresh]     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Overall Pass Rate                              │    │
│  │                                                 │    │
│  │           94.2%                                 │    │
│  │                                                 │    │
│  │  Based on 50 test queries                      │    │
│  │  Last updated: 2 hours ago                     │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Key Metrics                                             │
│  ┌──────────────────┬──────────────────┬─────────────┐ │
│  │ Faithfulness     │ ████████████ 0.89│ ✓ Passing   │ │
│  │ Answer Relevancy │ █████████████0.92│ ✓ Passing   │ │
│  │ Context Precision│ ██████████  0.84 │ ✓ Passing   │ │
│  │ Numerical Accuracy███████████ 0.96  │ ✓ Passing   │ │
│  │ Citation Quality │ ███████████ 0.88 │ ✓ Passing   │ │
│  │ LLM Judge Overall│ ████████████ 4.2 │ ✓ Passing   │ │
│  └──────────────────┴──────────────────┴─────────────┘ │
│                                                          │
│  Performance Metrics                                     │
│  • Avg Response Time: 3.2s (p50) | 5.1s (p95)          │
│  • Cost per Query: $0.09                               │
│  • Cache Hit Rate: 67%                                 │
│  • Embedding Reuse: 73%                                │
│                                                          │
│  📈 Trends (Last 30 Days)                               │
│                                                          │
│   1.0 ┤              ●───●                              │
│       │            ●       ●                            │
│  0.90 ┤          ●           ●──●                       │
│       │        ●                                        │
│  0.80 ┤    ●─●                                          │
│       │  ●                                              │
│  0.70 └─────────────────────────────────────           │
│        Dec 20    Jan 5       Jan 18                    │
│                                                          │
│        ── Faithfulness (improving)                      │
│        ── Answer Relevancy (stable)                     │
│        ── Numerical Accuracy (stable high)              │
│                                                          │
│  Recent Test Results                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Test: "What was Apple's revenue?"                │  │
│  │ Status: ✓ Passed | Faithfulness: 0.94           │  │
│  │ Answer: Correct | Citations: 2/2 valid          │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Test: "Compare R&D spending"                     │  │
│  │ Status: ✓ Passed | Numerical Accuracy: 1.0      │  │
│  │ All 4 numbers verified against sources          │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ Test: "Multi-hop reasoning"                      │  │
│  │ Status: ✓ Passed | Context Recall: 0.88         │  │
│  │ Retrieved all necessary documents               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Technical Implementation

**Frontend** (`frontend/src/components/MetricsDashboard.tsx`):
```typescript
function MetricsDashboard() {
  const [data, setData] = useState<MetricsData | null>(null);
  
  useEffect(() => {
    fetchMetrics();
  }, []);
  
  const fetchMetrics = async () => {
    const { data } = await api.getMetrics();
    setData(data);
  };
  
  return (
    <div className="space-y-6">
      {/* Pass Rate Card */}
      <Card>
        <CardContent>
          <h3>Overall Pass Rate</h3>
          <div className="text-5xl font-bold text-green-600">
            {(data.pass_rate * 100).toFixed(1)}%
          </div>
        </CardContent>
      </Card>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4">
        {Object.entries(data.latest_metrics).map(([metric, value]) => (
          <MetricCard 
            key={metric}
            name={metric}
            value={value}
            trend={data.trends[metric]}
          />
        ))}
      </div>
      
      {/* Trend Chart */}
      <Card>
        <LineChart data={prepareChartData(data.history)}>
          <Line dataKey="faithfulness" stroke="#8884d8" />
          <Line dataKey="answer_relevancy" stroke="#82ca9d" />
        </LineChart>
      </Card>
    </div>
  );
}
```

**Backend** (`backend/src/api/routes/evals.py`):
```python
@router.get("/metrics")
async def get_metrics():
    """Get current evaluation metrics and trends."""
    
    # Get latest evaluation run
    latest = await db.table('evaluation_runs')\
        .select('*')\
        .order('timestamp', desc=True)\
        .limit(1)\
        .single()
    
    # Get historical data (30 days)
    history = await db.table('evaluation_runs')\
        .select('*')\
        .gte('timestamp', thirty_days_ago)\
        .order('timestamp')
    
    # Calculate trends
    trends = calculate_trends(history)
    
    return {
        'latest_metrics': json.loads(latest['metrics']),
        'trends': trends,
        'history': format_history(history),
        'pass_rate': latest['pass_rate'],
        'last_updated': latest['timestamp']
    }
```

**Evaluation Pipeline** (`backend/src/evaluation/pipeline.py`):
```python
# This runs daily via Modal scheduled function

async def run_full_evaluation():
    """
    Comprehensive evaluation on golden dataset.
    """
    
    # Load golden dataset
    golden = GoldenDataset()
    test_cases = golden.get_all_cases()  # 50 test cases
    
    # Run RAGAS evaluation
    ragas_evaluator = RAGASEvaluator(rag_pipeline, llm)
    ragas_results = await ragas_evaluator.evaluate_test_set(test_cases)
    
    # Run custom metrics
    custom_metrics = FinancialMetrics()
    custom_results = await evaluate_custom_metrics(test_cases, custom_metrics)
    
    # Run LLM-as-judge (on sample to save costs)
    judge = LLMJudge(llm)
    judge_results = await judge.batch_evaluate(test_cases[:20])
    
    # Aggregate metrics
    metrics = {
        'faithfulness': ragas_results['overall_scores']['faithfulness'],
        'answer_relevancy': ragas_results['overall_scores']['answer_relevancy'],
        'context_precision': ragas_results['overall_scores']['context_precision'],
        'numerical_accuracy': custom_results['numerical_accuracy'],
        'citation_quality': custom_results['citation_rate'],
        'llm_judge_overall': judge_results['avg_overall']
    }
    
    # Store results
    await db.table('evaluation_runs').insert({
        'timestamp': datetime.now(),
        'metrics': json.dumps(metrics),
        'total_cases': len(test_cases),
        'passed': count_passed(metrics),
        'pass_rate': calculate_pass_rate(metrics)
    })
    
    return metrics
```

---

## 7. Source Exploration

### What the User Sees

Sarah clicks on "[1] Source 1" citation in a response:

```
┌─────────────────────────────────────────────────────────┐
│  Source Document                                    [×]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Document: Apple_10K_2023.pdf                           │
│  Section: Item 8. Financial Data                        │
│  Page: 42                                               │
│  Relevance: 94%                                         │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ Excerpt:                                        │    │
│  │                                                 │    │
│  │ Consolidated Statements of Operations          │    │
│  │                                                 │    │
│  │ For the fiscal year ended September 30, 2023   │    │
│  │                                                 │    │
│  │ Net sales:                                      │    │
│  │   Products              $298,085 million        │    │
│  │   Services               $85,200 million        │    │
│  │ Total net sales        $383,285 million        │    │
│  │                          ^^^^^^^^^^^^^^^^        │    │
│  │                          (Referenced in answer) │    │
│  │                                                 │    │
│  │ Cost of sales:                                  │    │
│  │   Products              $189,282 million        │    │
│  │   Services               $24,855 million        │    │
│  │ Total cost of sales    $214,137 million        │    │
│  │                                                 │    │
│  │ Gross margin           $169,148 million        │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  [View Full Document] [Download PDF]                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Technical Implementation

**Frontend** (`frontend/src/components/SourceViewer.tsx`):
```typescript
function SourceViewer() {
  const { selectedSource, isSourceViewerOpen, closeSourceViewer } = useStore();
  
  if (!selectedSource) return null;
  
  return (
    <Sheet open={isSourceViewerOpen} onOpenChange={closeSourceViewer}>
      <SheetContent className="w-full sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle>Source Document</SheetTitle>
          <SheetDescription>
            Relevance Score: {(selectedSource.score * 100).toFixed(1)}%
          </SheetDescription>
        </SheetHeader>
        
        <div className="mt-6 space-y-4">
          {/* Metadata */}
          <div className="bg-gray-50 rounded-lg p-4">
            <dl className="space-y-1 text-sm">
              <div className="flex justify-between">
                <dt>Document:</dt>
                <dd>{selectedSource.metadata.filename}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Section:</dt>
                <dd>{selectedSource.metadata.section}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Page:</dt>
                <dd>{selectedSource.metadata.page}</dd>
              </div>
            </dl>
          </div>
          
          {/* Content with highlighting */}
          <div className="prose prose-sm max-w-none">
            <h3>Excerpt:</h3>
            <div className="bg-white border rounded-lg p-4">
              <HighlightedContent 
                content={selectedSource.content}
                highlights={extractReferencedPhrases(selectedSource)}
              />
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

---

## 8. Complete System Data Flow

### Visual Flow Diagram

```
USER ACTION                 FRONTEND              BACKEND                 DATABASE
                                                                         
1. Upload PDF          
   │                   
   ├─────────────────> DocumentUpload.tsx
                       │
                       ├─ Validate file
                       │  (size, type)
                       │
                       └─────────────────> POST /api/documents/upload
                                           │
                                           ├─ Save to Supabase Storage
                                           │                              
                                           ├─ Create document record ──────> INSERT documents
                                           │
                                           └─ Queue processing
                                              │
                                              ▼
                                           RAGPipeline.process_document()
                                           │
                                           ├─ Parse PDF (PyMuPDF)
                                           ├─ Chunk (FinancialDocumentChunker)
                                           ├─ Embed (OpenAI API)
                                           │
                                           └─ Store chunks ─────────────────> INSERT chunks (230 rows)
                                                                              UPDATE documents.processed = true

2. Send Query
   │
   ├─────────────────> ChatInterface.tsx
                       │
                       ├─ Add user message to state
                       │
                       └─────────────────> POST /api/chat/stream
                                           │
                                           ▼
                                           ResearchAgentGraph.arun()
                                           │
                                           ├─ Supervisor analyzes ────────> (LLM call)
                                           │  Returns: route to "research"
                                           │
                                           ├─ Research agent:
                                           │  │
                                           │  ├─ RAG retrieval
                                           │  │  │
                                           │  │  ├─ Embed query ─────────> OpenAI API
                                           │  │  │
                                           │  │  ├─ Vector search ───────> SELECT ... ORDER BY embedding <=>
                                           │  │  │                          (10 chunks)
                                           │  │  │
                                           │  │  ├─ Keyword search ──────> SELECT ... ts_rank(search_vector)
                                           │  │  │                          (10 chunks)
                                           │  │  │
                                           │  │  ├─ RRF fusion
                                           │  │  │
                                           │  │  └─ Cohere rerank ───────> Cohere API
                                           │  │                             (top 5 chunks)
                                           │  │
                                           │  └─ Generate answer ────────> GPT-4o API
                                           │                                (with citations)
                                           │
                                           ├─ Fact checker validates ────> GPT-4 API
                                           │                                (verify claims)
                                           │
                                           ├─ Synthesizer combines
                                           │
                                           └─ Stream response chunks
                                              │
   <──────────────────────────────────────────┘
   │
   └─ Update UI in real-time
      (streaming response)

3. View Metrics
   │
   ├─────────────────> MetricsDashboard.tsx
                       │
                       └─────────────────> GET /api/evals/metrics
                                           │
                                           └─ Query evaluation_runs ─────> SELECT * FROM evaluation_runs
                                              │                             ORDER BY timestamp DESC
                                              │
   <──────────────────────────────────────────┘
   │
   └─ Display charts and metrics
```

---

## 9. Performance Characteristics

### Response Time Breakdown

**Simple Query** ("What was Apple's revenue?"):
```
Total: 2.3 seconds
├─ Supervisor: 0.4s
├─ Retrieval: 0.8s
│  ├─ Embed query: 0.2s
│  ├─ Vector search: 0.2s
│  ├─ Keyword search: 0.1s
│  └─ Rerank: 0.3s
├─ Generation: 0.7s
├─ Fact check: 0.3s
└─ Synthesis: 0.1s
```

**Complex Query** ("Compare R&D spending"):
```
Total: 4.1 seconds
├─ Supervisor: 0.5s
├─ Research (parallel): 1.8s
│  ├─ Apple retrieval: 0.9s
│  └─ Microsoft retrieval: 0.9s
├─ Analysis: 1.3s
│  ├─ Tool calls: 0.6s
│  └─ Synthesis: 0.7s
├─ Fact check: 0.3s
└─ Final synthesis: 0.2s
```

### Cost Per Query

**Simple Query**:
```
Embedding: $0.001
Vector search: $0 (database)
Reranking: $0.004
GPT-4o generation: $0.04
Fact checking: $0.01
Total: ~$0.05
```

**Complex Query**:
```
Embeddings (2 docs): $0.002
Reranking: $0.008
GPT-4o (analysis): $0.06
Tool calls: $0.01
Total: ~$0.08
```

### Caching Benefits

```
Without Cache:
- Every query generates new embeddings
- Cost per query: $0.08
- 100 queries/day = $8/day = $240/month

With Cache (67% hit rate):
- 67 queries use cache
- 33 queries generate embeddings
- Cost: $0.05 average
- 100 queries/day = $5/day = $150/month

Savings: $90/month (37.5%)
```

---

## 10. Error Handling & Edge Cases

### User Sees Error - Graceful Degradation

**Scenario**: LLM API timeout

```
┌─────────────────────────────────────────────────────────┐
│  🤖 AI Assistant                                         │
│                                                          │
│  ⚠️ I encountered a temporary issue while processing    │
│  your request. I've switched to a backup system and     │
│  will try again.                                        │
│                                                          │
│  [Retrying with fallback model...]                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Technical Implementation**:
```python
# backend/src/llm/fallback.py

async def generate_with_fallback(prompt: str):
    """Try primary, fall back to secondary on failure."""
    
    try:
        # Try primary (OpenAI GPT-4o)
        return await openai_client.generate(prompt)
    
    except (Timeout, RateLimitError) as e:
        logger.warning(f"Primary LLM failed: {e}, using fallback")
        
        # Fall back to Anthropic Claude
        return await anthropic_client.generate(prompt)
```

### No Results Found

```
┌─────────────────────────────────────────────────────────┐
│  🤖 AI Assistant                                         │
│                                                          │
│  I couldn't find information about "quantum computing"  │
│  in your uploaded documents.                            │
│                                                          │
│  Your documents cover:                                  │
│  • Apple 10-K 2023 (Financial data)                     │
│  • Microsoft 10-K 2023 (Financial data)                 │
│                                                          │
│  Would you like me to:                                  │
│  1. Search the web for this information?                │
│  2. Help you upload relevant documents?                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 11. Key Takeaways - How Everything Connects

### The Magic of Integration

1. **RAG Pipeline** (Invisible but Critical)
   - Smart chunking preserves document structure
   - Hybrid retrieval finds exact relevant sections
   - Reranking ensures precision
   - **Result**: 95%+ accuracy in finding right content

2. **Multi-Agent System** (Visible Through Trace)
   - Supervisor routes intelligently based on query type
   - Specialized agents handle specific tasks
   - Tools extend capabilities (math, charts, web)
   - **Result**: Right approach for each query automatically

3. **Evaluation Framework** (Builds Trust)
   - RAGAS provides industry-standard metrics
   - Custom metrics validate financial accuracy
   - Dashboard shows transparent quality scores
   - **Result**: Users trust the answers

4. **Frontend Experience** (Delightful UX)
   - Streaming responses feel instant
   - Agent trace shows reasoning process
   - Source viewer enables verification
   - Charts aid understanding
   - **Result**: Professional, trustworthy interface

### The Wow Factors

✨ **Speed**: 2-4 second responses despite complexity  
✨ **Accuracy**: 96% numerical accuracy with sources  
✨ **Transparency**: Full reasoning trace visible  
✨ **Intelligence**: Automatic tool selection  
✨ **Trust**: Every claim cited and verifiable  

### Production-Ready Features

✅ Multi-document support  
✅ Real-time data integration  
✅ Comparative analysis  
✅ Tool usage (calculator, charts)  
✅ Fact checking  
✅ Quality metrics  
✅ Source attribution  
✅ Error handling with fallbacks  
✅ Cost optimization (caching)  
✅ Performance monitoring  

---

## 12. Implementation Guide for Cursor

When implementing components, reference this flow:

### For Backend RAG:
```bash
@docs/plan.md @docs/rag-implementation.md @docs/user-experience.md 

Create the HybridRetriever class. It should support the query flow 
shown in section 3 where we do vector search, keyword search, RRF 
fusion, and Cohere reranking.
```

### For Agent System:
```bash
@docs/agents-implementation.md @docs/user-experience.md 

Implement the research_node function. Reference section 3 which shows 
how it retrieves chunks and generates answers with citations.
```

### For Frontend Components:
```bash
@docs/frontend-implementation.md @docs/user-experience.md 

Create the ChatInterface component with streaming support as shown 
in section 3, where responses stream in real-time.
```

### For Testing:
```bash
@docs/testing-guide.md @docs/user-experience.md 

Create integration tests that verify the complete flow from section 3:
query → supervisor → research → fact check → response
```

---

## Conclusion

This is not just an AI chatbot - it's a **production-grade intelligent research platform** that:

- Processes complex financial documents accurately
- Provides transparent, verifiable answers
- Adapts intelligently to different query types  
- Maintains high quality with comprehensive evaluation
- Delivers a professional user experience

**This is what makes it interview-worthy!** 🚀

---

## Quick Reference: Component Interactions

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│  (ChatInterface, DocumentUpload, MetricsDashboard)      │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                    API LAYER                             │
│         (FastAPI routes: chat, documents, evals)         │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐   ┌─────────────┐
│   RAG    │   │   AGENTS    │
│ Pipeline │   │   System    │
└────┬─────┘   └──────┬──────┘
     │                │
     ├─ Chunking     ├─ Supervisor
     ├─ Embeddings   ├─ Research
     ├─ Retrieval    ├─ Analysis
     └─ Reranking    ├─ Fact Check
                     └─ Synthesizer
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────┐   ┌─────────────┐
│ Database │   │ Evaluation  │
│ (Supabase)│   │  Framework  │
└──────────┘   └─────────────┘
```

Use this document to understand how all pieces fit together! 🎯# Investment Research AI - Complete User Experience Guide

## Overview

This document illustrates the complete end-to-end user experience, showing how all components (RAG, agents, evaluation, frontend) work together seamlessly. Use this to understand the full system behavior when implementing components.

**Scenario**: Sarah, an investment analyst, uses the platform to analyze Apple and Microsoft financials.

---

## 1. Initial Load - User Opens Application

### What the User Sees

```
┌─────────────────────────────────────────────────────────┐
│  Investment Research AI                    [⚙️ Settings] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│              📊 Welcome to Investment Research           │
│                                                          │
│         Upload financial documents to get started        │
│                                                          │
│              [+ New Conversation]                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Technical Implementation

**Frontend** (`frontend/src/App.tsx`):
```typescript
function App() {
  const { 
    conversations, 
    documents, 
    createConversation 
  } = useStore();
  
  useEffect(() => {
    // Load user data on mount
    loadDocuments();
    loadConversations();
  }, []);
  
  return (
    <Layout>
      <Tabs defaultValue="chat">
        <TabsList>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>
        <TabsContent value="chat">
          <ChatInterface />
        </TabsContent>
      </Tabs>
    </Layout>
  );
}
```

**Backend** (`backend/src/api/main.py`):
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

**State Initialized** (Zustand):
```typescript
{
  conversations: [],
  documents: [],
  currentConversationId: null,
  isLoading: false
}
```

---

## 2. Document Upload - Processing Financial Reports

### What the User Sees

**Step 1**: User drags files to upload area

```
┌─────────────────────────────────────────────────────────┐
│  Documents Tab                                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │     📁 Drop files here                          │    │
│  │                                                 │    │
│  │     or click to browse                          │    │
│  │     (PDF, Excel - max 10MB)                     │    │
│  │                                                 │    │
│  │          [Choose Files]                         │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Step 2**: Upload in progress

```
│  📄 Apple_10K_2023.pdf                                  │
│     15.0 MB • Uploaded 2 min ago                        │
│     ⏳ Processing... (32% complete)                     │
│     ├─ Parsing document...                    ✓         │
│     ├─ Extracting tables...                   ✓         │
│     ├─ Chunking content...                    ⏳        │
│     ├─ Generating embeddings...               ⏳        │
│     └─ Storing in database...                 ⏳        │
│                                                          │
│  📄 Microsoft_10K_2023.pdf                              │
│     12.0 MB • Uploaded just now                         │
│     ⏳ Processing... (18% complete)                     │
```

**Step 3**: Processing complete

```
│  📄 Apple_10K_2023.pdf                                  │
│     15.0 MB • Uploaded 3 min ago                        │
│     ✅ Processing complete (127 chunks created)          │
│                                                          │
│  📄 Microsoft_10K_2023.pdf                              │
│     12.0 MB • Uploaded 2 min ago                        │
│     ✅ Processing complete (103 chunks created)          │
```

### Technical Implementation

**Frontend** (`frontend/src/components/DocumentUpload.tsx`):
```typescript
const handleFiles = async (files: File[]) => {
  for (const file of files) {
    // Validate
    if (file.size > 10 * 1024 * 1024) {
      toast.error("File too large");
      continue;
    }
    
    // Upload
    const { data, error } = await api.uploadDocument(file);
    
    if (error) {
      toast.error(error);
      return;
    }
    
    // Add to state
    addDocument({
      id: data.document_id,
      filename: file.name,
      processed: false
    });
    
    // Poll for processing status
    pollProcessingStatus(data.document_id);
  }
};
```

**Backend API** (`backend/src/api/routes/documents.py`):
```python
@router.post("/upload")
async def upload_document(file: UploadFile):
    # 1. Save to Supabase Storage
    file_path = await storage.upload(
        bucket="documents",
        file=file
    )
    
    # 2. Create document record
    doc_id = str(uuid.uuid4())
    await db.table('documents').insert({
        'id': doc_id,
        'filename': file.filename,
        'file_size': file.size,
        'file_type': file.content_type,
        'storage_path': file_path,
        'processed': False
    })
    
    # 3. Queue for async processing
    await process_document_background(doc_id, file_path)
    
    return {
        "document_id": doc_id,
        "status": "processing"
    }
```

**Document Processing Pipeline** (`backend/src/rag/pipeline.py`):
```python
async def process_document(doc_id: str, file_path: str):
    """
    Complete document processing pipeline.
    
    Steps:
    1. Parse PDF → extract text, tables, metadata
    2. Smart chunking → structure-aware chunks
    3. Generate embeddings → batch API calls
    4. Store in database → chunks + vectors
    """
    
    # Step 1: Parse PDF
    parser = DocumentParser()
    parsed = parser.parse_pdf(file_path)
    # Output: ParsedDocument with text, tables, metadata
    
    # Step 2: Smart Chunking
    chunker = FinancialDocumentChunker(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = chunker.chunk_document(
        text=parsed.text,
        document_id=doc_id,
        metadata={'type': parsed.doc_type}
    )
    # Output: 127 chunks for Apple 10-K
    # Each chunk has: content, type, metadata, position
    
    # Step 3: Generate Embeddings (batched)
    embeddings_service = EmbeddingService()
    chunk_texts = [chunk.content for chunk in chunks]
    embeddings = await embeddings_service.embed_texts(chunk_texts)
    # API call to OpenAI: ~15 seconds, $0.17
    # Output: 127 vectors of 3072 dimensions each
    
    # Step 4: Store in Database
    for chunk, embedding in zip(chunks, embeddings):
        await db.table('document_chunks').insert({
            'document_id': doc_id,
            'content': chunk.content,
            'embedding': embedding,
            'metadata': {
                **chunk.metadata,
                'chunk_type': chunk.chunk_type,
                'position': chunk.position
            }
        })
    
    # Update document status
    await db.table('documents').update({
        'processed': True,
        'chunks_count': len(chunks)
    }).eq('id', doc_id)
    
    return {
        'success': True,
        'chunks_created': len(chunks)
    }
```

**Database State After Processing**:
```sql
-- documents table
+-------------------+------------+--------+
| filename          | processed  | chunks |
+-------------------+------------+--------+
| Apple_10K_2023    | true       | 127    |
| Microsoft_10K     | true       | 103    |
+-------------------+------------+--------+

-- document_chunks table (230 rows total)
+----------+--------------------------------+------------------+
| chunk_id | content                        | embedding        |
+----------+--------------------------------+------------------+
| chunk_1  | "Item 1. Business\n\nApple..." | [0.23, -0.11...] |
| chunk_2  | "Revenue\n\nTotal revenue..."  | [0.15, 0.08...]  |
| ...      | ...                            | ...              |
+----------+--------------------------------+------------------+
```

---

## 3. Simple Query - Factual Lookup

### What the User Sees

**User types**: "What was Apple's total revenue in 2023?"

**Step 1**: Query sent, agents working
```
┌─────────────────────────────────────────────────────────┐
│  💬 New Conversation                                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  👤 Sarah                                                │
│  What was Apple's total revenue in 2023?                │
│                                                          │
│  🤖 AI: Thinking...                                     │
│     🧭 Supervisor analyzing query...                    │
│     🔍 Research agent retrieving documents...           │
│     ✅ Fact checker validating...                       │
│     🔄 Synthesizing answer...                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Step 2**: Streaming response appears
```
│  🤖 AI Assistant                                         │
│  Apple's total revenue in fiscal year 2023 was          │
│  $383.9 billion [1], with net sales of...              │
│  ███                                                    │
```

**Step 3**: Complete answer with sources
```
┌─────────────────────────────────────────────────────────┐
│  👤 Sarah                                                │
│  What was Apple's total revenue in 2023?                │
│                                                          │
│  🤖 AI Assistant                                         │
│  Apple's total revenue in fiscal year 2023 was          │
│  **$383.9 billion** [1], with net sales of $383,285     │
│  million [2].                                            │
│                                                          │
│  Sources:                                                │
│  [1] Source 1  [2] Source 2                             │
│                                                          │
│  ⚡ View agent execution (4 steps, 2.3s)                │
└─────────────────────────────────────────────────────────┘
```

### Technical Implementation

**Frontend** (`frontend/src/components/ChatInterface.tsx`):
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  // Add user message
  const userMessage = {
    id: `msg_${Date.now()}`,
    role: 'user',
    content: input,
    timestamp: Date.now()
  };
  addMessage(currentConversationId, userMessage);
  
  // Create placeholder for assistant
  const assistantId = `msg_${Date.now() + 1}`;
  addMessage(currentConversationId, {
    id: assistantId,
    role: 'assistant',
    content: '',
    timestamp: Date.now()
  });
  
  // Stream response
  let fullContent = '';
  for await (const chunk of api.streamMessage(input)) {
    fullContent += chunk;
    setStreamingContent(fullContent);
    
    // Update message in real-time
    updateMessage(currentConversationId, assistantId, {
      content: fullContent
    });
  }
};
```

**Backend API** (`backend/src/api/routes/chat.py`):
```python
@router.post("/chat/stream")
async def chat_stream(query: str, conversation_id: str):
    """Streaming chat endpoint using Server-Sent Events."""
    
    async def generate():
        # Initialize agent system
        agent_graph = ResearchAgentGraph(db, llm, rag_pipeline)
        
        # Execute query
        async for event in agent_graph.astream(query):
            # Stream events back to frontend
            if event['type'] == 'agent_step':
                yield f"data: {json.dumps(event)}\n\n"
            elif event['type'] == 'content':
                yield f"data: {json.dumps({'content': event['content']})}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

**Agent System Execution** (`backend/src/agents/graph.py`):

**Phase 1: Supervisor Analyzes Query**
```python
# agents/nodes.py - supervisor_node()

async def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor analyzes query and determines routing.
    """
    query = state['query']  # "What was Apple's total revenue in 2023?"
    
    # Get available documents
    docs = await db.get_user_documents()
    # Returns: [Apple_10K_2023, Microsoft_10K_2023]
    
    # Analyze query with LLM
    analysis_prompt = f"""
    Analyze this query: "{query}"
    
    Available documents: {[d.filename for d in docs]}
    
    Determine:
    1. Strategy: research|analysis|web_search|multi_agent
    2. Complexity: 1-5
    3. Which documents are needed
    
    Return JSON.
    """
    
    decision = await llm.structured_output(analysis_prompt)
    # Returns: {
    #   "strategy": "research",
    #   "reasoning": "Simple factual lookup in Apple 10-K",
    #   "complexity": 1,
    #   "documents": ["Apple_10K_2023"]
    # }
    
    state['supervisor_analysis'] = decision
    state['agent_trace'].append({
        'agent': 'supervisor',
        'action': 'query_analysis',
        'result': decision,
        'duration': 0.4
    })
    
    return state
```

**Phase 2: Research Agent Retrieves & Generates**
```python
# agents/nodes.py - research_node()

async def research_node(state: AgentState) -> AgentState:
    """
    Research agent: RAG-based question answering.
    """
    query = state['query']
    
    # STEP 1: Retrieve relevant chunks
    retrieved = await rag_pipeline.retrieve(
        query=query,
        top_k=10,
        filters={'document_id': 'apple_10k_id'}
    )
    
    # Behind the scenes in rag_pipeline.retrieve():
    # ┌─────────────────────────────────────┐
    # │ 1. Generate query embedding         │
    # │    OpenAI API: embedding-3-large    │
    # │    Output: [0.15, -0.08, ...] (3072)│
    # │                                     │
    # │ 2. Vector search (pgvector)         │
    # │    SQL: SELECT ... ORDER BY         │
    # │         embedding <=> query_emb     │
    # │    Returns: 20 chunks               │
    # │                                     │
    # │ 3. Keyword search (full-text)       │
    # │    SQL: ts_rank(search_vector, ...) │
    # │    Returns: 20 chunks               │
    # │                                     │
    # │ 4. Reciprocal Rank Fusion           │
    # │    Combines both result sets        │
    # │    Formula: 1/(60+rank_v) +         │
    # │             1/(60+rank_k)           │
    # │    Returns: 20 fused chunks         │
    # │                                     │
    # │ 5. Rerank with Cohere               │
    # │    API call: rerank-english-v3.0    │
    # │    Returns: Top 10 chunks           │
    # └─────────────────────────────────────┘
    
    # Retrieved chunks:
    # [0] "Consolidated Statements of Operations...
    #      Net sales: $383,285 million (2023)..."
    # [1] "Item 8. Financial Data and Supplementary...
    #      Total net sales 2023: $383.9 billion..."
    # [2] "Revenue by segment: iPhone $200.6B, Mac $29.4B..."
    
    state['retrieved_docs'] = retrieved
    
    # STEP 2: Generate answer with citations
    context = "\n\n".join([
        f"[doc_{i}]\n{doc['content']}"
        for i, doc in enumerate(retrieved)
    ])
    
    answer_prompt = f"""
    Answer this question using ONLY the provided documents.
    
    Question: {query}
    
    Documents:
    {context}
    
    Requirements:
    - Cite every claim with [doc_X]
    - If info not in documents, say so
    - Be precise with numbers and dates
    - Quote directly when important
    
    Answer:
    """
    
    answer = await llm.generate(answer_prompt, model="gpt-4o")
    # Returns: "Apple's total revenue in fiscal year 2023 was 
    #           $383.9 billion [doc_1], with net sales of 
    #           $383,285 million [doc_0]."
    
    # Extract citations
    citations = extract_citations(answer, retrieved)
    # Returns: [
    #   {'chunk_id': 'chunk_42', 'text': '[doc_0]'},
    #   {'chunk_id': 'chunk_89', 'text': '[doc_1]'}
    # ]
    
    state['research_output'] = {
        'answer': answer,
        'sources': retrieved,
        'confidence': 0.95
    }
    state['citations'] = citations
    state['agent_trace'].append({
        'agent': 'research',
        'action': 'rag_query',
        'docs_retrieved': len(retrieved),
        'citations': len(citations),
        'duration': 1.2
    })
    
    return state
```

**Phase 3: Fact Checker Validates**
```python
# agents/nodes.py - fact_checker_node()

async def fact_checker_node(state: AgentState) -> AgentState:
    """
    Fact checker validates claims against sources.
    """
    answer = state['research_output']['answer']
    sources = state['retrieved_docs']
    
    # Extract claims from answer
    claims_prompt = f"""
    Extract specific factual claims from this answer:
    "{answer}"
    
    Return as JSON array of claims.
    """
    
    claims = await llm.structured_output(claims_prompt)
    # Returns: [
    #   "Apple's total revenue in fiscal year 2023 was $383.9 billion",
    #   "net sales of $383,285 million"
    # ]
    
    # Verify each claim
    verified_claims = []
    for claim in claims:
        # Check if claim appears in source documents
        verification = verify_claim_against_sources(claim, sources)
        # Returns: {
        #   'verified': True,
        #   'confidence': 0.95,
        #   'evidence': 'Found in doc_1: "Total net sales 2023: $383.9 billion"'
        # }
        verified_claims.append(verification)
    
    # All claims verified ✓
    state['fact_check_results'] = {
        'verified_claims': [c for c in verified_claims if c['verified']],
        'unverified_claims': [c for c in verified_claims if not c['verified']],
        'overall_confidence': 0.95
    }
    
    state['agent_trace'].append({
        'agent': 'fact_checker',
        'action': 'claim_verification',
        'claims_checked': len(claims),
        'verified': len([c for c in verified_claims if c['verified']]),
        'duration': 0.5
    })
    
    return state
```

**Phase 4: Synthesizer Creates Final Output**
```python
# agents/nodes.py - synthesizer_node()

async def synthesizer_node(state: AgentState) -> AgentState:
    """
    Synthesizer combines all agent outputs.
    """
    # Collect outputs
    research_answer = state['research_output']['answer']
    fact_check = state['fact_check_results']
    
    # In this simple case, research answer is already good
    # Just add confidence score from fact checker
    final_answer = research_answer
    
    state['final_answer'] = final_answer
    state['confidence_score'] = fact_check['overall_confidence']
    state['agent_trace'].append({
        'agent': 'synthesizer',
        'action': 'final_synthesis',
        'duration': 0.2
    })
    
    return state
```

**User Clicks "View Agent Execution"**:
```
┌─────────────────────────────────────────────────────────┐
│  Agent Execution Trace                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🧭 Supervisor (0.4s)                                   │
│  └─ Analyzed query → Routed to Research Agent          │
│     Strategy: Simple factual lookup                     │
│     Documents: Apple_10K_2023.pdf                       │
│                                                          │
│  🔍 Research Agent (1.2s)                               │
│  └─ Retrieved 10 relevant chunks                        │
│     • Vector search: 20 results                         │
│     • Keyword search: 20 results                        │
│     • RRF fusion + Cohere rerank → 10 final             │
│     Generated answer with 2 citations                   │
│                                                          │
│  ✅ Fact Checker (0.5s)                                 │
│  └─ Verified 2 claims                                   │
│     • Claim 1: "$383.9 billion" ✓ (confidence: 0.95)   │
│     • Claim 2: "$383,285 million" ✓ (confidence: 0.95) │
│     All claims supported by sources                     │
│                                                          │
│  🔄 Synthesizer (0.2s)                                  │
│  └─ Combined outputs into final answer                  │
│     Confidence: 95%                                     │
│                                                          │
│  ⚡ Total: 2.3 seconds | Cost: $0.05                    │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Complex Query - Comparative Analysis

### What the User Sees

**User types**: "Compare Apple and Microsoft's R&D spending as a percentage of revenue. Which company is investing more aggressively in innovation?"

```
┌─────────────────────────────────────────────────────────┐
│  🤖 AI Assistant                                         │
│                                                          │
│  Based on 2023 financial data:                          │
│                                                          │
│  **Apple:**                                              │
│  • R&D Spending: $29.9 billion [1]                      │
│  • Total Revenue: $383.9 billion [1]                    │
│  • R&D as % of Revenue: **7.8%**                        │
│                                                          │
│  **Microsoft:**                                          │
│  • R&D Spending: $27.2 billion [2]                      │
│  • Total Revenue: $211.9 billion [2]                    │
│  • R&D as % of Revenue: **12.8%**                       │
│                                                          │
│  **Analysis:**                                           │
│  Microsoft is investing more aggressively in innovation │
│  relative to their revenue, dedicating 12.8% compared   │
│  to Apple's 7.8%. This represents a 5 percentage point  │
│  difference. While Apple spends more in absolute        │
│  dollars ($29.9B vs $27.2B), Microsoft's higher         │
│  percentage suggests a stronger commitment to R&D       │
│  relative to their business size.                       │
│                                                          │
│  📊 [View Comparison Chart]                             │
│                                                          │
│  Sources: [1] Apple 10-K  [2] Microsoft 10-K            │
│                                                          │
│  ⚡ View agent execution (6 steps, 4.1s)                │
│     Tools used: Calculator (2x)                         │
└─────────────────────────────────────────────────────────┘
```

### Technical Implementation

**Supervisor Routes Differently**:
```python
# More complex query detected
decision = {
    "strategy": "multi_agent",
    "reasoning": "Requires multi-document comparison with calculations",
    "agents": ["research", "analysis", "fact_checker"],
    "complexity": 4
}
```

**Research Agent (Parallel Retrieval)**:
```python
# Retrieve from BOTH documents in parallel
apple_task = rag_pipeline.retrieve(
    "Apple R&D spending revenue 2023",
    filters={"document_id": "apple_10k_id"}
)

msft_task = rag_pipeline.retrieve(
    "Microsoft R&D spending revenue 2023",
    filters={"document_id": "msft_10k_id"}
)

apple_chunks, msft_chunks = await asyncio.gather(
    apple_task, msft_task
)

# Found data in both documents
# Apple: "R&D expenses: $29.9 billion... Revenue: $383.9 billion"
# MSFT: "Research and development: $27.2 billion... Revenue: $211.9 billion"
```

**Analysis Agent Uses Tools**:
```python
# agents/nodes.py - analysis_node()

# Agent has access to tools
from .tools import calculator, chart_generator

analysis_prompt = f"""
Task: Compare R&D spending as % of revenue

Apple: R&D $29.9B, Revenue $383.9B
Microsoft: R&D $27.2B, Revenue $211.9B

Use calculator tool to compute percentages.
Create comparison chart.
"""

# Agent calls tools
tool_results = []

# Call 1: Calculate Apple %
result1 = calculator("(29.9 / 383.9) * 100")
# Returns: "7.79"
tool_results.append({'tool': 'calculator', 'result': '7.79%'})

# Call 2: Calculate Microsoft %
result2 = calculator("(27.2 / 211.9) * 100")
# Returns: "12.84"
tool_results.append({'tool': 'calculator', 'result': '12.84%'})

# Call 3: Generate chart
chart_data = [
    {'company': 'Apple', 'percentage': 7.8},
    {'company': 'Microsoft', 'percentage': 12.8}
]
chart = chart_generator(chart_data, 'bar', 'R&D as % of Revenue')
# Returns: base64 encoded chart image

# Generate analysis combining data + calculations
analysis = await llm.generate(f"""
Create comparative analysis:
- Apple: 7.8% R&D/Revenue
- Microsoft: 12.8% R&D/Revenue
- Charts generated

Provide insights on which company invests more aggressively.
""")
```

**Agent Trace Shows Full Workflow**:
```
┌─────────────────────────────────────────────────────────┐
│  Agent Execution Trace                                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🧭 Supervisor (0.5s)                                   │
│  └─ Complex comparison detected                         │
│     Routed to: Research + Analysis + Fact Checker       │
│     Complexity: 4/5                                     │
│                                                          │
│  🔍 Research Agent (1.8s)                               │
│  └─ Retrieved from 2 documents in parallel              │
│     • Apple 10-K: 5 chunks (R&D, revenue data)          │
│     • Microsoft 10-K: 5 chunks (R&D, revenue data)      │
│     Total: 10 chunks retrieved                          │
│                                                          │
│  📊 Analysis Agent (1.3s)                               │
│  └─ Used tools:                                          │
│     [1] Calculator: (29.9/383.9)*100 = 7.79%            │
│     [2] Calculator: (27.2/211.9)*100 = 12.84%           │
│     [3] Chart Generator: Comparison bar chart           │
│     Generated comparative analysis with insights        │
│                                                          │
│  ✅ Fact Checker (0.3s)                                 │
│  └─ Verified 6 numerical claims:                        │
│     • Apple R&D: $29.9B ✓                               │
│     • Apple Revenue: $383.9B ✓                          │
│     • Microsoft R&D: $27.2B ✓                           │
│     • Microsoft Revenue: $211.9B ✓                      │
│     • Apple %: 7.8% ✓                                   │
│     • Microsoft %: 12.8% ✓                              │
│     All verified against sources                        │
│                                                          │
│  🔄 Synthesizer (0.2s)                                  │
│  └─ Combined analysis with insights                     │
│     Added interpretation and conclusion                 │
│                                                          │
│  ⚡ Total: 4.1 seconds | Cost: $0.08                    │
│     Tokens: 2,847 | Tools: 3                            │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Real-Time Query - Web Search Integration

### What the User Sees

**User types**: "How is Apple's stock performing today compared to their Q4 2023 earnings?"

```
┌─────────────────────────────────────────────────────────┐
│  🤖 AI Assistant                                         │
│                                                          │
│  **Current Performance (Live Data):**                   │
│  Apple stock (AAPL) is currently trading at **$195.42** │
│  [Web: Yahoo Finance], up 2.3% today.                   │
│                                                          │
│  **Q4 2