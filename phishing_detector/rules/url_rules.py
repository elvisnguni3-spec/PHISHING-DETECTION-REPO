import re
from urllib.parse import urlparse
from typing import Tuple, List


class URLRules:
    """Intensive URL heuristic rules"""
    
    SUSPICIOUS_KEYWORDS = [
        'login', 'verify', 'update', 'secure', 'account', 'signin', 
        'confirm', 'banking', 'paypal', 'amazon', 'apple', 'microsoft',
        'password', 'credential', 'authenticate', 'validation', 'security',
        'bank', 'alert', 'warning', 'identity', 'reset', 'billing'
    ]
    
    @staticmethod
    def analyze(url: str) -> Tuple[float, List[str]]:
        """Returns (score 0-100, reasons list)"""
        reasons = []
        score = 0
        
        # IP address
        if re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', url):
            score += 45
            reasons.append("IP address instead of domain (+45%)")
        
        # URL length
        if len(url) > 100:
            score += 25
            reasons.append(f"Very long URL ({len(url)} chars) (+25%)")
        elif len(url) > 75:
            score += 15
            reasons.append(f"Long URL ({len(url)} chars) (+15%)")
        
        # Suspicious keywords
        found = [kw for kw in URLRules.SUSPICIOUS_KEYWORDS if kw in url.lower()]
        if found:
            add = min(len(found) * 8, 30)
            score += add
            reasons.append(f"Suspicious keywords: {', '.join(found[:3])} (+{add}%)")
        
        # HTTP (insecure)
        if url.startswith("http://"):
            score += 20
            reasons.append("Uses HTTP (insecure) (+20%)")
        
        # Gibberish domain
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            domain = re.sub(r'^www\.', '', domain)
            letters = [c for c in domain if c.isalpha()]
            if letters:
                consonants = sum(1 for c in letters if c.lower() not in 'aeiou')
                if consonants / len(letters) > 0.7:
                    score += 30
                    reasons.append("Gibberish/random domain (+30%)")
        except:
            pass
        
        # Excessive subdomains
        if url.count('.') > 4:
            score += 15
            reasons.append("Excessive subdomains (+15%)")
        
        # URL encoding
        if '%' in url or '\\' in url:
            score += 20
            reasons.append("Contains encoded characters (+20%)")
        
        return min(score, 100), reasons