
from datetime import datetime, UTC
from urllib.parse import urlparse
import ipaddress
import re

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models.user import User
from app.database.connection import get_db
from app.models.scan_result import ScanResult

from app.schemas.scan_schema import (
    URLScanRequest,
    BatchScanRequest,
    ScanResponse,
    Analysis,
    RiskBreakdown,
    Features,
    Explanation,
    Recommendation,
    Metadata,
)
from app.schemas.report_schema import ReportResponse

from app.integrations.partner_detection import (
    detect_with_partner,
    prepare_partner_result,
)
from app.integrations.detection_engine import simple_phishing_check

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
    return current_user


async def run_detection(url: str) -> dict:
    try:
        raw_result = await detect_with_partner(url)
        return prepare_partner_result(raw_result)
    except Exception:
        # Fallback to local heuristic detection engine if partner engine is offline or unreachable
        fallback = simple_phishing_check(url)
        reasons = [e.reason for e in fallback.explanation]
        return {
            "input": url,
            "verdict": fallback.analysis.verdict,
            "confidence": fallback.analysis.confidence,
            "score": fallback.analysis.score,
            "reasons": reasons if reasons else ["No suspicious patterns detected"],
            "rule_score": fallback.risk_breakdown.rules_score,
            "ai_score": fallback.risk_breakdown.ml_score,
            "api_score": fallback.risk_breakdown.urlscan_score,
            "scan_report_link": None,
        }


def format_level(score: int, verdict: str) -> str:
    if score >= 70 or verdict.lower() in {"malicious", "scam"}:
        return "Malicious"
    if score >= 30 or verdict.lower() == "suspicious":
        return "Suspicious"
    return "Safe"


def build_frontend_scan_result(result: dict) -> dict:
    score = int(result.get("score", 0))
    verdict = str(result.get("verdict", "safe")).lower()
    level = format_level(score, verdict)
    reasons = [str(r) for r in result.get("reasons", []) if str(r).strip()]
    if not reasons:
        reasons = ["No suspicious patterns detected"]

    return {
        "id": str(uuid.uuid4()),
        "url": result.get("input", ""),
        "score": score,
        "level": level,
        "reasons": reasons,
        "scannedAt": datetime.now(UTC).isoformat(),
        "confidence": result.get("confidence", 0),
        "rule_score": result.get("rule_score", 0),
        "ai_score": result.get("ai_score", 0),
        "api_score": result.get("api_score", 0),
        "scan_report_link": result.get("scan_report_link"),
    }


def build_scan_response(result: dict) -> ScanResponse:
    url = result["input"]
    verdict = result["verdict"]
    hostname = urlparse(url).hostname or ""

    try:
        ipaddress.ip_address(hostname)
        contains_ip = True
    except ValueError:
        contains_ip = False

    features = Features(
        https=urlparse(url).scheme.lower() == "https",
        contains_ip=contains_ip,
        subdomains=(
            max(0, len(hostname.split(".")) - 2)
            if hostname and not contains_ip
            else 0
        ),
        length=len(url),
        special_characters=len(re.findall(r"[^a-zA-Z0-9]", url)),
        contains_login_keyword=any(
            word in (hostname + urlparse(url).path).lower()
            for word in [
                "login", "verify", "bank",
                "update", "secure", "account",
            ]
        ),
    )

    explanations = [
        Explanation(
            rule="Partner Detection Engine",
            impact="Informational",
            reason=str(reason),
        )
        for reason in result["reasons"]
    ]

    if verdict == "safe":
        recommendation = Recommendation(
            action=(
                "The detection engine classified this URL as safe. "
                "Still verify the destination before entering sensitive information."
            ),
            safe_to_open=True,
        )
    elif verdict == "suspicious":
        recommendation = Recommendation(
            action="Proceed with caution and verify the website independently.",
            safe_to_open=False,
        )
    else:
        recommendation = Recommendation(
            action="Avoid visiting this website or entering sensitive information.",
            safe_to_open=False,
        )

    return ScanResponse(
        input=url,
        analysis=Analysis(
            score=result["score"],
            verdict=verdict,
            confidence=result["confidence"],
        ),
        risk_breakdown=RiskBreakdown(
            rules_score=round(result["rule_score"]),
            ml_score=round(result["ai_score"]),
            urlscan_score=round(result["api_score"]),
        ),
        features=features,
        explanation=explanations,
        recommendation=recommendation,
        metadata=Metadata(
            scan_time=datetime.now(UTC),
            engine_version="partner",
            scan_type="url",
        ),
    )


