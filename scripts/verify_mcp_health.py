"""FastMCP service health verification script."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request


def check_health(url: str, timeout: int = 30) -> bool:
    start_time = time.time()
    print(f"Polling FastMCP endpoint: {url} (max {timeout}s)...")

    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KF-HealthCheck"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status in (200, 204, 307):
                    print("Service healthy and reachable.")
                    return True
        except Exception:
            time.sleep(2)

    print("Timed out waiting for FastMCP service.")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify FastMCP SSE service health")
    parser.add_argument("--url", default="http://localhost:8000/sse", help="Target URL to poll")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    args = parser.parse_args()

    healthy = check_health(args.url, args.timeout)
    sys.exit(0 if healthy else 1)
