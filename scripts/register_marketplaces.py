#!/usr/bin/env python3
"""
SOUQ // Automated Marketplace & MCP Registry Reachability Verifier
Checks live listing reachability across Official MCP Registry, PyPI, npm,
Smithery, Glama, and x402 Bazaar.
"""

import argparse
import json
import sys
import time
from typing import Any, Dict, List
import requests

MARKETPLACE_TARGETS: List[Dict[str, str]] = [
    {
        "name": "Official MCP Registry",
        "key": "official_mcp_registry",
        "url": "https://registry.modelcontextprotocol.io/v0/servers?search=souq",
    },
    {
        "name": "PyPI (souq-mcp)",
        "key": "pypi",
        "url": "https://pypi.org/pypi/souq-mcp/json",
    },
    {
        "name": "npm (souq-mcp)",
        "key": "npm",
        "url": "https://registry.npmjs.org/souq-mcp",
    },
    {
        "name": "Smithery MCP Directory",
        "key": "smithery",
        "url": "https://smithery.ai/server/souq-mcp",
    },
    {
        "name": "Glama MCP Directory",
        "key": "glama",
        "url": "https://glama.ai/mcp/servers?query=souq",
    },
    {
        "name": "x402 Bazaar Directory",
        "key": "x402_bazaar",
        "url": "https://www.x402.org/ecosystem",
    },
]


def verify_marketplaces(
    timeout_s: float = 8.0,
    offline: bool = False,
    http_get=None,
) -> Dict[str, Any]:
    """Probes all configured MCP / package / x402 directories and returns a structured status report."""
    getter = http_get or requests.get
    results: List[Dict[str, Any]] = []
    headers = {"User-Agent": "SOUQ-Marketplace-Verifier/1.0"}

    for target in MARKETPLACE_TARGETS:
        if offline:
            results.append({
                "key": target["key"],
                "name": target["name"],
                "url": target["url"],
                "reachable": None,
                "status_code": None,
                "status": "SKIPPED_OFFLINE",
            })
            continue

        t0 = time.time()
        try:
            resp = getter(target["url"], headers=headers, timeout=timeout_s, allow_redirects=True)
            code = int(getattr(resp, "status_code", 0))
            reachable = 200 <= code < 400
            results.append({
                "key": target["key"],
                "name": target["name"],
                "url": target["url"],
                "reachable": reachable,
                "status_code": code,
                "latency_ms": int((time.time() - t0) * 1000),
                "status": "LIVE" if reachable else f"HTTP_{code}",
            })
        except Exception as exc:
            results.append({
                "key": target["key"],
                "name": target["name"],
                "url": target["url"],
                "reachable": False,
                "status_code": None,
                "latency_ms": int((time.time() - t0) * 1000),
                "status": "UNREACHABLE",
                "error": str(exc)[:200],
            })

    live_count = sum(1 for r in results if r.get("reachable") is True)
    return {
        "checked_at_epoch": int(time.time()),
        "total_directories": len(results),
        "live_count": live_count,
        "offline_mode": offline,
        "directories": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SOUQ listings across MCP, PyPI, npm, and x402 directories.")
    parser.add_argument("--timeout", type=float, default=8.0, help="HTTP timeout per directory in seconds")
    parser.add_argument("--offline", action="store_true", help="Skip live HTTP calls and emit target manifest")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON output")
    args = parser.parse_args()

    report = verify_marketplaces(timeout_s=args.timeout, offline=args.offline)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"SOUQ Marketplace Reachability ({report['live_count']}/{report['total_directories']} LIVE)")
        for item in report["directories"]:
            print(f" - [{item['status']}] {item['name']}: {item['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
