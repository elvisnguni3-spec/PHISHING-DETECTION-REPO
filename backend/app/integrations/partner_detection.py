
import os

import httpx
from fastapi import HTTPException


DETECTION_ENGINE_URL = os.getenv(
    "DETECTION_ENGINE_URL",
    "http://127.0.0.1:8001",
)


async def detect_with_partner(url: str, input_type: str = "URL") -> dict:
    """Send a URL (or message text) to the partner's detection engine."""

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{DETECTION_ENGINE_URL}/detect",
                json={
                    "input": url,
                    "input_type": input_type,
                },
            )

        response.raise_for_status()
        payload = response.json()

        result = payload.get("data")

        if payload.get("success") is not True or not isinstance(result, dict):
            raise HTTPException(
                status_code=502,
                detail="Detection engine returned an invalid response.",
            )

        return result

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Detection engine took too long to respond.",
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="Detection engine returned an error.",
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the detection engine.",
        ) from exc


def prepare_partner_result(result: dict) -> dict:
    """Convert the partner's result into basic backend fields."""

    try:
        rule_score = float(result["rule_score"])
        ai_score = float(result["ai_score"])
        api_score = float(result["api_score"])
        confidence = float(result["confidence"])
        verdict = str(result["verdict"]).lower()
        original_input = str(result["original_input"])
        reasons = result["reasons"]

        if not isinstance(reasons, list):
            raise ValueError("Reasons must be a list.")

        scores = [
            score
            for score in (rule_score, ai_score, api_score)
            if score > 0
        ]

        score = round(float(result["final_score"]))

        if not 0 <= score <= 100 or not 0 <= confidence <= 1:
            raise ValueError("Score or confidence is outside its valid range.")

        if verdict not in {"safe", "suspicious", "malicious", "scam", "error"}:
            raise ValueError("Unknown verdict.")

        return {
            "input": original_input,
            "verdict": verdict,
            "confidence": round(confidence * 100),
            "score": score,
            "reasons": reasons,
            "rule_score": rule_score,
            "ai_score": ai_score,
            "api_score": api_score,
            "scan_report_link": result.get("scan_report_link"),
        }

    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Detection engine returned an invalid analysis result.",
        ) from exc
