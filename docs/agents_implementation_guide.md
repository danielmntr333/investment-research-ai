# Multi-Agent System Implementation Guide

## Overview

This document provides detailed implementation specifications for the multi-agent system using LangGraph. Use this alongside `plan.md` for complete agent implementation.

**Location**: `backend/src/agents/`

**Files**:
- `graph.py` - Main LangGraph orchestration
- `nodes.py` - Individual agent node implementations
- `tools.py` - Tool implementations
- `prompts.py` - System prompts for each agent
- `state.py` - State definitions

---

## Agent State Definition

**File**: `backend/src/agents/state.py`

```python
from typing import TypedDict, List, Dict, Annotated, Literal
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """
    State passed between agent nodes.
    
    This is the complete context that flows through the graph.
    Each agent reads from and writes to this state.
    """
    
    # User input
    query: str
    chat_history: Annotated[List[Dict], add_messages]
    
    # Document context
    retrieved_docs: List[Dict]  # From RAG retrieval
    document_ids: List[str]  # Available documents
    
    # Agent outputs
    supervisor_analysis: Dict  # Supervisor's query analysis
    research_output: Dict  # Research agent results
    analysis_output: Dict  # Analysis agent results
    fact_check_results: Dict  # Fact checker results
    web_search_results: List[Dict]  # Web search results
    
    # Final output
    final_answer: str
    citations: List[Dict]
    confidence_score: float
    
    # Execution trace (for UI visualization)
    agent_trace: List[Dict]
    
    # Error handling
    errors: List[str]
    retry_count: int
    
    # Metadata
    total_tokens: int
    total_cost: float
    execution_time: float

# Helper for specific agent outputs
class SupervisorDecision(TypedDict):
    strategy: Literal["research", "analysis", "web_search", "multi_agent"]
    reasoning: str
    needs_web_search: bool
    complexity: int  # 1-5
    estimated_steps: int

class ResearchResult(TypedDict):
    answer: str
    sources: List[Dict]
    confidence: float

class AnalysisResult(TypedDict):
    answer: str
    calculations: List[Dict]
    charts: List[Dict]
    tools_used: List[str]

class FactCheckResult(TypedDict):
    verified_claims: List[Dict]
    unverified_claims: List[Dict]
    overall_confidence: float
```

---

## System Prompts

**File**: `backend/src/agents/prompts.py`

