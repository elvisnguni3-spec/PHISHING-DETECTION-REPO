from datetime import datetime
from pydantic import BaseModel


class ReportResponse(BaseModel):
    scan_id: int
    input: str
    verdict: str
    confidence: int
    score: int
    created_at: datetime
