from core.models import AnalysisResult, Verdict
from rules.text_rules import TextRules
from ai.text_ai import TextAI


class TextDetector:
    """Combines Rules + AI for text analysis"""
    
    def __init__(self):
        self.rules = TextRules()
        self.ai = TextAI()
    
    def analyze(self, text: str) -> AnalysisResult:
        reasons = []
        
        print(f"\nAnalyzing Text: {text[:50]}...")
        print("-" * 40)
        
        # 1. RULES
        print("Running heuristic rules...")
        rule_score, rule_reasons = self.rules.analyze(text)
        reasons.extend(rule_reasons)
        
        # 2. AI
        print("Running AI analysis...")
        ai_score, ai_reasons = self.ai.analyze(text)
        reasons.extend(ai_reasons)
        
        # CALCULATE AVERAGE
        scores = [rule_score, ai_score]
        final_score = sum(scores) / len(scores)
        
        reasons.append(f"\nSCORE BREAKDOWN:")
        reasons.append(f"   Heuristic Rules: {rule_score:.0f}%")
        reasons.append(f"   AI Model: {ai_score:.0f}%")
        reasons.append(f"   ───────────────────")
        reasons.append(f"   FINAL SCORE: {final_score:.0f}%")
        
        print(f"\n   Final score: {final_score:.0f}%")
        
        # DETERMINE VERDICT
        if final_score >= 60:
            verdict = Verdict.SCAM
            confidence = min(0.95, final_score / 100)
        elif final_score >= 30:
            verdict = Verdict.SUSPICIOUS
            confidence = final_score / 100
        else:
            verdict = Verdict.SAFE
            confidence = 1 - (final_score / 100)
        
        return AnalysisResult(
            input_type="Text",
            original_input=text,
            verdict=verdict,
            confidence=confidence,
            reasons=reasons,
            rule_score=rule_score,
            ai_score=ai_score,
            api_score=0
        )