```python
# Version tracking for A/B testing
PROMPT_VERSION = "v1.0"

SUPERVISOR_PROMPT = """You are a supervisor agent that analyzes user queries and determines the best execution strategy.

Your job is to:
1. Understand the user's question and intent
2. Determine which agent(s) should handle it
3. Decide if external data (web search) is needed
4. Estimate complexity and execution steps

Available agents:
- RESEARCH: For factual questions answered by document retrieval (RAG)
- ANALYSIS: For comparative analysis, calculations, data manipulation
- WEB_SEARCH: For real-time/current information not in documents
- MULTI_AGENT: For complex queries needing multiple agents

Available documents: {document_list}

Analyze this query: "{query}"

Consider:
- Is this answerable from uploaded documents alone?
- Does it require calculations or comparisons?
- Does it need current/real-time data?
- How many steps will it take?

Return JSON:
{{
    "strategy": "research|analysis|web_search|multi_agent",
    "reasoning": "why you chose this strategy",
    "needs_web_search": true/false,
    "complexity": 1-5,
    "estimated_steps": number,
    "suggested_agents": ["agent1", "agent2"]
}}
"""

RESEARCH_AGENT_PROMPT = """You are a research agent specialized in answering questions using provided documents.

Your responsibilities:
1. Use retrieved documents to answer questions
2. Cite ALL sources with [doc_X:chunk_Y] format
3. Be precise with numbers, dates, and facts
4. If information is not in documents, say so explicitly
5. Quote directly when important for accuracy

CRITICAL RULES:
- Every factual claim MUST have a citation
- If you're uncertain, indicate confidence level
- Never make up information
- Preserve exact numbers and dates from sources

Retrieved Context:
{context}

Question: {query}

Provide a comprehensive answer with proper citations."""

ANALYSIS_AGENT_PROMPT = """You are an analysis agent specialized in comparative analysis and quantitative reasoning.

Your responsibilities:
1. Perform comparative analysis across multiple documents/companies
2. Extract and compare numerical data
3. Use tools for calculations and visualizations
4. Generate insights from data patterns

Available tools:
- calculator: For mathematical operations
- table_extractor: Extract structured data from documents
- chart_generator: Create visualizations
- financial_metrics: Calculate financial ratios

Context:
{context}

Question: {query}

Think step-by-step:
1. What data do I need to extract?
2. What calculations are required?
3. How should I present the results?
4. What insights can I derive?

Provide detailed analysis with supporting data."""

FACT_CHECKER_PROMPT = """You are a fact-checking agent that validates claims against source documents.

Your job:
1. Extract specific claims from the provided answer
2. Verify each claim against retrieved documents
3. Identify unsupported or contradictory claims
4. Assign confidence scores

For each claim, determine:
- Is it directly supported by a source? (high confidence)
- Is it implied but not stated? (medium confidence)
- Is it unsupported or contradictory? (low confidence / flag)

Answer to fact-check:
{answer}

Source documents:
{sources}

Return JSON list of claims:
[
    {{
        "claim": "the specific claim",
        "supported": true/false,
        "evidence": "quote from source or null",
        "confidence": 0.0-1.0,
        "source_ids": ["doc_X:chunk_Y"]
    }}
]
"""

WEB_SEARCH_AGENT_PROMPT = """You are a web search agent that finds current, real-time information.

Your job:
1. Formulate effective search queries
2. Search the web for relevant information
3. Synthesize findings
4. Cite web sources

Use web search when:
- Current stock prices, market data
- Recent news or events
- Real-time information
- Data not in uploaded documents

Query: {query}

Think:
1. What specific information do I need?
2. What are the best search queries?
3. How recent does the data need to be?

Search and provide findings with URLs."""

SYNTHESIZER_PROMPT = """You are a synthesizer agent that combines outputs from multiple agents into a coherent final answer.

Your job:
1. Review all agent outputs
2. Resolve any contradictions
3. Combine information logically
4. Maintain all citations
5. Produce a clear, comprehensive answer

Agent outputs:
{agent_outputs}

Original query: {query}

Create a final answer that:
- Answers the user's question completely
- Integrates all relevant information
- Preserves citations from all sources
- Highlights any uncertainties or caveats
- Is well-structured and readable

Final answer:"""
```

---

## LangGraph Orchestration

**File**: `backend/src/agents/graph.py`

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Literal
import asyncio

from .state import AgentState, SupervisorDecision
from .nodes import (
    supervisor_node,
    research_node,
    analysis_node,
    fact_checker_node,
    web_search_node,
    synthesizer_node
)
from .tools import get_tools

