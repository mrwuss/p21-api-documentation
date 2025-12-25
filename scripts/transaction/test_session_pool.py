"""
P21 Transaction API - Session Pool Behavior Test

This script tests for session pool contamination issues by:
1. Making rapid successive requests
2. Logging success/failure patterns
3. Testing with various delays
4. Capturing session-related headers

Results help diagnose intermittent failures caused by dirty session pools.
"""

import asyncio
import httpx
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = os.getenv("P21_BASE_URL", "https://play.p21server.com")
USERNAME = os.getenv("P21_USERNAME")
PASSWORD = os.getenv("P21_PASSWORD")

import warnings
warnings.filterwarnings("ignore")


@dataclass
class TestResult:
    """Result of a single API call."""
    attempt: int
    timestamp: str
    elapsed_ms: int
    success: bool
    status_code: int
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    session_headers: dict = field(default_factory=dict)
    response_preview: str = ""


class SessionPoolTester:
    """Tests P21 Transaction API session pool behavior."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.ui_server_url = None
        self.results: list[TestResult] = []

    async def authenticate(self, client: httpx.AsyncClient) -> None:
        """Get authentication token."""
        resp = await client.post(
            f"{self.base_url}/api/security/token",
            headers={
                "username": self.username,
                "password": self.password,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            content="",
            follow_redirects=True
        )
        resp.raise_for_status()
        self.token = resp.json()["AccessToken"]

        # Get UI server URL
        resp = await client.get(
            f"{self.base_url}/api/ui/router/v1?urlType=external",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
            follow_redirects=True
        )
        resp.raise_for_status()
        self.ui_server_url = resp.json()["Url"].rstrip("/")

    def build_test_payload(self) -> dict:
        """Build a simple test payload that should succeed.

        Using SalesPricePage create since we know it works.
        """
        return {
            "Name": "SalesPricePage",
            "UseCodeValues": False,
            "Transactions": [
                {
                    "DataElements": [
                        {
                            "Name": "FORM.form",
                            "Type": "Form",
                            "Keys": [],
                            "Rows": [{
                                "Edits": [
                                    {"Name": "price_page_type_cd", "Value": "Supplier / Product Group"},
                                    {"Name": "company_id", "Value": "ACME"},
                                    {"Name": "supplier_id", "Value": 10.0},
                                    {"Name": "product_group_id", "Value": "FA5"},
                                    {"Name": "description", "Value": f"SESSION-TEST-{datetime.now().strftime('%H%M%S%f')}"},
                                    {"Name": "pricing_method_cd", "Value": "Source"},
                                    {"Name": "source_price_cd", "Value": "Supplier List Price"},
                                    {"Name": "effective_date", "Value": "2025-01-01"},
                                    {"Name": "expiration_date", "Value": "2030-12-31"},
                                    {"Name": "totaling_method_cd", "Value": "Item"},
                                    {"Name": "totaling_basis_cd", "Value": "Supplier List Price"},
                                    {"Name": "row_status_flag", "Value": "Active"}
                                ],
                                "RelativeDateEdits": []
                            }]
                        },
                        {
                            "Name": "VALUES.values",
                            "Type": "Form",
                            "Keys": [],
                            "Rows": [{
                                "Edits": [
                                    {"Name": "calculation_method_cd", "Value": "Multiplier"},
                                    {"Name": "calculation_value1", "Value": "0.5"}
                                ],
                                "RelativeDateEdits": []
                            }]
                        }
                    ],
                    "Status": "New"
                }
            ]
        }

    async def make_request(self, client: httpx.AsyncClient, attempt: int) -> TestResult:
        """Make a single Transaction API request and capture results."""
        timestamp = datetime.now().isoformat()
        start = time.perf_counter()

        payload = self.build_test_payload()

        try:
            resp = await client.post(
                f"{self.ui_server_url}/api/v2/transaction",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=payload,
                follow_redirects=True,
                timeout=30.0
            )

            elapsed_ms = int((time.perf_counter() - start) * 1000)

            # Capture session-related headers
            session_headers = {
                k: v for k, v in resp.headers.items()
                if any(x in k.lower() for x in ['session', 'x-p21', 'server', 'instance'])
            }

            if resp.status_code == 200:
                data = resp.json()
                summary = data.get("Summary", {})
                succeeded = summary.get("Succeeded", 0)
                failed = summary.get("Failed", 0)
                messages = data.get("Messages", [])

                if succeeded > 0 and failed == 0:
                    return TestResult(
                        attempt=attempt,
                        timestamp=timestamp,
                        elapsed_ms=elapsed_ms,
                        success=True,
                        status_code=200,
                        session_headers=session_headers,
                        response_preview=f"Succeeded: {succeeded}"
                    )
                else:
                    error_msg = messages[0] if messages else "Unknown error"
                    return TestResult(
                        attempt=attempt,
                        timestamp=timestamp,
                        elapsed_ms=elapsed_ms,
                        success=False,
                        status_code=200,
                        error_type="ValidationError",
                        error_message=str(error_msg)[:200],
                        session_headers=session_headers,
                        response_preview=f"Failed: {failed}, Messages: {len(messages)}"
                    )
            else:
                error_text = resp.text[:500]
                error_type = "UnexpectedWindow" if "Unexpected response window" in error_text else "HTTPError"

                return TestResult(
                    attempt=attempt,
                    timestamp=timestamp,
                    elapsed_ms=elapsed_ms,
                    success=False,
                    status_code=resp.status_code,
                    error_type=error_type,
                    error_message=error_text[:200],
                    session_headers=session_headers,
                    response_preview=error_text[:100]
                )

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return TestResult(
                attempt=attempt,
                timestamp=timestamp,
                elapsed_ms=elapsed_ms,
                success=False,
                status_code=0,
                error_type=type(e).__name__,
                error_message=str(e)[:200],
                response_preview=""
            )

    async def run_rapid_test(self, count: int = 10, delay_ms: int = 0) -> list[TestResult]:
        """Run rapid successive requests with optional delay."""
        results = []

        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            await self.authenticate(client)

            for i in range(count):
                result = await self.make_request(client, i + 1)
                results.append(result)

                status = "OK" if result.success else "FAIL"
                print(f"  [{i+1:2d}] {status} {result.elapsed_ms:4d}ms - {result.response_preview[:50]}")

                if delay_ms > 0 and i < count - 1:
                    await asyncio.sleep(delay_ms / 1000)

        return results

    async def run_parallel_test(self, count: int = 5) -> list[TestResult]:
        """Run parallel requests to stress test session pool."""
        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            await self.authenticate(client)

            tasks = [self.make_request(client, i + 1) for i in range(count)]
            results = await asyncio.gather(*tasks)

            for result in results:
                status = "OK" if result.success else "FAIL"
                print(f"  [{result.attempt:2d}] {status} {result.elapsed_ms:4d}ms - {result.response_preview[:50]}")

            return list(results)

    async def run_pattern_test(self) -> dict:
        """Run various patterns to identify session pool behavior."""
        all_results = {}

        print("\n" + "=" * 70)
        print("TEST 1: Rapid Fire (10 requests, no delay)")
        print("=" * 70)
        all_results["rapid_fire"] = await self.run_rapid_test(10, delay_ms=0)

        await asyncio.sleep(2)

        print("\n" + "=" * 70)
        print("TEST 2: With 500ms Delay (10 requests)")
        print("=" * 70)
        all_results["delayed_500ms"] = await self.run_rapid_test(10, delay_ms=500)

        await asyncio.sleep(2)

        print("\n" + "=" * 70)
        print("TEST 3: With 2000ms Delay (5 requests)")
        print("=" * 70)
        all_results["delayed_2000ms"] = await self.run_rapid_test(5, delay_ms=2000)

        await asyncio.sleep(2)

        print("\n" + "=" * 70)
        print("TEST 4: Parallel Requests (5 concurrent)")
        print("=" * 70)
        all_results["parallel"] = await self.run_parallel_test(5)

        await asyncio.sleep(2)

        print("\n" + "=" * 70)
        print("TEST 5: Random Jitter (10 requests, 100-1000ms random delay)")
        print("=" * 70)
        results = []
        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            await self.authenticate(client)
            for i in range(10):
                result = await self.make_request(client, i + 1)
                results.append(result)
                status = "OK" if result.success else "FAIL"
                print(f"  [{i+1:2d}] {status} {result.elapsed_ms:4d}ms - {result.response_preview[:50]}")
                if i < 9:
                    jitter = random.uniform(0.1, 1.0)
                    await asyncio.sleep(jitter)
        all_results["random_jitter"] = results

        return all_results

    def analyze_results(self, all_results: dict) -> str:
        """Analyze test results and generate report."""
        report = []
        report.append("\n" + "=" * 70)
        report.append("SESSION POOL BEHAVIOR ANALYSIS")
        report.append("=" * 70)

        total_requests = 0
        total_failures = 0
        failure_patterns = {}

        for test_name, results in all_results.items():
            successes = sum(1 for r in results if r.success)
            failures = len(results) - successes
            total_requests += len(results)
            total_failures += failures

            report.append(f"\n{test_name.upper()}:")
            report.append(f"  Total: {len(results)}, Success: {successes}, Failed: {failures}")
            report.append(f"  Success Rate: {successes/len(results)*100:.1f}%")

            # Track failure patterns
            for r in results:
                if not r.success:
                    error_key = r.error_type or "Unknown"
                    failure_patterns[error_key] = failure_patterns.get(error_key, 0) + 1

            # Check for alternating pattern
            if len(results) >= 4:
                pattern = [r.success for r in results]
                alternating = all(pattern[i] != pattern[i+1] for i in range(len(pattern)-1))
                if alternating:
                    report.append("  [!] ALTERNATING PATTERN DETECTED!")

            # Check consecutive failures
            max_consecutive_fail = 0
            current_consecutive = 0
            for r in results:
                if not r.success:
                    current_consecutive += 1
                    max_consecutive_fail = max(max_consecutive_fail, current_consecutive)
                else:
                    current_consecutive = 0
            if max_consecutive_fail > 2:
                report.append(f"  [!] Max consecutive failures: {max_consecutive_fail}")

        report.append("\n" + "-" * 70)
        report.append("SUMMARY:")
        report.append(f"  Total Requests: {total_requests}")
        report.append(f"  Total Failures: {total_failures}")
        report.append(f"  Overall Success Rate: {(total_requests-total_failures)/total_requests*100:.1f}%")

        if failure_patterns:
            report.append("\n  Failure Types:")
            for error_type, count in sorted(failure_patterns.items(), key=lambda x: -x[1]):
                report.append(f"    - {error_type}: {count}")

        # Conclusions
        report.append("\n" + "-" * 70)
        report.append("CONCLUSIONS:")

        if total_failures == 0:
            report.append("  [OK] No failures detected - session pool appears healthy")
        elif total_failures / total_requests > 0.3:
            report.append("  [!] High failure rate (>30%) - likely session pool contamination")
            report.append("  [!] Consider using async endpoint or implementing retry logic")
        else:
            report.append("  [!] Intermittent failures detected")
            report.append("  [!] Pattern suggests session pool issues")

        if "UnexpectedWindow" in failure_patterns:
            report.append("  [!] 'Unexpected window' errors confirm dirty session pool")
            report.append("  [!] Previous operations left dialogs open in pooled sessions")

        return "\n".join(report)


async def main():
    print("=" * 70)
    print("P21 Transaction API - Session Pool Behavior Test")
    print("=" * 70)
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")

    tester = SessionPoolTester(BASE_URL, USERNAME, PASSWORD)

    # Run all pattern tests
    all_results = await tester.run_pattern_test()

    # Analyze and print report
    report = tester.analyze_results(all_results)
    print(report)

    # Save results to file
    output_file = Path(__file__).parent / "session_pool_results.json"
    results_json = {
        test_name: [
            {
                "attempt": r.attempt,
                "timestamp": r.timestamp,
                "elapsed_ms": r.elapsed_ms,
                "success": r.success,
                "status_code": r.status_code,
                "error_type": r.error_type,
                "error_message": r.error_message,
                "session_headers": r.session_headers
            }
            for r in results
        ]
        for test_name, results in all_results.items()
    }

    with open(output_file, "w") as f:
        json.dump(results_json, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
