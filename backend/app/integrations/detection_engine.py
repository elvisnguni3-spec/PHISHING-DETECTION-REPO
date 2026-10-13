from fastapi import HTTPException
from urllib.parse import urlparse
import re
import ipaddress
import tldextract
from datetime import datetime, UTC

from app.schemas.scan_schema import (
    Analysis,
    Explanation,
    Features,
    Metadata,
    Recommendation,
    RiskBreakdown,
    ScanResponse,

)


# =========================
# Helpers
# =========================

def normalize_url(url: str) -> str:
    """
    Normalize a URL before scanning.
    """

    # Remove leading/trailing spaces
    url = url.strip()

    # Convert the scheme to lowercase
    if url.lower().startswith("https://"):
        url = "https://" + url[8:]
    elif url.lower().startswith("http://"):
        url = "http://" + url[7:]

    # If no scheme exists, assume HTTPS
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def is_valid_url(url: str) -> bool:
    """
    Checks whether a URL has a valid structure.
    """

    parsed = urlparse(url)

    # Must have a scheme
    if not parsed.scheme:
        return False

    # Must have a hostname
    if not parsed.netloc:
        return False

    hostname = parsed.hostname or ""

    # Must contain at least one dot
    if "." not in hostname:
        return False

    return True



def parse_url(url: str):
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    return {
        "scheme": parsed.scheme,
        "hostname": hostname,
        "path": parsed.path,
        "labels": hostname.split(".") if hostname else []
    }


def get_registered_domain(hostname: str) -> str:
    if not hostname:
        return ""

    extracted = tldextract.extract(hostname)

    if not extracted.domain or not extracted.suffix:
        return hostname

    return f"{extracted.domain}.{extracted.suffix}"



def get_tld(hostname: str) -> str:
    if not hostname or "." not in hostname:
        return ""
    return hostname.split(".")[-1]


def count_subdomains(hostname: str) -> int:
    if not hostname:
        return 0

    # IP addresses do not have subdomains
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", hostname):
        return 0

    parts = hostname.split(".")

    return max(0, len(parts) - 2)

def detect_subdomain_abuse(
    hostname: str,
    registered_domain: str,
    trusted_domains: list[str]
):

    """
    Detects a trusted brand being used inside a subdomain
    while the actual registered domain belongs to someone else.
    """

    if not hostname or not registered_domain:
         return None


    # If the actual domain is trusted, this is not subdomain abuse.
         # If the actual domain is trusted, this is not subdomain abuse.
    if registered_domain in trusted_domains:
         return None

    suffix = "." + registered_domain

    if not hostname.endswith(suffix):
         return None


    # If the actual domain is trusted, this is not subdomain abuse.
    if registered_domain in trusted_domains:
         return None

    suffix = "." + registered_domain

    if not hostname.endswith(suffix):
         return None

    # Extract everything before the registered domain.
    subdomain = hostname[:-len(suffix)].rstrip(".")

    if not subdomain:
         return None

    # Break the subdomain into individual parts.
    labels = subdomain.split(".")



    for trusted_domain in trusted_domains:

        brand = trusted_domain.split(".")[0]


        if brand in labels:
                return {
                    "brand": brand,
                    "subdomain": subdomain,
                    "registered_domain": registered_domain
                }

    return None


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    if len(s1) == 0:
        return len(s2)

    previous_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        current_row = [i + 1]

        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)

            current_row.append(
                min(insertions, deletions, substitutions)
            )

        previous_row = current_row

    return previous_row[-1]

def similarity_score(s1: str, s2: str) -> float:
    """
    Calculates how similar two strings are using
    Levenshtein distance.

    Returns a value between 0 and 1.
    """

    if not s1 or not s2:
        return 0.0

    distance = levenshtein_distance(s1, s2)

    max_length = max(len(s1), len(s2))

    return 1 - (distance / max_length)