class ResearchAgentGraph:
    """
    Multi-agent orchestration system using LangGraph.
    
    Flow:
    User Query → Supervisor (routing) → Agent(s) → Fact Checker → Synthesizer → Final Answer
    """
    
    def __init__(self, supabase_client, llm_provider, rag_pipeline):
        self.db = supabase_client
        self.llm = llm_provider
        self.rag = rag_pipeline
        
        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Construct the agent execution graph."""
        
        # Initialize graph with state schema
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("supervisor", self._supervisor_wrapper)
        workflow.add_node("research", self._research_wrapper)
        workflow.add_node("analysis", self._analysis_wrapper)
        workflow.add_node("fact_checker", self._fact_checker_wrapper)
        workflow.add_node("web_search", self._web_search_wrapper)
        workflow.add_node("synthesizer", self._synthesizer_wrapper)
        
        # Define entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional routing from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_query,
            {
                "research": "research",
                "analysis": "analysis",
                "web_search": "web_search",
                "multi_agent": "research",  # Start multi-agent flow
            }
        )
        
        # Define edges between nodes
        workflow.add_edge("research", "fact_checker")
        workflow.add_edge("analysis", "fact_checker")
        workflow.add_edge("web_search", "research")  # Web search feeds into research
        workflow.add_edge("fact_checker", "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        return workflow
    
    def _route_query(self, state: AgentState) -> str:
        """
        Routing logic based on supervisor's decision.
        
        Returns the next node to execute.
        """
        decision = state.get("supervisor_analysis", {})
        strategy = decision.get("strategy", "research")
        
        return strategy
    
    # Node wrappers that inject dependencies
    async def _supervisor_wrapper(self, state: AgentState) -> AgentState:
        return await supervisor_node(state, self.llm, self.db)
    
    async def _research_wrapper(self, state: AgentState) -> AgentState:
        return await research_node(state, self.rag, self.llm)
    
    async def _analysis_wrapper(self, state: AgentState) -> AgentState:
        tools = get_tools()
        return await analysis_node(state, self.llm, tools)
    
    async def _fact_checker_wrapper(self, state: AgentState) -> AgentState:
        return await fact_checker_node(state, self.llm)
    
    async def _web_search_wrapper(self, state: AgentState) -> AgentState:
        return await web_search_node(state, self.llm)
    
    async def _synthesizer_wrapper(self, state: AgentState) -> AgentState:
        return await synthesizer_node(state, self.llm)
    
    async def arun(self, query: str, chat_history: List = None) -> Dict:
        """
        Execute the agent graph asynchronously.
        
        Args:
            query: User's question
            chat_history: Previous conversation messages
        
        Returns:
            Final state with answer and metadata
        """
        
        # Initialize state
        initial_state = AgentState(
            query=query,
            chat_history=chat_history or [],
            retrieved_docs=[],
            document_ids=[],
            supervisor_analysis={},
            research_output={},
            analysis_output={},
            fact_check_results={},
            web_search_results=[],
            final_answer="",
            citations=[],
            confidence_score=0.0,
            agent_trace=[],
            errors=[],
            retry_count=0,
            total_tokens=0,
            total_cost=0.0,
            execution_time=0.0
        )
        
        # Execute graph
        final_state = await self.app.ainvoke(initial_state)
        
        return final_state
    
    def visualize(self, output_path: str = "agent_graph.png"):
        """
        Generate a visualization of the agent graph.
        Useful for documentation.
        """
        from langchain.graphs import graph_to_graphviz
        
        graph_viz = graph_to_graphviz(self.graph)
        graph_viz.render(output_path, format='png', cleanup=True)
        print(f"Graph visualization saved to {output_path}")
```

---

## Agent Node Implementations

**File**: `backend/src/agents/nodes.py`

```python
from typing import Dict, List
import json
import time

from .state import AgentState, SupervisorDecision, ResearchResult, AnalysisResult
from .prompts import (
    SUPERVISOR_PROMPT,
    RESEARCH_AGENT_PROMPT,
    ANALYSIS_AGENT_PROMPT,
    FACT_CHECKER_PROMPT,
    WEB_SEARCH_AGENT_PROMPT,
    SYNTHESIZER_PROMPT
)

async def supervisor_node(
    state: AgentState, 
    llm, 
    db
) -> AgentState:
    """
    Supervisor agent: Analyzes query and determines routing strategy.
    """
    start_time = time.time()
    
    # Get list of available documents
    docs = await db.get_user_documents(state.get('user_id'))
    doc_list = [f"{d['filename']} ({d['document_type']})" for d in docs]
    
    # Format prompt
    prompt = SUPERVISOR_PROMPT.format(
        query=state['query'],
        document_list="\n".join(doc_list) if doc_list else "No documents uploaded"
    )
    
    # Call LLM for structured output
    response = await llm.structured_output(
        prompt,
        schema=SupervisorDecision,
        model="gpt-4o"
    )
    
    # Update state
    state['supervisor_analysis'] = response
    state['agent_trace'].append({
        'agent': 'supervisor',
        'action': 'query_analysis',
        'result': response,
        'timestamp': time.time(),
        'duration': time.time() - start_time
    })
    
    return state


async def research_node(
    state: AgentState,
    rag_pipeline,
    llm
) -> AgentState:
    """
    Research agent: RAG-based question answering.
    """
    start_time = time.time()
    query = state['query']
    
    # Retrieve relevant documents
    retrieved = await rag_pipeline.retrieve(
        query=query,
        top_k=10,
        filters={}  # Could filter by document_ids from state
    )
    
    state['retrieved_docs'] = retrieved
    
    # Format context
    context = "\n\n".join([
        f"[doc_{i}:chunk_{doc['id']}]\n{doc['content']}"
        for i, doc in enumerate(retrieved)
    ])
    
    # Generate answer
    prompt = RESEARCH_AGENT_PROMPT.format(
        query=query,
        context=context
    )
    
    answer = await llm.generate(prompt, model="gpt-4o")
    
    # Extract citations
    citations = _extract_citations(answer, retrieved)
    
    # Update state
    state['research_output'] = ResearchResult(
        answer=answer,
        sources=retrieved,
        confidence=_calculate_confidence(answer, retrieved)
    )
    state['citations'].extend(citations)
    state['agent_trace'].append({
        'agent': 'research',
        'action': 'rag_query',
        'docs_retrieved': len(retrieved),
        'citations_found': len(citations),
        'duration': time.time() - start_time
    })
    
    return state


async def analysis_node(
    state: AgentState,
    llm,
    tools: List
) -> AgentState:
    """
    Analysis agent: Comparative analysis with tool usage.
    """
    start_time = time.time()
    query = state['query']
    context = state.get('retrieved_docs', [])
    
    # Format context
    context_str = "\n\n".join([
        f"Document {i}: {doc['content']}"
        for i, doc in enumerate(context)
    ])
    
    # Analysis with tool access
    prompt = ANALYSIS_AGENT_PROMPT.format(
        query=query,
        context=context_str
    )
    
    # Create agent with tools
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    
    agent = create_tool_calling_agent(llm.get_langchain_llm(), tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # Execute
    result = await agent_executor.ainvoke({"input": query})
    
    # Update state
    state['analysis_output'] = AnalysisResult(
        answer=result['output'],
        calculations=[],  # Extract from tool calls
        charts=[],  # Extract chart data
        tools_used=[tool.name for tool in tools if tool.name in str(result)]
    )
    state['agent_trace'].append({
        'agent': 'analysis',
        'action': 'comparative_analysis',
        'tools_used': state['analysis_output']['tools_used'],
        'duration': time.time() - start_time
    })
    
    return state


async def fact_checker_node(
    state: AgentState,
    llm
) -> AgentState:
    """
    Fact checker: Validates claims against sources.
    """
    start_time = time.time()
    
    # Get answer to fact-check
    answer = state.get('research_output', {}).get('answer', '')
    if not answer:
        answer = state.get('analysis_output', {}).get('answer', '')
    
    sources = state.get('retrieved_docs', [])
    
    if not answer or not sources:
        # Nothing to fact-check
        state['fact_check_results'] = {'verified_claims': [], 'unverified_claims': []}
        return state
    
    # Format sources
    sources_str = "\n\n".join([
        f"Source {i}: {doc['content']}"
        for i, doc in enumerate(sources)
    ])
    
    # Fact-check prompt
    prompt = FACT_CHECKER_PROMPT.format(
        answer=answer,
        sources=sources_str
    )
    
    # Get structured output
    result = await llm.structured_output(prompt, model="gpt-4o")
    
    # Separate verified and unverified
    verified = [c for c in result if c['supported']]
    unverified = [c for c in result if not c['supported']]
    
    # Calculate overall confidence
    overall_confidence = (
        sum(c['confidence'] for c in verified) / len(result)
        if result else 0.0
    )
    
    # Update state
    state['fact_check_results'] = {
        'verified_claims': verified,
        'unverified_claims': unverified,
        'overall_confidence': overall_confidence
    }
    
    # Add warnings for unverified claims
    if unverified:
        state['errors'].append(
            f"Warning: {len(unverified)} claims could not be verified"
        )
    
    state['agent_trace'].append({
        'agent': 'fact_checker',
        'action': 'claim_verification',
        'claims_checked': len(result),
        'verified': len(verified),
        'unverified': len(unverified),
        'confidence': overall_confidence,
        'duration': time.time() - start_time
    })
    
    return state


async def web_search_node(
    state: AgentState,
    llm
) -> AgentState:
    """
    Web search agent: Fetches real-time external data.
    """
    start_time = time.time()
    query = state['query']
    
    # Use Tavily for web search
    from tavily import TavilyClient
    import os
    
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    # Search
    results = await tavily.search_async(
        query=query,
        max_results=5,
        search_depth="advanced"
    )
    
    # Format results
    search_results = [
        {
            'title': r['title'],
            'url': r['url'],
            'content': r['content'],
            'score': r.get('score', 0.0)
        }
        for r in results.get('results', [])
    ]
    
    # Update state
    state['web_search_results'] = search_results
    state['agent_trace'].append({
        'agent': 'web_search',
        'action': 'external_search',
        'results_found': len(search_results),
        'duration': time.time() - start_time
    })
    
    return state


async def synthesizer_node(
    state: AgentState,
    llm
) -> AgentState:
    """
    Synthesizer: Combines all agent outputs into final answer.
    """
    start_time = time.time()
    
    # Collect all outputs
    agent_outputs = {
        'research': state.get('research_output', {}),
        'analysis': state.get('analysis_output', {}),
        'fact_check': state.get('fact_check_results', {}),
        'web_search': state.get('web_search_results', [])
    }
    
    # Format for prompt
    outputs_str = json.dumps(agent_outputs, indent=2)
    
    # Synthesis prompt
    prompt = SYNTHESIZER_PROMPT.format(
        query=state['query'],
        agent_outputs=outputs_str
    )
    
    # Generate final answer
    final_answer = await llm.generate(prompt, model="gpt-4o")
    
    # Update state
    state['final_answer'] = final_answer
    state['confidence_score'] = state.get('fact_check_results', {}).get('overall_confidence', 0.8)
    state['agent_trace'].append({
        'agent': 'synthesizer',
        'action': 'final_synthesis',
        'duration': time.time() - start_time
    })
    
    return state


# Helper functions
def _extract_citations(answer: str, documents: List[Dict]) -> List[Dict]:
    """Extract citation markers from answer and link to documents."""
    import re
    
    citations = []
    pattern = r'\[doc_(\d+):chunk_([a-f0-9-]+)\]'
    
    for match in re.finditer(pattern, answer):
        doc_idx = int(match.group(1))
        chunk_id = match.group(2)
        
        if doc_idx < len(documents):
            citations.append({
                'doc_id': documents[doc_idx]['document_id'],
                'chunk_id': chunk_id,
                'content': documents[doc_idx]['content'][:200] + '...'
            })
    
    return citations


def _calculate_confidence(answer: str, sources: List[Dict]) -> float:
    """Calculate confidence score based on citations and source quality."""
    
    # Count citations
    import re
    citation_count = len(re.findall(r'\[doc_\d+:chunk_[a-f0-9-]+\]', answer))
    
    # Baseline confidence
    if citation_count == 0:
        return 0.3
    elif citation_count < 3:
        return 0.6
    else:
        return 0.9
```

---

## Tool Implementations

**File**: `backend/src/agents/tools.py`

```python
from langchain.tools import tool, StructuredTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import List, Optional
import ast
import operator

# Tool schemas
class CalculatorInput(BaseModel):
    expression: str = Field(description="Mathematical expression to evaluate, e.g., '(100 + 50) / 2'")

class TableExtractorInput(BaseModel):
    document_id: str = Field(description="ID of the document to extract table from")
    page_number: Optional[int] = Field(None, description="Specific page number (if known)")

class ChartGeneratorInput(BaseModel):
    data: List[dict] = Field(description="Data to plot as list of dicts")
    chart_type: str = Field(description="Type of chart: 'bar', 'line', 'pie'")
    title: str = Field(description="Chart title")

# Tool implementations
@tool("calculator", args_schema=CalculatorInput, return_direct=False)
def calculator(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.
    
    Examples:
    - "(1000 + 500) / 2" -> "750.0"
    - "0.15 * 10000" -> "1500.0"
    """
    
    # Safe operators
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(f"Unsupported type {type(node)}")
    
    try:
        tree = ast.parse(expression, mode='eval')
        result = _eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool("table_extractor", args_schema=TableExtractorInput, return_direct=False)
