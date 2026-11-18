"""
SOUQ // Munadi Herald (Discovery & Registry Distribution Officer)
Coordinates public endpoint verification, AI crawler indexing, and Agent Engine Optimization (AEO).
"""

import urllib.error
import urllib.parse
import urllib.request
import json
import time
from typing import Any, Dict, List, Optional, Set, Tuple

KOYEB_PUBLIC_URL = "https://written-emera-arapython-bf7436a4.apps.mistral.run"


class MunadiHerald:
    """
    Sovereign Distribution Officer for SOUQ Swarm.
    Verifies live endpoints, optimizes machine manifests, and broadcasts presence to AI aggregators.
    """

    def __init__(self, base_url: str = KOYEB_PUBLIC_URL):
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _validate_endpoint_response(
        path: str,
        expected_type: str,
        allowed_statuses: Set[int],
        status: int,
        content_type: str,
        body_text: str,
    ) -> Tuple[bool, Optional[str]]:
        if status not in allowed_statuses:
            return False, f"Unexpected HTTP status {status} (expected {sorted(allowed_statuses)})"

        media_type = (content_type or "").split(";")[0].strip().lower()
        stripped = (body_text or "").lstrip()
        is_html_payload = media_type == "text/html" or stripped.lower().startswith(("<!doctype html", "<html"))

        if expected_type != "text/html" and is_html_payload:
            return False, f"Unexpected HTML payload returned for {expected_type} endpoint"

        if expected_type == "application/json":
            if path == "/mcp" and status in (200, 406) and media_type == "text/event-stream":
                if not stripped:
                    return False, "Empty SSE MCP discovery response body"
                return True, None

            if media_type != "application/json" and not media_type.endswith("+json"):
                return False, f"Content-Type mismatch: expected application/json, got '{media_type or 'none'}'"

            if not stripped:
                return False, "Empty JSON response body"

            try:
                parsed = json.loads(body_text)
            except Exception as exc:
                return False, f"Invalid JSON response body: {exc}"

            if path == "/mcp" and status == 405 and not isinstance(parsed, dict):
                return False, "Expected JSON object payload on 405 /mcp response"
            if not isinstance(parsed, (dict, list)):
                return False, "Expected JSON object or array payload"
            return True, None

        if expected_type == "application/xml":
            if media_type not in ("application/xml", "text/xml"):
                return False, f"Content-Type mismatch: expected application/xml, got '{media_type or 'none'}'"
            if not stripped:
                return False, "Empty XML response body"
            return True, None

        if media_type != expected_type:
            return False, f"Content-Type mismatch: expected {expected_type}, got '{media_type or 'none'}'"
        if not stripped:
            return False, f"Empty {expected_type} response body"
        return True, None

    def verify_public_discovery_endpoints(self) -> Dict[str, Any]:
        """
        Audits all public endpoints required for machine discovery.
        """
        endpoints: List[Tuple[str, str, Set[int]]] = [
            ("/", "text/html", {200}),
            ("/health", "application/json", {200}),
            ("/api/catalog", "application/json", {200}),
            ("/api/products", "application/json", {200}),
            ("/mcp", "application/json", {200, 405, 406}),
            ("/llms.txt", "text/plain", {200}),
            ("/llms-full.txt", "text/plain", {200}),
            ("/.well-known/mcp.json", "application/json", {200}),
            ("/.well-known/agent-card.json", "application/json", {200}),
            ("/.well-known/agent.json", "application/json", {200}),
            ("/openapi.json", "application/json", {200}),
            ("/sitemap.xml", "application/xml", {200}),
            ("/robots.txt", "text/plain", {200}),
        ]

        results = []
        for path, expected_type, allowed_statuses in endpoints:
            url = f"{self.base_url}{path}"
            start_t = time.time()
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "MunadiHerald/1.0 (SOUQ-Discovery-Audit)"},
                )
                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        status = resp.status
                        content_type = resp.headers.get("Content-Type", "")
                        body_bytes = resp.read()
                except urllib.error.HTTPError as http_err:
                    status = http_err.code
                    content_type = http_err.headers.get("Content-Type", "") if http_err.headers else ""
                    try:
                        body_bytes = http_err.read()
                    except Exception:
                        body_bytes = b""

                body_text = body_bytes.decode("utf-8", errors="replace")
                latency_ms = int((time.time() - start_t) * 1000)
                healthy, err_reason = self._validate_endpoint_response(
                    path=path,
                    expected_type=expected_type,
                    allowed_statuses=allowed_statuses,
                    status=status,
                    content_type=content_type,
                    body_text=body_text,
                )
                entry: Dict[str, Any] = {
                    "path": path,
                    "status": status,
                    "healthy": healthy,
                    "latency_ms": latency_ms,
                    "content_type": content_type,
                }
                if err_reason:
                    entry["error"] = err_reason
                results.append(entry)
            except Exception as e:
                results.append({
                    "path": path,
                    "status": "ERROR",
                    "healthy": False,
                    "latency_ms": int((time.time() - start_t) * 1000),
                    "error": str(e),
                })

        all_healthy = all(r["healthy"] for r in results)
        return {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "overall_status": "ONLINE_AND_DISCOVERABLE" if all_healthy else "DEGRADED",
            "endpoints": results
        }

    def broadcast_to_indexnow(self) -> Dict[str, Any]:
        """
        Broadcasts all discovery URLs to IndexNow (Microsoft Bing / IndexNow search network).
        """
        host = urllib.parse.urlparse(self.base_url).netloc
        urls = [
            f"{self.base_url}/",
            f"{self.base_url}/llms.txt",
            f"{self.base_url}/llms-full.txt",
            f"{self.base_url}/.well-known/mcp.json",
            f"{self.base_url}/.well-known/agent-card.json",
            f"{self.base_url}/openapi.json",
            f"{self.base_url}/api/catalog"
        ]

        payload = {
            "host": host,
            "key": "souq-agent-commerce-index-key-2026",
            "keyLocation": f"{self.base_url}/souq-agent-commerce-index-key-2026.txt",
            "urlList": urls
        }

        try:
            req = urllib.request.Request(
                "https://api.indexnow.org/indexnow",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "SOUQ-Herald/1.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                http_code = getattr(resp, "status", None) or resp.getcode()
                if http_code in (200, 202):
                    return {
                        "status": "success",
                        "http_code": http_code,
                        "urls_submitted": len(urls),
                        "network": "IndexNow (Bing, Yandex, Seznam)"
                    }
                return {
                    "status": "error",
                    "http_code": http_code,
                    "error": f"Unexpected IndexNow HTTP status {http_code}",
                    "urls_submitted": 0,
                }
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace").strip()
            except Exception:
                pass
            return {
                "status": "error",
                "http_code": e.code,
                "error": f"HTTP {e.code}: {err_body or e.reason}",
                "urls_submitted": 0,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "urls_submitted": 0,
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
            "a2a_agent_card": {
                "specification": "https://a2a-protocol.org",
                "endpoint": f"{self.base_url}/.well-known/agent-card.json"
            },
            "openapi": {
                "spec_url": f"{self.base_url}/openapi.json"
            },
            "llms_txt": {
                "specification": "https://llmstxt.org",
                "url": f"{self.base_url}/llms.txt",
                "full_url": f"{self.base_url}/llms-full.txt"
            }
        }


if __name__ == "__main__":
    herald = MunadiHerald()
    print("📢 Auditing SOUQ Public Endpoints...")
    audit = herald.verify_public_discovery_endpoints()
    print(json.dumps(audit, indent=2))
    print("\n🌐 Broadcasting to IndexNow Search Network...")
    ping_res = herald.broadcast_to_indexnow()
    print(json.dumps(ping_res, indent=2))
