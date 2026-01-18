"""PII detection and redaction (optional feature)."""
import re


class PIIDetector:
    """Detect and redact personally identifiable information."""
    
    def detect(self, text: str) -> list:
        """Detect PII in text."""
        # To be implemented
        return []
    
    def redact(self, text: str) -> str:
        """Redact PII from text."""
        # Patterns for common PII
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        }
        
        redacted = text
        for pii_type, pattern in patterns.items():
            redacted = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', redacted)
        
        return redacted