# =========================
# Main Detection Function
# =========================
def simple_phishing_check(url: str) -> ScanResponse:


    url = normalize_url(url)

    if not is_valid_url(url):
        raise HTTPException(

             status_code=400,
             detail="Invalid URL. Please enter a valid website address."
        )

    risk_score = 0
    indicators = []
    explanations = []

    parsed = parse_url(url)

    hostname = parsed["hostname"]
    path = parsed["path"]
    labels = parsed["labels"]

    hostname_lower = hostname.lower()
    path_lower = path.lower()

    registered_domain = get_registered_domain(hostname_lower)
    tld = get_tld(hostname_lower)
    subdomain_count = count_subdomains(hostname_lower)

    trusted_domains = [
        "google.com",
        "paypal.com",
        "microsoft.com",
        "apple.com",
        "amazon.com",
        "facebook.com"
    ]

    subdomain_abuse = detect_subdomain_abuse(
    hostname_lower,
    registered_domain,
    trusted_domains
)

    print("SUBDOMAIN ABUSE RESULT:", subdomain_abuse)


    suspicious_keywords = ["login", "verify", "bank", "update", "secure", "account"]

    # =========================
    # Rule 1: Keywords
    # =========================

    hostname_keyword_count = 0
    path_keyword_count = 0

    # ---------------------------------
    # Check suspicious keywords
    # ---------------------------------
    for word in suspicious_keywords:

        # Keywords in hostname
        if word in hostname_lower:

            if registered_domain in trusted_domains:

                risk_score += 10

                indicators.append(
                    f"Keyword in trusted domain (low risk): {word}"
                )

                explanations.append({
                    "rule": "Keyword Detection",
                    "impact": "+10",
                    "reason": (
                        f"The keyword '{word}' appears in a trusted domain. "
                        "This is treated as a low-risk signal."
                    )
                })

            else:
                hostname_keyword_count += 1

        # Keywords in path
        elif word in path_lower:
            path_keyword_count += 1


    # ---------------------------------
    # Hostname keyword scoring
    # ---------------------------------
    if registered_domain not in trusted_domains:

        if hostname_keyword_count >= 3:

            risk_score += 20

            indicators.append(
                f"Multiple suspicious keywords in hostname "
                f"({hostname_keyword_count})"
            )

            explanations.append({
                "rule": "Keyword Detection",
                "impact": "+20",
                "reason": (
                    f"The hostname contains {hostname_keyword_count} "
                    "suspicious keywords, which increases phishing risk."
                )
            })

        elif hostname_keyword_count == 2:

            risk_score += 15

            indicators.append(
                f"Multiple suspicious keywords in hostname "
                f"({hostname_keyword_count})"
            )

            explanations.append({
                "rule": "Keyword Detection",
                "impact": "+15",
                "reason": (
                    "The hostname contains two suspicious keywords, "
                    "which increases phishing risk."
                )
            })

        elif hostname_keyword_count == 1:

            risk_score += 10

            indicators.append(
                "Suspicious keyword in hostname"
            )

            explanations.append({
                "rule": "Keyword Detection",
                "impact": "+10",
                "reason": (
                    "A suspicious keyword appears in the hostname."
                )
            })


    # ---------------------------------
    # Path keyword scoring
    # ---------------------------------
    if path_keyword_count > 0:

        path_score = min(path_keyword_count * 3, 6)

        risk_score += path_score

        indicators.append(
            f"Suspicious keywords in path ({path_keyword_count})"
        )

        explanations.append({
            "rule": "Keyword Detection",
            "impact": f"+{path_score}",
            "reason": (
                f"The URL path contains {path_keyword_count} "
                "suspicious keyword(s). Path keywords are treated "
                "as weaker evidence than hostname keywords."
            )
        })
    # =========================
    # Rule 2: URL shorteners
    # =========================
    print("DEBUG hostname:", hostname_lower)
    print("DEBUG shortener matches:", [x for x in ["bit.ly", "tinyurl", "t.co", "short"] if x in hostname_lower])


    registered_domain = get_registered_domain(hostname_lower)

    if registered_domain in ["bit.ly", "tinyurl.com", "t.co"]:
        risk_score += 30
        indicators.append("URL shortener detected")


        explanations.append({
            "rule": "URL Shortener Detection",
            "impact": "+30",
            "reason": "Shortened URLs hide the real destination."
        })


    # =========================
    # Rule 3: HTTPS
    # =========================
    if not url.startswith("https"):
        risk_score += 15
        indicators.append("No HTTPS encryption")


        explanations.append({
            "rule": "HTTPS Check",
            "impact": "+15",
            "reason": "Connection is not encrypted (HTTP used)."
        })


    print("Hyphen count:", hostname.count("-"))

    # =========================
    # Rule 4: Hyphens
    # =========================
    hyphen_count = hostname.count("-")

    if hyphen_count > 2:

        risk_score += 10

        indicators.append(
            f"Excessive hyphens in domain ({hyphen_count})"
        )

        explanations.append({
            "rule": "Hyphen Structure Detection",
            "impact": "+10",
            "reason": (
                f"The hostname contains {hyphen_count} hyphens, "
                "which may indicate an unusually complex or deceptive "
                "domain structure."
            )
        })

    # =========================
    # Rule 5: Levenshtein
    # =========================
    trusted_brands = ["google", "paypal", "microsoft", "apple", "amazon", "facebook"]

    best_match = None
    best_similarity = 0.0

    base_domain = registered_domain.split(".")[0]

    # Only check for typosquatting if the domain
    # is NOT already a legitimate trusted domain.
    if registered_domain not in trusted_domains:

        for brand in trusted_brands:

            similarity = similarity_score(base_domain, brand)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = brand

        if best_similarity >= 0.80:

            risk_score += 30

            indicators.append(
                f"Strong typosquatting signal → {best_match}"
            )

            explanations.append({
                "rule": "Typosquatting Detection",
                "impact": "+30",
                "reason": f"Domain is extremely similar to {best_match}"
            })

        elif best_similarity >= 0.70:

            risk_score += 20

            indicators.append(
                f"Moderate similarity to {best_match}"
            )

            explanations.append({
                "rule": "Typosquatting Detection",
                "impact": "+20",
                "reason": f"Domain is similar to {best_match}"
            })


    # =========================
    # Rule 6: IP detection
    # =========================

    is_ip = False

    try:
        ipaddress.ip_address(hostname)
        is_ip = True
    except ValueError:
        is_ip = False

    if is_ip:

        risk_score += 25

        indicators.append(
            "IP address used instead of domain name"
        )

        explanations.append({
            "rule": "IP Address Detection",
            "impact": "+25",
            "reason": (
                "The URL uses an IP address instead of a domain name, "
                "which can be used to obscure the identity of the destination."
            )
        })

    # =========================
    # Rule 7: TLD risk
    # =========================
    suspicious_tlds = [
        "xyz",
        "top",
        "click",
        "shop",
        "online",
        "site",
        "info",
        "icu"
    ]

    if tld in suspicious_tlds:

        risk_score += 20

        indicators.append(
            f"Suspicious TLD: .{tld}"
        )

        explanations.append({
            "rule": "Suspicious TLD Detection",
            "impact": "+20",
            "reason": (
                f"The domain uses the '.{tld}' TLD, which is treated "
                "as a higher-risk signal because it is commonly associated "
                "with suspicious or abusive domains."
            )
        })


    # =========================
    # Rule 8: Subdomains
    # =========================
    if registered_domain not in trusted_domains:

        if subdomain_count >= 3:

            risk_score += 10

            indicators.append(
                f"Excessive subdomains ({subdomain_count})"
            )

            explanations.append({
                "rule": "Subdomain Structure Detection",
                "impact": "+10",
                "reason": (
                    f"The hostname contains {subdomain_count} subdomains, "
                    "which creates an unusually complex domain structure."
                )
            })

        elif subdomain_count == 2:

            risk_score += 5

            indicators.append(
                "Multiple subdomains detected"
            )

            explanations.append({
                "rule": "Subdomain Structure Detection",
                "impact": "+5",
                "reason": (
                    "The hostname contains multiple subdomains, "
                    "which slightly increases structural risk."
                )
            })


 # =========================