async def table_extractor(document_id: str, page_number: Optional[int] = None) -> str:
    """
    Extract tables from a document.
    
    Returns structured table data as JSON string.
    """
    
    # This would integrate with your document processing
    # For now, a stub implementation
    
    try:
        # Fetch document
        from src.db.supabase import get_supabase_client
        db = get_supabase_client()
        
        doc = await db.get_document(document_id)
        if not doc:
            return f"Error: Document {document_id} not found"
        
        # Extract tables using pdfplumber or similar
        import pdfplumber
        
        with pdfplumber.open(doc['storage_path']) as pdf:
            tables = []
            pages = [pdf.pages[page_number]] if page_number else pdf.pages
            
            for page in pages:
                page_tables = page.extract_tables()
                for table in page_tables:
                    # Convert to dict format
                    if table and len(table) > 1:
                        headers = table[0]
                        rows = table[1:]
                        table_dict = [
                            dict(zip(headers, row)) for row in rows
                        ]
                        tables.append(table_dict)
            
            return json.dumps(tables, indent=2)
    
    except Exception as e:
        return f"Error extracting tables: {str(e)}"


@tool("chart_generator", args_schema=ChartGeneratorInput, return_direct=False)
def chart_generator(data: List[dict], chart_type: str, title: str) -> str:
    """
    Generate a chart from data and return as base64 image.
    
    Returns: Base64-encoded PNG image
    """
    
    import matplotlib.pyplot as plt
    import io
    import base64
    
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == 'bar':
            keys = [d.get('label', d.get('name', str(i))) for i, d in enumerate(data)]
            values = [d.get('value', 0) for d in data]
            ax.bar(keys, values)
        
        elif chart_type == 'line':
            keys = [d.get('label', d.get('name', str(i))) for i, d in enumerate(data)]
            values = [d.get('value', 0) for d in data]
            ax.plot(keys, values, marker='o')
        
        elif chart_type == 'pie':
            labels = [d.get('label', d.get('name', str(i))) for i, d in enumerate(data)]
            values = [d.get('value', 0) for d in data]
            ax.pie(values, labels=labels, autopct='%1.1f%%')
        
        else:
            return f"Error: Unsupported chart type '{chart_type}'"
        
        ax.set_title(title)
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    except Exception as e:
        return f"Error generating chart: {str(e)}"


