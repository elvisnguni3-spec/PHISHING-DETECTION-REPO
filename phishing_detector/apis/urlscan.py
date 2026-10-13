import aiohttp
import asyncio
from typing import Tuple, List, Optional


class URLScanAPI:
    """URLScan.io API integration."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://urlscan.io/api/v1"

    async def analyze(
        self,
        url: str
    ) -> Tuple[float, List[str], Optional[str]]:

        reasons = []

        # ---------------------------------------------------------
        # CHECK API KEY
        # ---------------------------------------------------------

        if not self.api_key:
            return (
                0,
                ["URLScan API key is not configured"],
                None
            )

        # ---------------------------------------------------------
        # HEADERS
        # ---------------------------------------------------------

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        # ---------------------------------------------------------
        # PAYLOAD
        # ---------------------------------------------------------

        payload = {
            "url": url,
            "visibility": "public"
        }

        timeout = aiohttp.ClientTimeout(total=120)

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            try:

                # =================================================
                # 1. SUBMIT SCAN
                # =================================================

                print("\nSubmitting URL to URLScan...")
                print(f"URL: {url}")

                async with session.post(
                    f"{self.base_url}/scan",
                    json=payload,
                    headers=headers
                ) as response:

                    response_text = await response.text()

                    print(
                        f"URLScan submission status: "
                        f"{response.status}"
                    )

                    if response.status not in (200, 201):

                        print(
                            f"URLScan response: "
                            f"{response_text}"
                        )

                        return (
                            0,
                            [
                                f"URLScan submission failed: "
                                f"HTTP {response.status}: "
                                f"{response_text[:200]}"
                            ],
                            None
                        )

                    try:
                        scan_data = await response.json()
                    except Exception:

                        return (
                            0,
                            [
                                "URLScan returned an invalid JSON response"
                            ],
                            None
                        )

                # =================================================
                # 2. GET SCAN UUID
                # =================================================

                scan_id = scan_data.get("uuid")

                report_link = scan_data.get("result")

                if not scan_id:

                    return (
                        0,
                        [
                            "URLScan did not return a scan UUID"
                        ],
                        report_link
                    )

                reasons.append(
                    f"URLScan scan submitted successfully"
                )

                print(
                    f"URLScan scan ID: {scan_id}"
                )

                print(
                    f"URLScan report: {report_link}"
                )

                # =================================================
                # 3. WAIT FOR SCAN
                # =================================================

                print(
                    "Waiting for URLScan analysis..."
                )

                await asyncio.sleep(10)

                # =================================================
                # 4. POLL RESULT
                # =================================================

                max_attempts = 25

                for attempt in range(max_attempts):

                    print(
                        f"Checking URLScan result "
                        f"({attempt + 1}/{max_attempts})..."
                    )

                    async with session.get(
                        f"{self.base_url}/result/{scan_id}/",
                        headers=headers
                    ) as result_response:

                        # -------------------------------------------------
                        # SCAN NOT READY
                        # -------------------------------------------------

                        if result_response.status == 404:

                            print(
                                "Scan not ready yet..."
                            )

                            await asyncio.sleep(3)

                            continue

                        # -------------------------------------------------
                        # AUTHENTICATION ERROR
                        # -------------------------------------------------

                        if result_response.status == 401:

                            error_text = await result_response.text()

                            return (
                                0,
                                [
                                    "URLScan result authentication "
                                    f"failed: {error_text[:200]}"
                                ],
                                report_link
                            )

                        # -------------------------------------------------
                        # OTHER ERROR
                        # -------------------------------------------------

                        if result_response.status != 200:

                            error_text = await result_response.text()

                            return (
                                0,
                                [
                                    f"URLScan result request failed: "
                                    f"HTTP {result_response.status}: "
                                    f"{error_text[:200]}"
                                ],
                                report_link
                            )

                        # -------------------------------------------------
                        # RESULT READY
                        # -------------------------------------------------

                        result_data = await result_response.json()

                        print(
                            "URLScan result received!"
                        )

                        return self._process_result(
                            result_data,
                            report_link
                        )

                # =================================================
                # 5. RESULT TIMEOUT
                # =================================================

                return (
                    0,
                    [
                        "URLScan scan was submitted, "
                        "but the result was not ready "
                        "within the polling period"
                    ],
                    report_link
                )

            # =====================================================
            # NETWORK TIMEOUT
            # =====================================================

            except asyncio.TimeoutError:

                return (
                    0,
                    [
                        "URLScan request timed out"
                    ],
                    None
                )

            # =====================================================
            # AIOHTTP ERROR
            # =====================================================

            except aiohttp.ClientError as e:

                return (
                    0,
                    [
                        f"URLScan connection error: "
                        f"{str(e)[:200]}"
                    ],
                    None
                )

            # =====================================================
            # UNEXPECTED ERROR
            # =====================================================

            except Exception as e:

                return (
                    0,
                    [
                        f"URLScan error: "
                        f"{str(e)[:200]}"
                    ],
                    None
                )

    # =============================================================
    # PROCESS URLSCAN RESULT
    # =============================================================

    def _process_result(
        self,
        result_data: dict,
        report_link: Optional[str]
    ) -> Tuple[float, List[str], Optional[str]]:

        reasons = []

        # ---------------------------------------------------------
        # VERDICTS
        # ---------------------------------------------------------

        verdicts = result_data.get(
            "verdicts",
            {}
        )

        print("\nURLScan verdicts:")
        print(verdicts)

        # ---------------------------------------------------------
        # OVERALL VERDICT
        # ---------------------------------------------------------

        overall = verdicts.get(
            "overall",
            {}
        )

        score = 0

        if overall.get("malicious"):

            score = 95

            reasons.append(
                "URLScan.io: Malicious"
            )

        elif overall.get("suspicious"):

            score = 70

            reasons.append(
                "URLScan.io: Suspicious"
            )

        else:

            score = 10

            reasons.append(
                "URLScan.io: No malicious verdict"
            )

        # ---------------------------------------------------------
        # ENGINE VERDICTS
        # ---------------------------------------------------------

        engines = verdicts.get(
            "engines",
            {}
        )

        malicious_engines = 0
        suspicious_engines = 0

        if isinstance(engines, dict):

            for engine_name, engine_result in engines.items():

                if not isinstance(engine_result, dict):
                    continue

                if engine_result.get("malicious"):
                    malicious_engines += 1

                    reasons.append(
                        f"URLScan engine flagged URL: "
                        f"{engine_name}"
                    )

                elif engine_result.get("suspicious"):
                    suspicious_engines += 1

                    reasons.append(
                        f"URLScan engine marked URL suspicious: "
                        f"{engine_name}"
                    )

        if malicious_engines > 0:

            score = max(
                score,
                min(
                    95,
                    60 + malicious_engines * 10
                )
            )

        elif suspicious_engines > 0:

            score = max(
                score,
                70
            )

        # ---------------------------------------------------------
        # PAGE INFORMATION
        # ---------------------------------------------------------

        page = result_data.get(
            "page",
            {}
        )

        page_url = page.get("url")
        page_status = page.get("status")
        page_title = page.get("title")
        page_ip = page.get("ip")
        page_country = page.get("country")

        if page_url:

            reasons.append(
                f"Final URL: {page_url}"
            )

        if page_status is not None:

            reasons.append(
                f"HTTP status: {page_status}"
            )

        if page_title:

            reasons.append(
                f"Page title: {page_title}"
            )

        if page_ip:

            reasons.append(
                f"Server IP: {page_ip}"
            )

        if page_country:

            reasons.append(
                f"Server country: {page_country}"
            )

        # ---------------------------------------------------------
        # STATS
        # ---------------------------------------------------------

        stats = result_data.get(
            "stats",
            {}
        )

        requests = stats.get("requests")
        unique_ips = stats.get("uniqIPs")
        unique_countries = stats.get("uniqCountries")

        if requests is not None:

            reasons.append(
                f"Network requests: {requests}"
            )

        if unique_ips is not None:

            reasons.append(
                f"Unique IPs contacted: {unique_ips}"
            )

        if unique_countries is not None:

            reasons.append(
                f"Unique countries contacted: "
                f"{unique_countries}"
            )

        # ---------------------------------------------------------
        # RETURN
        # ---------------------------------------------------------

        return (
            float(min(score, 100)),
            reasons,
            report_link
        )