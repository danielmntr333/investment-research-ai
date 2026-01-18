"""Fallback logic for provider failures."""
import asyncio
from typing import List, Callable


class FallbackHandler:
    """Handle fallback between LLM providers."""
    
    def __init__(self, providers: List[str]):
        self.providers = providers
        self.current_provider_index = 0
    
    async def execute_with_fallback(self, func: Callable, *args, **kwargs):
        """Execute function with automatic fallback on failure."""
        for i, provider in enumerate(self.providers):
            try:
                result = await func(*args, model=provider, **kwargs)
                self.current_provider_index = i
                return result
            except Exception as e:
                if i == len(self.providers) - 1:
                    raise Exception(f"All providers failed. Last error: {e}")
                continue