@tool("financial_metrics")
def financial_metrics(metric: str, values: dict) -> str:
    """
    Calculate common financial metrics.
    
    Supported metrics:
    - pe_ratio: P/E ratio (price, earnings)
    - profit_margin: (net_income, revenue)
    - roe: Return on Equity (net_income, equity)
    - debt_to_equity: (total_debt, total_equity)
    - current_ratio: (current_assets, current_liabilities)
    
    Args:
        metric: Name of metric to calculate
        values: Dict with required values
    
    Returns:
        Calculated metric as string
    """
    
    try:
        if metric == 'pe_ratio':
            price = values.get('price', 0)
            earnings = values.get('earnings', 0)
            if earnings == 0:
                return "Error: Earnings cannot be zero"
            return f"P/E Ratio: {price / earnings:.2f}"
        
        elif metric == 'profit_margin':
            net_income = values.get('net_income', 0)
            revenue = values.get('revenue', 0)
            if revenue == 0:
                return "Error: Revenue cannot be zero"
            margin = (net_income / revenue) * 100
            return f"Profit Margin: {margin:.2f}%"
        
        elif metric == 'roe':
            net_income = values.get('net_income', 0)
            equity = values.get('equity', 0)
            if equity == 0:
                return "Error: Equity cannot be zero"
            roe = (net_income / equity) * 100
            return f"Return on Equity: {roe:.2f}%"
        
        elif metric == 'debt_to_equity':
            debt = values.get('total_debt', 0)
            equity = values.get('total_equity', 0)
            if equity == 0:
                return "Error: Equity cannot be zero"
            ratio = debt / equity
            return f"Debt-to-Equity Ratio: {ratio:.2f}"
        
        elif metric == 'current_ratio':
            assets = values.get('current_assets', 0)
            liabilities = values.get('current_liabilities', 0)
            if liabilities == 0:
                return "Error: Liabilities cannot be zero"
            ratio = assets / liabilities
            return f"Current Ratio: {ratio:.2f}"
        
        else:
            return f"Error: Unknown metric '{metric}'"
    
    except Exception as e:
        return f"Error calculating {metric}: {str(e)}"