class TextScanRequest(BaseModel):
    text: str


SCAM_PHRASES = [
    "verify your account", "urgent", "suspended", "click here", "password",
    "bank", "winner", "prize", "gift card", "wire transfer", "limited time",
    "confirm your identity", "login", "otp", "pin", "act now", "invoice",
]


def simple_text_check(text: str) -> dict:
    """Basic keyword check, used only if the detection engine is offline."""
    lowered = text.lower()
    hits = [phrase for phrase in SCAM_PHRASES if phrase in lowered]
    links = re.findall(r"https?://\S+|www\.\S+", text)

    score = len(hits) * 15
    reasons = [f"Contains the phrase '{phrase}'" for phrase in hits]
    if links:
        score += 15
        reasons.append("Contains a link that you should verify before opening")
    if text.count("!") >= 2:
        score += 10
        reasons.append("Uses pressure tactics such as repeated exclamation marks")
    score = min(score, 100)

    return {
        "input": text,
        "verdict": "malicious" if score >= 70 else "suspicious" if score >= 30 else "safe",
        "confidence": min(100, score + 10),
        "score": score,
        "reasons": reasons or ["No suspicious patterns detected"],
        "rule_score": score,
        "ai_score": 0,
        "api_score": 0,
        "scan_report_link": None,
    }


@router.post("/scan/text")
async def scan_text(data: TextScanRequest):
    text = data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        raw_result = await detect_with_partner(text, "Text")
        # The engine's text detector does not set final_score (it stays 0),
        # so rebuild it from the rule and AI scores.
        if not float(raw_result.get("final_score") or 0):
            raw_result["final_score"] = (
                float(raw_result.get("rule_score") or 0)
                + float(raw_result.get("ai_score") or 0)
            ) / 2
        result = prepare_partner_result(raw_result)
    except Exception:
        # Engine offline or returned something unusable: use the simple check
        result = simple_text_check(text)

    response = build_frontend_scan_result(result)
    response["type"] = "message"
    return response


@router.post("/scan/single")
async def scan_single(data: URLScanRequest):
    result = await run_detection(data.url)
    return build_frontend_scan_result(result)


@router.post("/scan/batch")
async def scan_batch(data: BatchScanRequest):
    results = []
    for raw_url in data.urls:
        url = raw_url.strip()
        if not url:
            continue
        result = await run_detection(url)
        results.append(build_frontend_scan_result(result))
    return {"results": results}


@router.post("/detect", response_model=ScanResponse)
async def detect_phishing(data: URLScanRequest):
    result = await run_detection(data.url)
    return build_scan_response(result)


@router.post("/reports", response_model=ReportResponse)
async def create_report(
    data: URLScanRequest,
    db: Session = Depends(get_db),
):
    result = await run_detection(data.url)

    report = ScanResult(
        input=result["input"],
        verdict=result["verdict"],
        confidence=result["confidence"],
        score=result["score"],
    )

    try:
        db.add(report)
        db.commit()
        db.refresh(report)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save report.",
        ) from exc

    return ReportResponse(
        scan_id=report.scan_id,
        input=report.input,
        verdict=report.verdict,
        confidence=report.confidence,
        score=report.score,
        created_at=report.created_at,
    )


@router.get("/reports", response_model=list[ReportResponse])
def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    reports = (
        db.query(ScanResult)
        .order_by(ScanResult.created_at.desc())
        .all()
    )

    return [
        ReportResponse(
            scan_id=report.scan_id,
            input=report.input,
            verdict=report.verdict,
            confidence=report.confidence,
            score=report.score,
            created_at=report.created_at,
        )
        for report in reports
    ]


@router.get("/reports/{scan_id}", response_model=ReportResponse)
def get_report(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    report = (
        db.query(ScanResult)
        .filter(ScanResult.scan_id == scan_id)
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return ReportResponse(
        scan_id=report.scan_id,
        input=report.input,
        verdict=report.verdict,
        confidence=report.confidence,
        score=report.score,
        created_at=report.created_at,
    )
