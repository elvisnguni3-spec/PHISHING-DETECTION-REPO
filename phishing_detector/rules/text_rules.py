import re
from typing import Tuple, List


class TextRules:
    """Intensive text heuristic rules"""
    
    URGENCY = ['urgent', 'immediately', 'asap', 'action required', 'limited time', 'immediate']
    FINANCIAL = ['bank', 'account', 'payment', 'credit card', 'paypal', 'transfer', 'money', 'wire']
    SENSITIVE = ['password', 'ssn', 'verify identity', 'confirm details', 'login', 'credential']
    PRIZE = ['won', 'winner', 'prize', 'lottery', 'congratulations', 'free gift', 'claim']
    
    @staticmethod
    def analyze(text: str) -> Tuple[float, List[str]]:
        """Returns (score 0-100, reasons list)"""
        reasons = []
        score = 0
        text_lower = text.lower()
        
        # Urgency
        found = [kw for kw in TextRules.URGENCY if kw in text_lower]
        if found:
            score += 25
            reasons.append(f"Urgency tactics: {', '.join(found[:2])} (+25%)")
        
        # Financial
        found = [kw for kw in TextRules.FINANCIAL if kw in text_lower]
        if found:
            score += 20
            reasons.append(f"Financial terms: {', '.join(found[:2])} (+20%)")
        
        # Sensitive info requests
        found = [kw for kw in TextRules.SENSITIVE if kw in text_lower]
        if found:
            score += 35
            reasons.append(f"Requests sensitive info: {', '.join(found[:2])} (+35%)")
        
        # Prize scams
        found = [kw for kw in TextRules.PRIZE if kw in text_lower]
        if found:
            score += 30
            reasons.append(f"Prize/winner scam: {', '.join(found[:2])} (+30%)")
        
        # Links
        links = re.findall(r'https?://[^\s]+|www\.[^\s]+', text)
        if links:
            score += 20
            reasons.append(f"Contains {len(links)} link(s) (+20%)")
        
        # All caps
        uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if uppercase_ratio > 0.3:
            score += 15
            reasons.append(f"Excessive capitalization (+15%)")
        
        # Exclamation marks
        exc_count = text.count('!')
        if exc_count > 2:
            add = min(exc_count * 3, 15)
            score += add
            reasons.append(f"Multiple exclamations ({exc_count}) (+{add}%)")
        
        return min(score, 100), reasons