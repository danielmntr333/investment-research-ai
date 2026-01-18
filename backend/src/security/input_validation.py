"""Input validation and prompt injection defense."""
import re


def validate_input(user_input: str) -> str:
    """
    Validate and sanitize user input.
    
    Checks:
    - Length limits
    - Suspicious patterns
    - Injection attempts
    
    Raises:
        ValueError if input is invalid
    """
    # Check length
    if len(user_input) > 10000:
        raise ValueError("Input too long (max 10,000 characters)")
    
    # Check for injection patterns
    injection_patterns = [
        r"ignore previous instructions",
        r"system prompt",
        r"you are now",
        r"disregard all",
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            raise ValueError("Suspicious input detected")
    
    return user_input


def sanitize_output(output: str) -> str:
    """Sanitize LLM output before returning to user."""
    # To be implemented
    return output
