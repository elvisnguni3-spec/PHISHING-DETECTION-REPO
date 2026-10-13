
from datetime import datetime, UTC
from urllib.parse import urlparse
import ipaddress
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models.user import User
from app.database.connection import get_db
from app.models.scan_result import ScanResult

from app.schemas.scan_schema import (
    URLScanRequest,
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

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
    return current_user


async def run_detection(url: str) -> dict:
    raw_result = await detect_with_partner(url)
    return prepare_partner_result(raw_result)


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
