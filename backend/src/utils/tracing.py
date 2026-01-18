"""LangSmith integration for tracing."""
import os


def setup_tracing():
    """Configure LangSmith tracing."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "investment-research-ai")
    
    # API key should be set in environment variables
    if not os.getenv("LANGSMITH_API_KEY"):
        print("Warning: LANGSMITH_API_KEY not set. Tracing will be disabled.")


def trace_function(func_name: str):
    """Decorator for tracing functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # To be implemented with LangSmith
            return await func(*args, **kwargs)
        return wrapper
    return decorator
