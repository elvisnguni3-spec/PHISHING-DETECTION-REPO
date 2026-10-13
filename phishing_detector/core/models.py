
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class Verdict(Enum):
    SAFE = "Safe"
    SUSPICIOUS = "Suspicious"
    MALICIOUS = "Malicious"
    SCAM = "Scam"
    ERROR = "Error"


@dataclass
class AnalysisResult:
    input_type: str
    original_input: str
    timestamp: datetime = field(default_factory=datetime.now)
    verdict: Verdict = Verdict.SAFE
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    rule_score: float = 0.0
    ai_score: float = 0.0
    api_score: float = 0.0
    final_score: float = 0.0
    scan_report_link: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'input_type': self.input_type,
            'original_input': self.original_input,
            'verdict': self.verdict.value,
            'confidence': self.confidence,
            'reasons': self.reasons,
            'rule_score': self.rule_score,
            'ai_score': self.ai_score,
            'api_score': self.api_score,
            'final_score': self.final_score,
            'scan_report_link': self.scan_report_link
        }
