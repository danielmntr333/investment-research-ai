"""Tool implementations for agents."""
from langchain.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional, Dict, Any
import ast
import operator
import json


# Tool schemas
class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""
    expression: str = Field(description="Mathematical expression to evaluate, e.g., '(100 + 50) / 2'")


class TableExtractorInput(BaseModel):
    """Input schema for table extractor tool."""
    document_id: str = Field(description="ID of the document to extract table from")
    page_number: Optional[int] = Field(None, description="Specific page number (if known)")


class ChartGeneratorInput(BaseModel):
    """Input schema for chart generator tool."""
    data: List[dict] = Field(description="Data to plot as list of dicts with 'label' and 'value' keys")
    chart_type: str = Field(description="Type of chart: 'bar', 'line', 'pie'")
    title: str = Field(description="Chart title")


class FinancialMetricsInput(BaseModel):
    """Input schema for financial metrics tool."""
    metric: str = Field(description="Metric to calculate: 'pe_ratio', 'profit_margin', 'roe', 'debt_to_equity', 'current_ratio'")
    values: Dict[str, float] = Field(description="Dict with required values for the metric")


# Tool implementations
@tool("calculator", args_schema=CalculatorInput, return_direct=False)
def calculator(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.
    
    Examples:
    - "(1000 + 500) / 2" -> "750.0"
    - "0.15 * 10000" -> "1500.0"
    - "100 ** 2" -> "10000.0"
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
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Fallback for older Python
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
    
    try:
        # Import here to avoid circular imports
        from src.db.supabase import get_supabase
        
        db = get_supabase()
        
        # Get document metadata
        result = db.table('documents').select('*').eq('id', document_id).execute()
        if not result.data:
            return f"Error: Document {document_id} not found"
        
        doc = result.data[0]
        storage_path = doc.get('storage_path')
        
        if not storage_path:
            return f"Error: No storage path found for document {document_id}"
        
        # Extract tables using pdfplumber
        import pdfplumber
        
        # Download file from Supabase storage if needed
        # For now, assume local storage path
        with pdfplumber.open(storage_path) as pdf:
            tables = []
            pages = [pdf.pages[page_number]] if page_number and page_number < len(pdf.pages) else pdf.pages
            
            for page_idx, page in enumerate(pages):
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    # Convert to dict format
                    if table and len(table) > 1:
                        headers = table[0]
                        rows = table[1:]
                        table_dict = {
                            'page': page_number if page_number else page_idx + 1,
                            'table_index': table_idx,
                            'headers': headers,
                            'rows': rows,
                            'data': [dict(zip(headers, row)) for row in rows]
                        }
                        tables.append(table_dict)
            
            if not tables:
                return "No tables found in the document"
            
            return json.dumps(tables, indent=2)
    
    except Exception as e:
        return f"Error extracting tables: {str(e)}"


@tool("chart_generator", args_schema=ChartGeneratorInput, return_direct=False)
def chart_generator(data: List[dict], chart_type: str, title: str) -> str:
    """
    Generate a chart from data and return as base64 image.
    
    Returns: Base64-encoded PNG image with data URL prefix
    """
    
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import io
    import base64
    
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == 'bar':
            keys = [d.get('label', d.get('name', str(i))) for i, d in enumerate(data)]
            values = [float(d.get('value', 0)) for d in data]
            ax.bar(keys, values)
            plt.xticks(rotation=45, ha='right')
        
        elif chart_type == 'line':
            keys = [d.get('label', d.get('name', str(i))) for i, d in enumerate(data)]
            values = [float(d.get('value', 0)) for d in data]
            ax.plot(keys, values, marker='o')
            plt.xticks(rotation=45, ha='right')
        
        elif chart_type == 'pie':
            labels = [d.get('label', d.get('name', str(i))) for i, d in enumerate(data)]
            values = [float(d.get('value', 0)) for d in data]
            ax.pie(values, labels=labels, autopct='%1.1f%%')
        
        else:
            plt.close()
            return f"Error: Unsupported chart type '{chart_type}'. Use 'bar', 'line', or 'pie'."
        
        ax.set_title(title)
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    except Exception as e:
        plt.close()
        return f"Error generating chart: {str(e)}"


@tool("financial_metrics", args_schema=FinancialMetricsInput, return_direct=False)
def financial_metrics(metric: str, values: dict) -> str:
    """
    Calculate common financial metrics.
    
    Supported metrics:
    - pe_ratio: P/E ratio (requires: price, earnings)
    - profit_margin: Profit margin % (requires: net_income, revenue)
    - roe: Return on Equity % (requires: net_income, equity)
    - debt_to_equity: Debt-to-Equity ratio (requires: total_debt, total_equity)
    - current_ratio: Current ratio (requires: current_assets, current_liabilities)
    
    Args:
        metric: Name of metric to calculate
        values: Dict with required values
    
    Returns:
        Calculated metric as string
    """
    
    try:
        if metric == 'pe_ratio':
            price = float(values.get('price', 0))
            earnings = float(values.get('earnings', 0))
            if earnings == 0:
                return "Error: Earnings cannot be zero"
            ratio = price / earnings
            return f"P/E Ratio: {ratio:.2f}"
        
        elif metric == 'profit_margin':
            net_income = float(values.get('net_income', 0))
            revenue = float(values.get('revenue', 0))
            if revenue == 0:
                return "Error: Revenue cannot be zero"
            margin = (net_income / revenue) * 100
            return f"Profit Margin: {margin:.2f}%"
        
        elif metric == 'roe':
            net_income = float(values.get('net_income', 0))
            equity = float(values.get('equity', 0))
            if equity == 0:
                return "Error: Equity cannot be zero"
            roe = (net_income / equity) * 100
            return f"Return on Equity: {roe:.2f}%"
        
        elif metric == 'debt_to_equity':
            debt = float(values.get('total_debt', 0))
            equity = float(values.get('total_equity', 0))
            if equity == 0:
                return "Error: Equity cannot be zero"
            ratio = debt / equity
            return f"Debt-to-Equity Ratio: {ratio:.2f}"
        
        elif metric == 'current_ratio':
            assets = float(values.get('current_assets', 0))
            liabilities = float(values.get('current_liabilities', 0))
            if liabilities == 0:
                return "Error: Liabilities cannot be zero"
            ratio = assets / liabilities
            return f"Current Ratio: {ratio:.2f}"
        
        else:
            return f"Error: Unknown metric '{metric}'. Supported: pe_ratio, profit_margin, roe, debt_to_equity, current_ratio"
    
    except Exception as e:
        return f"Error calculating {metric}: {str(e)}"


def get_tools() -> List:
    """Return list of all available tools for agent use."""
    return [
        calculator,
        table_extractor,
        chart_generator,
        financial_metrics
    ]
