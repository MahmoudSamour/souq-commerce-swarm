"""
SOUQ // Munadi Herald (Discovery & Registry Distribution Officer)
Coordinates public endpoint verification, AI crawler indexing, and MCP registry visibility.
"""

import urllib.request
import urllib.parse
import json
import time
from typing import Dict, Any, List

KOYEB_PUBLIC_URL = "https://written-emera-arapython-bf7436a4.apps.mistral.run"


class MunadiHerald:
    """
    Sovereign Distribution Officer for SOUQ Swarm.
    Verifies live endpoints, optimizes machine manifests, and broadcasts presence to AI aggregators.
    """

    def __init__(self, base_url: str = KOYEB_PUBLIC_URL):
        self.base_url = base_url.rstrip("/")

    def verify_public_discovery_endpoints(self) -> Dict[str, Any]:
        """
        Audits all public endpoints required for machine discovery.
        """
        endpoints = [
            ("/", "text/html"),
            ("/health", "application/json"),
            ("/api/catalog", "application/json"),
            ("/llms.txt", "text/plain"),
            ("/.well-known/mcp.json", "application/json"),
            ("/sitemap.xml", "application/xml"),
            ("/robots.txt", "text/plain"),
        ]

        results = []
        for path, expected_type in endpoints:
            url = f"{self.base_url}{path}"
            start_t = time.time()
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "MunadiHerald/1.0 (SOUQ-Discovery-Audit)"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    status = resp.status
                    content_type = resp.headers.get("Content-Type", "")
                    latency_ms = int((time.time() - start_t) * 1000)
                    results.append({
                        "path": path,
                        "status": status,
                        "healthy": 200 <= status < 300,
                        "latency_ms": latency_ms,
                        "content_type": content_type
                    })
            except Exception as e:
                results.append({
                    "path": path,
                    "status": "ERROR",
                    "healthy": False,
                    "latency_ms": int((time.time() - start_t) * 1000),
                    "error": str(e)
                })

        all_healthy = all(r["healthy"] for r in results)
        return {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "overall_status": "ONLINE_AND_DISCOVERABLE" if all_healthy else "DEGRADED",
            "endpoints": results
        }

    def generate_registry_packages(self) -> Dict[str, Any]:
        """
        Returns registry-ready configs and instructions for external directories.
        """
        return {
            "smithery": {
                "registry": "https://smithery.ai",
                "manifest_path": "smithery.yaml",
                "public_endpoint": f"{self.base_url}/api/catalog",
                "transport": "HTTP/REST x402 + SSE"
            },
            "glama": {
                "registry": "https://glama.ai/mcp/servers",
                "protocol": "Model Context Protocol (MCP)",
                "manifest": f"{self.base_url}/.well-known/mcp.json"
            },
            "mcp_so": {
                "registry": "https://mcp.so",
                "catalog": f"{self.base_url}/api/catalog"
            },
            "llms_txt": {
                "specification": "https://llmstxt.org",
                "url": f"{self.base_url}/llms.txt"
            }
        }


if __name__ == "__main__":
    herald = MunadiHerald()
    print("Auditing SOUQ Public Endpoints...")
    audit = herald.verify_public_discovery_endpoints()
    print(json.dumps(audit, indent=2))