def get_tools() -> List:
    """Return list of all available tools."""
    return [
        calculator,
        table_extractor,
        chart_generator,
        financial_metrics
    ]
```

---

## Usage Example

**How to use the agent system:**

```python
# In your FastAPI endpoint
from src.agents.graph import ResearchAgentGraph
from src.db.supabase import get_supabase_client
from src.llm.provider import LLMProvider
from src.rag.pipeline import RAGPipeline

# Initialize
db = get_supabase_client()
llm = LLMProvider()
rag = RAGPipeline(db, llm)

# Create agent graph
agent_graph = ResearchAgentGraph(db, llm, rag)

# Run query
result = await agent_graph.arun(
    query="Compare Apple and Microsoft's R&D spending",
    chat_history=[]
)

# Result contains:
{
    "final_answer": "...",
    "citations": [...],
    "confidence_score": 0.87,
    "agent_trace": [
        {"agent": "supervisor", "action": "query_analysis", ...},
        {"agent": "research", "action": "rag_query", ...},
        {"agent": "fact_checker", "action": "claim_verification", ...},
        {"agent": "synthesizer", "action": "final_synthesis", ...}
    ],
    "total_tokens": 5432,
    "total_cost": 0.12,
    "execution_time": 4.3
}
```

---

## Testing the Agent System

**File**: `backend/tests/test_agents.py`

```python
import pytest
from src.agents.graph import ResearchAgentGraph
from src.agents.state import AgentState

