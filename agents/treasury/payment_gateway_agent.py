"""
SOUQ // Payment Gateway & Service Linker Agent
Audits Polar.sh (card payouts, products, webhooks) and Base L2 USDC (x402),
safely syncs active products with live service readiness, and verifies the live
Koyeb commerce endpoint on a fixed schedule.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.treasury.polar_adapter import POLAR_PRODUCTS

POLAR_API = "https://api.polar.sh/v1"
DEFAULT_SERVICE_URL = "https://written-emera-arapython-bf7436a4.apps.mistral.run"
STATUS_LOG_PATH = REPO_ROOT / "logs" / "payment_gateway_status.json"


def _polar_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "SOUQ-PaymentGatewayAgent/1.0",
        "Content-Type": "application/json",
    }


def _sync_polar_products(headers: Dict[str, str], paid_routes_ready: bool) -> Dict[str, Any]:
    """Ensure active Polar products match live route readiness and asset availability."""
    r = requests.get(f"{POLAR_API}/products/", headers=headers, timeout=15)
    r.raise_for_status()
    by_id = {p["id"]: p for p in r.json().get("items", [])}

    synced: List[Dict[str, Any]] = []
    for sku, meta in POLAR_PRODUCTS.items():
        pid = os.getenv(meta["product_id_env"], "").strip()
        if not pid or pid not in by_id:
            synced.append({"sku": sku, "status": "not_linked_in_env"})
            continue

        prod = by_id[pid]
        asset_env = meta.get("asset_url_env")
        has_asset = True if not asset_env else bool(os.getenv(asset_env, "").strip())
        should_archive = (not has_asset) or (not paid_routes_ready)

        if prod.get("is_archived") != should_archive:
            patch = requests.patch(
                f"{POLAR_API}/products/{pid}",
                headers=headers,
                json={"is_archived": should_archive},
                timeout=15,
            )
            patch.raise_for_status()
            if not paid_routes_ready:
                action = "paused_live_routes_not_ready"
            elif not has_asset:
                action = "archived_missing_asset"
            else:
                action = "activated"
        else:
            if not paid_routes_ready:
                action = "paused_live_routes_not_ready"
            elif not has_asset:
                action = "archived_missing_asset"
            else:
                action = "active"

        synced.append({"sku": sku, "product_id": pid, "state": action})
    return {"products": synced}


def _check_polar_webhook(headers: Dict[str, str], target_url: str) -> Dict[str, Any]:
    """Verify the Polar webhook endpoint points to the live SOUQ service."""
    r = requests.get(f"{POLAR_API}/webhooks/endpoints", headers=headers, timeout=15)
    r.raise_for_status()
    for ep in r.json().get("items", []):
        if ep.get("url", "").rstrip("/") == target_url.rstrip("/"):
            return {"configured": True, "endpoint_id": ep.get("id"), "enabled": ep.get("enabled", True)}
    return {"configured": False, "expected_url": target_url}


def _check_live_service(service_url: str) -> Dict[str, Any]:
    """Ping live Koyeb service health, product catalog, and Polar webhook route."""
    result: Dict[str, Any] = {"online": False, "routes": {}}
    try:
        r_health = requests.get(f"{service_url}/health", timeout=15)
        result["status_code"] = r_health.status_code
        result["online"] = r_health.status_code == 200

        r_prods = requests.get(f"{service_url}/api/products", timeout=15)
        result["routes"]["/api/products"] = r_prods.status_code

        # POST /webhooks/polar with empty body: 401 = route live & secret set; 404 = stale deploy; 503 = secret missing
        r_hook = requests.post(f"{service_url}/webhooks/polar", data=b"{}", timeout=15)
        result["routes"]["/webhooks/polar"] = r_hook.status_code

        r_claim = requests.get(f"{service_url}/api/checkout/claim", timeout=15)
        result["routes"]["/api/checkout/claim"] = r_claim.status_code

        result["paid_routes_ready"] = (
            r_prods.status_code == 200
            and r_hook.status_code in (400, 401)
            and r_claim.status_code != 404
        )
        return result
    except requests.RequestException as exc:
        result["error"] = str(exc)
        return result


def run_gateway_audit() -> Dict[str, Any]:
    """Run full Polar + Base USDC + live Koyeb service audit and persist status."""
    load_dotenv(REPO_ROOT / ".env", override=True)

    token = os.getenv("POLAR_ACCESS_TOKEN", "").strip()
    org_id = os.getenv("POLAR_ORGANIZATION_ID", "").strip()
    webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "").strip()
    service_url = os.getenv("SOUQ_PUBLIC_URL", DEFAULT_SERVICE_URL).rstrip("/")
    wallet_addr = (
        os.getenv("BASE_RECIPIENT_WALLET_ADDRESS", "").strip()
        or os.getenv("WALLET_ADDRESS", "").strip()
    )

    report: Dict[str, Any] = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "service_url": service_url,
        "polar": {"configured": bool(token and org_id and webhook_secret)},
        "x402_usdc": {
            "wallet_set": bool(wallet_addr),
            "pepper_set": bool(os.getenv("SOUQ_API_KEY_PEPPER", "").strip()),
            "receipt_key_set": bool(os.getenv("SOUQ_RECEIPT_SIGNING_KEY", "").strip()),
        },
        "live_service": _check_live_service(service_url),
        "issues": [],
        "warnings": [],
    }

    if not os.getenv("DATABASE_URL", "").strip():
        report["warnings"].append("database_url_missing_ephemeral_duckdb")

    if token and org_id:
        headers = _polar_headers(token)
        org_res = requests.get(f"{POLAR_API}/organizations/{org_id}", headers=headers, timeout=15)
        if org_res.status_code == 200:
            org = org_res.json()
            report["polar"]["status"] = org.get("status")
            report["polar"]["payouts_ready"] = bool(org.get("payouts_enabled", False))
            if not report["polar"]["payouts_ready"]:
                report["warnings"].append("polar_payouts_disabled")
        else:
            report["issues"].append(f"polar_org_http_{org_res.status_code}")

        report["polar"].update(_sync_polar_products(headers, bool(report["live_service"].get("paid_routes_ready"))))
        webhook_info = _check_polar_webhook(headers, f"{service_url}/webhooks/polar")
        report["polar"]["webhook"] = webhook_info
        if not webhook_info.get("configured"):
            report["issues"].append("polar_webhook_missing")
    else:
        report["issues"].append("polar_credentials_missing")

    if not report["live_service"].get("online"):
        report["issues"].append("live_service_unreachable")
    elif not report["live_service"].get("paid_routes_ready"):
        report["issues"].append("live_paid_routes_not_ready")

    STATUS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_LOG_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    report = run_gateway_audit()
    issues = report["issues"]
    warnings = report.get("warnings", [])
    active_count = sum(1 for p in report["polar"].get("products", []) if p.get("state") == "active")
    print(
        f"[SOUQ PaymentGatewayAgent] service_online={report['live_service'].get('online')} "
        f"polar_active_products={active_count} issues={issues or 'none'} warnings={warnings or 'none'}"
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
