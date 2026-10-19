from core.models import AnalysisResult, Verdict
from rules.url_rules import URLRules
from ai.url_ai import URLAI
from apis.urlscan import URLScanAPI


class URLDetector:
    """Combines Rules + AI + URLScan.io for URL analysis"""
    
    def __init__(self, api_key: str = None):
        self.rules = URLRules()
        self.ai = URLAI()
        self.api = URLScanAPI(api_key)
    
    async def analyze(self, url: str) -> AnalysisResult:
        reasons = []
        
        print(f"\nAnalyzing URL: {url}")
        print("-" * 40)
        
        # 1. RULES
        print("Running heuristic rules...")
        rule_score, rule_reasons = self.rules.analyze(url)
        reasons.extend(rule_reasons)
        
        # 2. AI
        print("Running AI analysis...")
        ai_score, ai_reasons = self.ai.analyze(url)
        reasons.extend(ai_reasons)
        
        # 3. URLSCAN.IO API
        print("Checking URLScan.io...")
        api_score, api_reasons, report_link = await self.api.analyze(url)
        reasons.extend(api_reasons)
        
        # CALCULATE AVERAGE
        scores = []
        if rule_score > 0:
            scores.append(rule_score)
        if ai_score > 0:
            scores.append(ai_score)
        if api_score > 0:
            scores.append(api_score)
        
        if scores:
            final_score = sum(scores) / len(scores)
        else:
            final_score = 0
        
        reasons.append(f"\nSCORE BREAKDOWN:")
        reasons.append(f"   Heuristic Rules: {rule_score:.0f}%")
        reasons.append(f"   AI Model: {ai_score:.0f}%")
        reasons.append(f"   URLScan.io: {api_score:.0f}%")
        reasons.append(f"   ───────────────────")
        reasons.append(f"   FINAL SCORE: {final_score:.0f}%")
        
        print(f"\n   Final score: {final_score:.0f}%")
        
        # DETERMINE VERDICT
        if final_score >= 60:
            verdict = Verdict.MALICIOUS
            confidence = min(0.95, final_score / 100)
        elif final_score >= 30:
            verdict = Verdict.SUSPICIOUS
            confidence = final_score / 100
        else:
            verdict = Verdict.SAFE
            confidence = 1 - (final_score / 100)
        
        return AnalysisResult(
            input_type="URL",
            original_input=url,
            verdict=verdict,
            confidence=confidence,
            reasons=reasons,
            rule_score=rule_score,
            ai_score=ai_score,
            api_score=api_score,
            final_score=final_score,
            scan_report_link=report_link
        )