@pytest.mark.asyncio
async def test_supervisor_routing():
    """Test supervisor routes queries correctly."""
    
    # Mock dependencies
    mock_db = MockSupabaseClient()
    mock_llm = MockLLMProvider()
    mock_rag = MockRAGPipeline()
    
    graph = ResearchAgentGraph(mock_db, mock_llm, mock_rag)
    
    # Test simple factual query
    result = await graph.arun("What was Apple's revenue in Q3?")
    assert "research" in [step['agent'] for step in result['agent_trace']]
    
    # Test comparative query
    result = await graph.arun("Compare Apple and Microsoft")
    assert "analysis" in [step['agent'] for step in result['agent_trace']]
    
    # Test current data query
    result = await graph.arun("What is Tesla's stock price today?")
    assert "web_search" in [step['agent'] for step in result['agent_trace']]


@pytest.mark.asyncio
async def test_fact_checker():
    """Test fact checker identifies unsupported claims."""
    
    state = AgentState(
        query="test",
        research_output={
            "answer": "Apple's revenue was $100B [doc_1]. Microsoft invented the iPhone.",
            "sources": [{"id": "1", "content": "Apple revenue: $100B"}]
        },
        retrieved_docs=[{"id": "1", "content": "Apple revenue: $100B"}]
    )
    
    mock_llm = MockLLMProvider()
    result = await fact_checker_node(state, mock_llm)
    
    # Should flag "Microsoft invented iPhone" as unsupported
    assert len(result['fact_check_results']['unverified_claims']) > 0


@pytest.mark.asyncio
async def test_tool_usage():
    """Test analysis agent uses tools correctly."""
    
    from src.agents.tools import calculator, financial_metrics
    
    # Test calculator
    result = calculator("(100 + 50) / 2")
    assert result == "75.0"
    
    # Test financial metrics
    result = financial_metrics("profit_margin", {
        "net_income": 20,
        "revenue": 100
    })
    assert "20.00%" in result
```

---

## Agent Visualization in UI

**Frontend component to show agent execution:**

```typescript
// src/components/AgentTrace.tsx

interface AgentStep {
  agent: string;
  action: string;
  result?: any;
  timestamp: number;
  duration: number;
}