# Rule 9: Subdomain Abuse
# =========================
    if subdomain_abuse:
        risk_score += 20

        indicators.append(
            f"Trusted brand used in suspicious subdomain: "
            f"{subdomain_abuse['brand']}"
        )

        explanations.append({
            "rule": "Subdomain Abuse Detection",
            "impact": "+20",
            "reason": (
                f"The trusted brand '{subdomain_abuse['brand']}' "
                f"appears in the subdomain, but the actual registered "
                f"domain is '{subdomain_abuse['registered_domain']}'."
            )
        })

    # =========================
    # Final verdict
    # =========================
    risk_score = min(risk_score, 100)

    if risk_score >= 70:
        verdict = "malicious"
    elif risk_score >= 30:
        verdict = "suspicious"
    else:
        verdict = "safe"


    confidence = min(100, risk_score + 10)

    analysis = Analysis(
        score=risk_score,
        verdict=verdict,
        confidence=confidence,
    )

    risk_breakdown = RiskBreakdown(
        rules_score=risk_score,
        ml_score=0,
        urlscan_score=0,
    )

    features = Features(
        https=url.startswith("https"),
        contains_ip=is_ip,
        subdomains=subdomain_count,
        length=len(url),
        special_characters=len(re.findall(r"[^a-zA-Z0-9]", url)),
        contains_login_keyword=any(
            keyword in hostname_lower or keyword in path_lower
            for keyword in suspicious_keywords
        ),
    )

    if verdict == "safe":
        recommendation = Recommendation(
            action="Safe to visit.",
            safe_to_open=True,
        )
    elif verdict == "suspicious":
        recommendation = Recommendation(
            action="Proceed with caution.",
            safe_to_open=False,
        )
    else:
        recommendation = Recommendation(
            action="Do not visit this website.",
            safe_to_open=False,
        )

    metadata = Metadata(
        scan_time=datetime.now(UTC),
        engine_version="1.0.0",
        scan_type="url",
    )

    explanation_models = [
        Explanation(
            rule=item["rule"],
            impact=item["impact"],
            reason=item["reason"],
        )
        for item in explanations
    ]

    return ScanResponse(
        input=url,
        analysis=analysis,
        risk_breakdown=risk_breakdown,
        features=features,
        explanation=explanation_models,
        recommendation=recommendation,
        metadata=metadata,
    )


