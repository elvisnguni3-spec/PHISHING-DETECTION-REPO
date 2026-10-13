from datetime import datetime
from pydantic import BaseModel

class URLScanRequest(BaseModel):
    url: str

class Analysis(BaseModel):
    score: int
    verdict: str
    confidence: int


class RiskBreakdown(BaseModel):
    rules_score: int
    ml_score: int
    urlscan_score: int


class Features(BaseModel):
    https: bool
    contains_ip: bool
    subdomains: int
    length: int
    special_characters: int
    contains_login_keyword: bool


class Explanation(BaseModel):
    rule: str
    impact: str
    reason: str


class Recommendation(BaseModel):
    action: str
    safe_to_open: bool


class Metadata(BaseModel):
    scan_time: datetime
    engine_version: str
    scan_type: str


class ScanResponse(BaseModel):
    input: str
    analysis: Analysis
    risk_breakdown: RiskBreakdown
    features: Features
    explanation: list[Explanation]
    recommendation: Recommendation
    metadata: Metadata




