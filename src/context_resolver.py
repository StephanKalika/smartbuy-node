"""
Context Resolver: Hygiene & Sanitization Utility
Part of SmartBuy Node - Automated B2B Procurement & Compliance

This module provides context sanitization utilities:
1. PII (Personally Identifiable Information) scrubbing
2. Credential masking
3. Regex-based pattern replacement
4. Safe variable substitution

Prevents data leakage and prompt injection attacks.
"""

import re
from typing import Dict, Tuple, List


class ContextResolver:
    """Utility for context cleansing and safe variable substitution."""
    
    # Regex patterns for sensitive data
    PATTERNS = {
        "email": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        "api_key": r'(?:api_key|apikey|api-key)\s*[:=]\s*[a-zA-Z0-9_-]{20,}',
        "password": r'(?:password|pwd|passwd)\s*[:=]\s*[^\s]+',
        "token": r'(?:token|auth_token)\s*[:=]\s*[a-zA-Z0-9_-]{20,}',
        "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
    }
    
    @classmethod
    def scrub_pii(cls, text: str) -> Tuple[str, List[Dict]]:
        """
        Scrub personally identifiable information from text.
        
        Args:
            text: Input text to clean
            
        Returns:
            Tuple of (scrubbed_text, list of findings)
        """
        
        scrubbed = text
        findings = []
        
        for pii_type, pattern in cls.PATTERNS.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "match": match.group(0)[:20] + "...",  # Truncate
                    "position": (match.start(), match.end())
                })
                # Replace with placeholder
                scrubbed = scrubbed[:match.start()] + f"[[{pii_type.upper()}]]" + scrubbed[match.end():]
        
        return scrubbed, findings
    
    @classmethod
    def mask_credentials(cls, text: str) -> str:
        """
        Mask API keys, passwords, tokens.
        
        Args:
            text: Input text
            
        Returns:
            Text with credentials masked
        """
        
        # Mask API keys
        text = re.sub(
            r'(api[_-]?key|apikey)\s*[:=]\s*[a-zA-Z0-9_-]{20,}',
            r'\1 = [[REDACTED_API_KEY]]',
            text,
            flags=re.IGNORECASE
        )
        
        # Mask passwords
        text = re.sub(
            r'(password|pwd|passwd)\s*[:=]\s*[^\s]+',
            r'\1 = [[REDACTED_PASSWORD]]',
            text,
            flags=re.IGNORECASE
        )
        
        # Mask tokens
        text = re.sub(
            r'(token|auth_token|bearer)\s+[a-zA-Z0-9_-]{20,}',
            r'\1 [[REDACTED_TOKEN]]',
            text,
            flags=re.IGNORECASE
        )
        
        return text
    
    @classmethod
    def safe_substitute(cls, template: str, variables: Dict[str, str]) -> str:
        """
        Safely substitute variables into template, preventing injection.
        
        Args:
            template: Template with [[VAR_NAME]] placeholders
            variables: Dictionary of variable values
            
        Returns:
            Substituted string with values escaped
        """
        
        result = template
        
        for var_name, var_value in variables.items():
            placeholder = f"[[{var_name.upper()}]]"
            # Escape value to prevent injection
            escaped_value = cls._escape_value(var_value)
            result = result.replace(placeholder, escaped_value)
        
        return result
    
    @classmethod
    def _escape_value(cls, value: str) -> str:
        """
        Escape special characters in variable values.
        
        Args:
            value: Value to escape
            
        Returns:
            Escaped value safe for insertion
        """
        
        # Basic HTML/SQL escaping
        escape_map = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '&': '&amp;',
            ';': '&#59;',
            '(': '&#40;',
            ')': '&#41;',
        }
        
        for char, escaped in escape_map.items():
            value = value.replace(char, escaped)
        
        return value
    
    @classmethod
    def validate_input(cls, user_input: str, max_length: int = 5000) -> Tuple[bool, str]:
        """
        Validate user input for safety.
        
        Args:
            user_input: Input to validate
            max_length: Maximum allowed length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        if not user_input:
            return False, "Input cannot be empty"
        
        if len(user_input) > max_length:
            return False, f"Input exceeds maximum length of {max_length} characters"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*=',
            r'drop\s+table',
            r'delete\s+from',
            r'union\s+select',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, f"Input contains suspicious pattern"
        
        return True, ""


if __name__ == "__main__":
    # Demo: Context resolver functionality
    resolver = ContextResolver()
    
    # Example 1: PII scrubbing
    print("[Example] PII Scrubbing:")
    text_with_pii = "Contact John at john.doe@example.com or call 555-123-4567. SSN: 123-45-6789"
    scrubbed, findings = resolver.scrub_pii(text_with_pii)
    print(f"  Original: {text_with_pii}")
    print(f"  Scrubbed: {scrubbed}")
    print(f"  Findings: {len(findings)} PII elements detected")
    
    # Example 2: Credential masking
    print("\n[Example] Credential Masking:")
    text_with_creds = "API key: sk_live_abc123def456ghi789jkl Password: MySecret123"
    masked = resolver.mask_credentials(text_with_creds)
    print(f"  Original: {text_with_creds}")
    print(f"  Masked: {masked}")
    
    # Example 3: Safe substitution
    print("\n[Example] Safe Variable Substitution:")
    template = "Department [[DEPARTMENT]] needs [[QUANTITY]] [[PRODUCT]] for [[PURPOSE]]"
    variables = {
        "department": "IT",
        "quantity": "5",
        "product": "4K Monitors",
        "purpose": "developer workstations"
    }
    result = resolver.safe_substitute(template, variables)
    print(f"  Template: {template}")
    print(f"  Result: {result}")
    
    # Example 4: Input validation
    print("\n[Example] Input Validation:")
    test_inputs = [
        ("Buy 5 monitors", True),
        ("<script>alert('xss')</script>", False),
        ("' OR '1'='1", False),
        ("I need to purchase 10 keyboards for the engineering team", True),
    ]
    for user_input, expected in test_inputs:
        is_valid, error = resolver.validate_input(user_input)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} '{user_input[:40]}...' → Valid: {is_valid}")
