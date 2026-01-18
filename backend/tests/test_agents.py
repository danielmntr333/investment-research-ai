"""Tests for multi-agent system."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.graph import ResearchAgentGraph
from src.agents.state import AgentState
from src.agents.nodes import (
    supervisor_node,
    research_node,
    fact_checker_node,
    _extract_citations,
    _calculate_confidence
)
from src.agents.tools import calculator, financial_metrics


class TestTools:
    """Test tool implementations."""
    
    def test_calculator_basic(self):
        """Test basic calculator operations."""
        assert calculator("2 + 2") == "4"
        assert calculator("10 * 5") == "50"
        assert calculator("(100 + 50) / 2") == "75.0"
    
    def test_calculator_error(self):
        """Test calculator error handling."""
        result = calculator("invalid expression")
        assert "Error" in result
    
    def test_financial_metrics_profit_margin(self):
        """Test profit margin calculation."""
        result = financial_metrics(
            "profit_margin",
            {"net_income": 20, "revenue": 100}
        )
        assert "20.00%" in result
    
    def test_financial_metrics_pe_ratio(self):
        """Test P/E ratio calculation."""
        result = financial_metrics(
            "pe_ratio",
            {"price": 150, "earnings": 10}
        )
        assert "15.00" in result
    
    def test_financial_metrics_roe(self):
        """Test ROE calculation."""
        result = financial_metrics(
            "roe",
            {"net_income": 50, "equity": 500}
        )
        assert "10.00%" in result
    
    def test_financial_metrics_unknown(self):
        """Test unknown metric error."""
        result = financial_metrics("unknown_metric", {})
        assert "Error" in result


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_extract_citations(self):
        """Test citation extraction from answer."""
        answer = "Apple's revenue was $100B [doc_0:chunk_abc123]. Microsoft earned $80B [doc_1:chunk_def456]."
        documents = [
            {"document_id": "doc1", "content": "Apple revenue data..."},
            {"document_id": "doc2", "content": "Microsoft revenue data..."}
        ]
        
        citations = _extract_citations(answer, documents)
        assert len(citations) == 2
        assert citations[0]['doc_id'] == "doc1"
        assert citations[1]['doc_id'] == "doc2"
    
    def test_calculate_confidence_no_citations(self):
        """Test confidence with no citations."""
        answer = "Some answer without citations"
        confidence = _calculate_confidence(answer, [])
        assert confidence == 0.3
    
    def test_calculate_confidence_with_citations(self):
        """Test confidence with multiple citations."""
        answer = "Answer with [doc_0:chunk_abc] and [doc_1:chunk_def] and [doc_2:chunk_ghi]"
        confidence = _calculate_confidence(answer, [])
        assert confidence == 0.9


@pytest.mark.asyncio
class TestAgentNodes:
    """Test individual agent nodes."""
    
    async def test_supervisor_node_with_documents(self):
        """Test supervisor routing with available documents."""
        # Mock dependencies
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value='{"strategy": "research", "reasoning": "Query about documents", "needs_web_search": false, "complexity": 2, "estimated_steps": 2}')
        
        mock_db = Mock()
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"filename": "apple_10k.pdf", "document_type": "10-K"}]
        )
        
        state = {
            'query': "What was Apple's revenue?",
            'user_id': 'test_user',
            'agent_trace': [],
            'errors': []
        }
        
        result = await supervisor_node(state, mock_llm, mock_db)
        
        assert 'supervisor_analysis' in result
        assert result['supervisor_analysis']['strategy'] == 'research'
        assert len(result['agent_trace']) == 1
        assert result['agent_trace'][0]['agent'] == 'supervisor'
    
    async def test_supervisor_node_error_fallback(self):
        """Test supervisor fallback on error."""
        mock_llm = Mock()
        mock_llm.generate = Mock(side_effect=Exception("LLM error"))
        
        mock_db = Mock()
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(data=[])
        
        state = {
            'query': "Test query",
            'user_id': None,
            'agent_trace': [],
            'errors': []
        }
        
        result = await supervisor_node(state, mock_llm, mock_db)
        
        # Should fallback to research strategy
        assert result['supervisor_analysis']['strategy'] == 'research'
        assert len(result['errors']) > 0
    
    async def test_research_node(self):
        """Test research node with mocked RAG pipeline."""
        # Mock RAG pipeline
        mock_rag = Mock()
        mock_rag.query = Mock(return_value={
            'answer': 'Apple revenue was $100B [doc_0:chunk_abc].',
            'sources': [
                {'document_id': 'doc1', 'content': 'Apple annual report...', 'id': 'chunk_abc'}
            ]
        })
        
        mock_llm = Mock()
        
        state = {
            'query': "What was Apple's revenue?",
            'document_ids': [],
            'citations': [],
            'agent_trace': [],
            'errors': []
        }
        
        result = await research_node(state, mock_rag, mock_llm)
        
        assert 'research_output' in result
        assert 'answer' in result['research_output']
        assert len(result['retrieved_docs']) > 0
        assert len(result['agent_trace']) == 1
    
    async def test_fact_checker_node(self):
        """Test fact checker node."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value='[{"claim": "Apple revenue was $100B", "supported": true, "evidence": "Source text", "confidence": 0.9, "source_ids": ["doc_0:chunk_abc"]}]')
        
        state = {
            'query': 'test',
            'research_output': {
                'answer': 'Apple revenue was $100B [doc_0:chunk_abc].'
            },
            'retrieved_docs': [
                {'content': 'Apple annual report shows revenue of $100B...'}
            ],
            'agent_trace': [],
            'errors': []
        }
        
        result = await fact_checker_node(state, mock_llm)
        
        assert 'fact_check_results' in result
        assert 'verified_claims' in result['fact_check_results']
        assert 'overall_confidence' in result['fact_check_results']


