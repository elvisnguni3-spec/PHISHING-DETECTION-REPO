import re

class InputTypeDetector:
    """Auto-detect if input is URL or text"""
    
    def detect(self, input_str: str) -> str:
        input_str = input_str.strip()
        
        # Check for URL patterns
        url_patterns = [
            r'^https?://',
            r'^www\.',
            r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        ]
        
        for pattern in url_patterns:
            if re.match(pattern, input_str, re.IGNORECASE):
                return 'URL'
        
        # Check for common TLDs
        common_tlds = ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co']
        if any(tld in input_str.lower() for tld in common_tlds) and ' ' not in input_str:
            if '/' in input_str or '?' in input_str or '=' in input_str:
                return 'URL'
            if re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', input_str):
                return 'URL'
        
        return 'Text'