export function AgentTrace({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Agent Execution Trace</h3>
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
        
        {steps.map((step, i) => (
          <div key={i} className="relative pl-12 pb-8">
            {/* Agent icon */}
            <div className="absolute left-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
              {getAgentIcon(step.agent)}
            </div>
            
            {/* Step details */}
            <div className="bg-white border rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium">{step.agent}</h4>
                  <p className="text-sm text-gray-600">{step.action}</p>
                </div>
                <span className="text-xs text-gray-500">
                  {step.duration.toFixed(2)}s
                </span>
              </div>
              
              {/* Result preview */}
              {step.result && (
                <div className="mt-2 text-sm">
                  {renderResult(step.result)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getAgentIcon(agent: string) {
  const icons = {
    supervisor: '🧭',
    research: '🔍',
    analysis: '📊',
    fact_checker: '✅',
    web_search: '🌐',
    synthesizer: '🔄'
  };
  return icons[agent] || '🤖';
}
```

---

## Prompt Versioning & A/B Testing

**Track prompt performance:**

```python
# backend/src/agents/prompt_registry.py

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PromptVersion:
    name: str
    version: str
    template: str
    active: bool
    performance_metrics: Dict

class PromptRegistry:
    """
    Manage prompt versions and A/B testing.
    """
    
    def __init__(self, db):
        self.db = db
        self._cache = {}
    
    async def get_prompt(self, name: str, version: str = None) -> str:
        """
        Get prompt template by name and version.
        If version not specified, returns active version.
        """
        
        if version:
            key = f"{name}:{version}"
        else:
            # Get active version
            result = await self.db.get_active_prompt(name)
            return result['template']
        
        # Check cache
        if key in self._cache:
            return self._cache[key]
        
        # Fetch from DB
        result = await self.db.get_prompt_version(name, version)
        self._cache[key] = result['template']
        
        return result['template']
    
    async def create_version(
        self, 
        name: str, 
        template: str,
        version: str,
        set_active: bool = False
    ):
        """Create new prompt version."""
        
        await self.db.insert_prompt_version({
            'name': name,
            'version': version,
            'template': template,
            'active': set_active
        })
        
        if set_active:
            await self.db.set_active_prompt(name, version)
    
    async def ab_test(
        self,
        name: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5
    ):
        """
        Run A/B test between two prompt versions.
        
        Args:
            traffic_split: % of traffic to version_a (0.0-1.0)
        """
        
        import random
        
        if random.random() < traffic_split:
            return await self.get_prompt(name, version_a)
        else:
            return await self.get_prompt(name, version_b)
```

---

## Advanced: Parallel Agent Execution

**Run multiple agents in parallel when they don't depend on each other:**

```python
# In graph.py

async def _parallel_execution(self, state: AgentState) -> AgentState:
    """
    Execute multiple agents in parallel for better performance.
    
    Example: Research agent and Web search can run simultaneously
    """
    
    import asyncio
    
    # Run research and web search in parallel
    research_task = self._research_wrapper(state)
    web_search_task = self._web_search_wrapper(state)
    
    # Wait for both to complete
    research_state, web_search_state = await asyncio.gather(
        research_task,
        web_search_task
    )
    
    # Merge states
    state['research_output'] = research_state['research_output']
    state['web_search_results'] = web_search_state['web_search_results']
    state['agent_trace'].extend(research_state['agent_trace'])
    state['agent_trace'].extend(web_search_state['agent_trace'])
    
    return state
```

---

## Key Points for Implementation

### 1. Start Simple
```
Phase 1: Just supervisor + research agent
Phase 2: Add analysis agent
Phase 3: Add fact checker
Phase 4: Add web search + synthesizer
```

### 2. Test Each Agent Independently
```python
# Test research agent alone
from src.agents.nodes import research_node

state = {"query": "What is Apple's revenue?", ...}
result = await research_node(state, rag, llm)
assert result['research_output']['answer']
```

### 3. Use LangSmith for Debugging
```python
from langsmith import traceable

@traceable(name="research_agent")
async def research_node(state, rag, llm):
    # LangSmith will automatically trace this
    ...
```

### 4. Monitor Token Usage
```python
# Track in agent_trace
state['agent_trace'].append({
    'agent': 'research',
    'tokens_used': response.usage.total_tokens,
    'cost': calculate_cost(response.usage)
})
```

---

## Example Cursor Prompts

**To generate code from this document:**

```
@agents-implementation.md Generate the complete supervisor_node function with error handling and token tracking

@agents-implementation.md Implement the calculator tool with comprehensive tests

@agents-implementation.md Create the AgentTrace React component exactly as specified

@agents-implementation.md Build the complete LangGraph with all nodes and edges as shown
```

---

## Summary

This document provides:
- ✅ Complete agent state definitions
- ✅ All system prompts for each agent
- ✅ Full LangGraph orchestration code
- ✅ Detailed node implementations
- ✅ All tool implementations (calculator, table extractor, chart generator, financial metrics)
- ✅ Testing examples
- ✅ UI visualization component
- ✅ Prompt versioning system
- ✅ Parallel execution pattern

**With `plan.md` + `agents-implementation.md`, Claude in Cursor has everything needed to generate production-ready agent code!**