@pytest.mark.asyncio
class TestAgentGraph:
    """Test full agent graph execution."""
    
    async def test_graph_initialization(self):
        """Test graph initialization."""
        mock_db = Mock()
        mock_llm = Mock()
        mock_rag = Mock()
        
        graph = ResearchAgentGraph(mock_db, mock_llm, mock_rag)
        
        assert graph.db == mock_db
        assert graph.llm == mock_llm
        assert graph.rag == mock_rag
        assert graph.app is not None
    
    @patch('src.agents.nodes.supervisor_node')
    @patch('src.agents.nodes.research_node')
    @patch('src.agents.nodes.fact_checker_node')
    @patch('src.agents.nodes.synthesizer_node')
    async def test_graph_execution_flow(
        self, 
        mock_synthesizer,
        mock_fact_checker,
        mock_research,
        mock_supervisor
    ):
        """Test complete graph execution flow."""
        # Setup mocks
        async def mock_supervisor_fn(state, llm, db):
            state['supervisor_analysis'] = {
                'strategy': 'research',
                'reasoning': 'Test',
                'needs_web_search': False,
                'complexity': 1,
                'estimated_steps': 1
            }
            state['agent_trace'].append({'agent': 'supervisor', 'action': 'routing', 'duration': 0.1})
            return state
        
        async def mock_research_fn(state, rag, llm):
            state['research_output'] = {
                'answer': 'Test answer',
                'sources': [],
                'confidence': 0.8
            }
            state['retrieved_docs'] = []
            state['agent_trace'].append({'agent': 'research', 'action': 'rag', 'duration': 0.2})
            return state
        
        async def mock_fact_checker_fn(state, llm):
            state['fact_check_results'] = {
                'verified_claims': [],
                'unverified_claims': [],
                'overall_confidence': 0.8
            }
            state['agent_trace'].append({'agent': 'fact_checker', 'action': 'verify', 'duration': 0.1})
            return state
        
        async def mock_synthesizer_fn(state, llm):
            state['final_answer'] = 'Final test answer'
            state['confidence_score'] = 0.8
            state['agent_trace'].append({'agent': 'synthesizer', 'action': 'synthesize', 'duration': 0.1})
            return state
        
        mock_supervisor.side_effect = mock_supervisor_fn
        mock_research.side_effect = mock_research_fn
        mock_fact_checker.side_effect = mock_fact_checker_fn
        mock_synthesizer.side_effect = mock_synthesizer_fn
        
        # Create graph
        mock_db = Mock()
        mock_llm = Mock()
        mock_rag = Mock()
        
        graph = ResearchAgentGraph(mock_db, mock_llm, mock_rag)
        
        # Execute
        result = await graph.arun(
            query="What is Apple's revenue?",
            user_id="test_user"
        )
        
        # Verify
        assert result['final_answer'] == 'Final test answer'
        assert len(result['agent_trace']) >= 3  # At least supervisor, research, synthesizer
        assert result['execution_time'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
