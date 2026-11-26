"""
SOUQ // Two-Sided AI Agent & Creator Marketplace Registry (Sayrafi + Amin + Sayf)
Allows external AI agents and human developers to list HTTPS tools/APIs on SOUQ,
executes calls safely behind Sayf's prompt-injection/secret firewall, and splits
revenue atomically (80% Seller / 20% SOUQ platform profit).
"""

import os
import re
import hmac
import json
import math
import socket
import hashlib
import secrets
import logging
import ipaddress
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from agents.treasury.db_backend import (
    resolve_db_target,
    db_transaction,
    ensure_parent_dir,
    load_souq_env,
    get_ephemeral_test_pepper,
)
from agents.production.cyber_defense_vault import (
    PromptInjectionFirewall,
    SecretLeakScanner,
)
from agents.treasury.wallet_gate import WalletEnforcementGate, WalletGateError

load_souq_env()
logger = logging.getLogger("souq.marketplace_registry")

PLATFORM_COMMISSION_RATE = 0.20  # 20% SOUQ commission, 80% Seller share
MIN_PRICE_USD = 0.005
MAX_PRICE_USD = 5.00
MIN_PAYOUT_USD = 10.00
MAX_CONSECUTIVE_FAILURES = 3

EVM_WALLET_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
SLUG_SANITIZE_RE = re.compile(r"[^a-z0-9_]+")

FORBIDDEN_CONTENT_KEYWORDS = (
    "steal credentials",
    "phishing kit",
    "ddos attack",
    "ransomware",
    "bypass captcha",
    "credit card dump",
    "carding",
    "doxxing",
    "keylogger",
    "exploit zero-day",
    "malware payload",
)


def normalize_tool_id(raw_slug: str) -> str:
    """Normalizes any user-supplied tool slug into a safe `ext_<slug>` identifier."""
    cleaned = (raw_slug or "").strip().lower()
    if cleaned.startswith("ext_"):
        cleaned = cleaned[4:]
    cleaned = SLUG_SANITIZE_RE.sub("_", cleaned).strip("_")
    cleaned = cleaned[:40]
    return f"ext_{cleaned}" if cleaned else ""


def validate_public_https_url(raw_url: str, resolve_dns: bool = True) -> Tuple[bool, str]:
    """
    Amin SSRF Guard: Ensures seller endpoint URLs are strict public HTTPS URLs
    and never resolve to loopback, private, link-local, or reserved IP ranges.
    """
    if not raw_url or not isinstance(raw_url, str):
        return False, "Missing endpoint_url"
    url = raw_url.strip()
    if len(url) > 512:
        return False, "endpoint_url exceeds 512 characters"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        return False, "endpoint_url must use https://"
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return False, "endpoint_url missing hostname"
    if host in ("localhost", "localhost.localdomain") or host.endswith((".local", ".internal", ".localhost")):
        return False, "SSRF blocked: local/internal hostnames are prohibited"
    if parsed.username or parsed.password:
        return False, "endpoint_url must not contain embedded credentials"

    def _is_unsafe_ip(ip_str: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            return (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            )
        except ValueError:
            return True

    # Direct IP literal check
    try:
        ipaddress.ip_address(host)
        if _is_unsafe_ip(host):
            return False, f"SSRF blocked: private or reserved IP '{host}'"
        return True, "OK"
    except ValueError:
        pass

    if "." not in host:
        return False, "endpoint_url hostname must be a public FQDN"

    if resolve_dns:
        try:
            infos = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
            if not infos:
                return False, f"Unresolvable host '{host}'"
            for info in infos:
                ip_str = info[4][0]
                if _is_unsafe_ip(ip_str):
                    return False, f"SSRF blocked: host '{host}' resolved to private IP '{ip_str}'"
        except socket.gaierror:
            return False, f"Unresolvable host '{host}'"
        except Exception as exc:
            return False, f"DNS resolution check failed: {exc}"

    return True, "OK"


class MarketplaceRegistry:
    """
    Two-Sided SOUQ Marketplace engine:
      - Seller & tool onboarding with Amin safety/SSRF validation
      - Safe proxy execution guarded by Sayf prompt-injection & secret-leak scanners
      - Atomic 80% Seller / 20% SOUQ revenue splitting & payout ledger
    """

    def __init__(
        self,
        db_path: str = "data/souq_treasury_lake.duckdb",
        commission_rate: float = PLATFORM_COMMISSION_RATE,
        resolve_dns: bool = True,
        payout_ledger_path: Optional[str] = None,
    ):
        self.db_path = db_path
        self.db_target, self.is_postgres = resolve_db_target(db_path)
        if not self.is_postgres:
            ensure_parent_dir(self.db_target)
        if payout_ledger_path is not None:
            self.payout_ledger_path = payout_ledger_path
        elif os.getenv("SOUQ_PAYOUT_GATE_LEDGER"):
            self.payout_ledger_path = os.getenv("SOUQ_PAYOUT_GATE_LEDGER")
        elif not self.is_postgres:
            self.payout_ledger_path = os.path.join(
                os.path.dirname(os.path.abspath(self.db_target)),
                "payout_gate_ledger.json",
            )
        else:
            self.payout_ledger_path = "data/payout_gate_ledger.json"

        self.commission_rate = float(commission_rate)
        self.resolve_dns = resolve_dns
        self._secret_pepper = (
            os.getenv("SOUQ_HASH_PEPPER")
            or os.getenv("SOUQ_API_KEY_PEPPER")
            or get_ephemeral_test_pepper()
        )
        self.prompt_firewall = PromptInjectionFirewall()
        self.secret_scanner = SecretLeakScanner()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "SOUQ-Marketplace-Proxy/1.0 (+https://written-emera-arapython-bf7436a4.apps.mistral.run)",
            "Accept": "application/json",
        })
        self._init_db()

    def _hash_seller_key(self, raw_key: str) -> str:
        return hmac.new(
            self._secret_pepper.encode("utf-8"),
            raw_key.strip().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _init_db(self) -> None:
        with db_transaction(self.db_target, read_only=False) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_sellers (
                    seller_id VARCHAR PRIMARY KEY,
                    seller_key_hash VARCHAR NOT NULL UNIQUE,
                    seller_name VARCHAR NOT NULL,
                    payout_wallet_base VARCHAR NOT NULL,
                    contact_handle VARCHAR DEFAULT '',
                    earned_balance_usd DECIMAL(18, 6) NOT NULL DEFAULT 0.0,
                    total_earned_usd DECIMAL(18, 6) NOT NULL DEFAULT 0.0,
                    total_paid_out_usd DECIMAL(18, 6) NOT NULL DEFAULT 0.0,
                    status VARCHAR NOT NULL DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_listings (
                    tool_id VARCHAR PRIMARY KEY,
                    seller_id VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    description VARCHAR NOT NULL,
                    category VARCHAR NOT NULL DEFAULT 'External Agent Tool',
                    price_usdc DECIMAL(18, 6) NOT NULL,
                    endpoint_url VARCHAR NOT NULL,
                    input_schema_json VARCHAR NOT NULL DEFAULT '{}',
                    calls_count INTEGER NOT NULL DEFAULT 0,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    consecutive_failures INTEGER NOT NULL DEFAULT 0,
                    featured BOOLEAN NOT NULL DEFAULT FALSE,
                    status VARCHAR NOT NULL DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_settlements (
                    settlement_id VARCHAR PRIMARY KEY,
                    tool_id VARCHAR NOT NULL,
                    seller_id VARCHAR NOT NULL,
                    gross_amount_usd DECIMAL(18, 6) NOT NULL,
                    platform_fee_usd DECIMAL(18, 6) NOT NULL,
                    seller_earning_usd DECIMAL(18, 6) NOT NULL,
                    payment_rail VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_payouts (
                    payout_id VARCHAR PRIMARY KEY,
                    seller_id VARCHAR NOT NULL,
                    amount_usd DECIMAL(18, 6) NOT NULL,
                    payout_wallet_base VARCHAR NOT NULL,
                    status VARCHAR NOT NULL DEFAULT 'QUEUED',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def _amin_screen_listing(
        self,
        title: str,
        description: str,
        endpoint_url: str,
        payout_wallet_base: str,
        price_usdc: float,
    ) -> Tuple[bool, str]:
        """Runs Amin Compliance & Safety Gate before a listing can go live."""
        if not title or len(title.strip()) < 3 or len(title.strip()) > 100:
            return False, "title must be between 3 and 100 characters"
        if not description or len(description.strip()) < 10 or len(description.strip()) > 600:
            return False, "description must be between 10 and 600 characters"
        if not EVM_WALLET_RE.match((payout_wallet_base or "").strip()):
            return False, "payout_wallet_base must be a valid Base L2 EVM address (0x... 40 hex chars)"
        if not math.isfinite(price_usdc) or price_usdc < MIN_PRICE_USD or price_usdc > MAX_PRICE_USD:
            return False, f"price_usdc must be between ${MIN_PRICE_USD:.3f} and ${MAX_PRICE_USD:.2f}"

        combined = f"{title} {description}".lower()
        for bad in FORBIDDEN_CONTENT_KEYWORDS:
            if bad in combined:
                return False, f"Amin Compliance Rejected: prohibited capability '{bad}'"

        url_ok, url_reason = validate_public_https_url(endpoint_url, resolve_dns=self.resolve_dns)
        if not url_ok:
            return False, url_reason
        return True, "CLEARED"

    def register_seller_and_listing(
        self,
        tool_slug: str,
        title: str,
        description: str,
        endpoint_url: str,
        price_usdc: float,
        payout_wallet_base: str,
        seller_name: str = "External Agent Builder",
        category: str = "External Agent Tool",
        contact_handle: str = "",
        input_schema: Optional[Dict[str, Any]] = None,
        existing_seller_key: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Onboards an external seller (human developer or autonomous AI agent) and
        publishes their tool into the SOUQ Marketplace after passing Amin's safety gate.
        """
        tool_id = normalize_tool_id(tool_slug or title)
        if not tool_id or len(tool_id) < 7:
            return False, {"error": "Invalid tool_slug; use at least 3 alphanumeric characters."}

        try:
            price_val = round(float(price_usdc), 6)
        except (TypeError, ValueError):
            return False, {"error": "price_usdc must be a valid number."}

        ok_amin, amin_reason = self._amin_screen_listing(
            title=title,
            description=description,
            endpoint_url=endpoint_url,
            payout_wallet_base=payout_wallet_base,
            price_usdc=price_val,
        )
        if not ok_amin:
            return False, {"error": "Amin Compliance Gate Rejected", "reason": amin_reason}

        schema_str = json.dumps(input_schema if isinstance(input_schema, dict) else {"type": "object"})
        now = datetime.now(timezone.utc)
        raw_seller_key: Optional[str] = None

        with db_transaction(self.db_target, read_only=False) as con:
            dup = con.execute(
                "SELECT tool_id FROM marketplace_listings WHERE tool_id = ?",
                (tool_id,),
            ).fetchone()
            if dup:
                return False, {"error": "Tool ID already registered", "tool_id": tool_id}

            if existing_seller_key:
                sk_hash = self._hash_seller_key(existing_seller_key)
                srow = con.execute(
                    "SELECT seller_id, status FROM marketplace_sellers WHERE seller_key_hash = ?",
                    (sk_hash,),
                ).fetchone()
                if not srow:
                    return False, {"error": "Invalid X-Seller-Key"}
                if srow[1] != "ACTIVE":
                    return False, {"error": f"Seller account status is '{srow[1]}'"}
                seller_id = srow[0]
            else:
                seller_id = f"sel_{secrets.token_hex(6)}"
                raw_seller_key = f"souq_seller_{secrets.token_urlsafe(24)}"
                sk_hash = self._hash_seller_key(raw_seller_key)
                con.execute(
                    """
                    INSERT INTO marketplace_sellers (
                        seller_id, seller_key_hash, seller_name, payout_wallet_base,
                        contact_handle, earned_balance_usd, total_earned_usd,
                        total_paid_out_usd, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, 0.0, 0.0, 0.0, 'ACTIVE', ?)
                    """,
                    (
                        seller_id,
                        sk_hash,
                        (seller_name or "External Agent Builder").strip()[:80],
                        payout_wallet_base.strip(),
                        (contact_handle or "").strip()[:80],
                        now,
                    ),
                )

            con.execute(
                """
                INSERT INTO marketplace_listings (
                    tool_id, seller_id, title, description, category, price_usdc,
                    endpoint_url, input_schema_json, calls_count, success_count,
                    consecutive_failures, featured, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, FALSE, 'ACTIVE', ?)
                """,
                (
                    tool_id,
                    seller_id,
                    title.strip()[:100],
                    description.strip()[:600],
                    (category or "External Agent Tool").strip()[:60],
                    price_val,
                    endpoint_url.strip(),
                    schema_str,
                    now,
                ),
            )

        res: Dict[str, Any] = {
            "status": "LISTED_ACTIVE",
            "tool_id": tool_id,
            "seller_id": seller_id,
            "price_usdc": price_val,
            "revenue_split": {
                "seller_share_pct": int(round((1.0 - self.commission_rate) * 100)),
                "souq_commission_pct": int(round(self.commission_rate * 100)),
            },
            "amin_compliance": "CLEARED",
            "call_endpoint": "/api/tools/call",
            "mcp_tool_name": tool_id,
        }
        if raw_seller_key:
            res["seller_api_key"] = raw_seller_key
            res["note"] = "Save your seller_api_key securely (shown once). Pass via header X-Seller-Key for dashboard & payouts."
        return True, res

    def get_listing(self, tool_id: str) -> Optional[Dict[str, Any]]:
        if not tool_id or not tool_id.startswith("ext_"):
            return None
        with db_transaction(self.db_target, read_only=True) as con:
            row = con.execute(
                """
                SELECT l.tool_id, l.seller_id, s.seller_name, l.title, l.description,
                       l.category, l.price_usdc, l.endpoint_url, l.input_schema_json,
                       l.calls_count, l.success_count, l.featured, l.status
                FROM marketplace_listings l
                JOIN marketplace_sellers s ON l.seller_id = s.seller_id
                WHERE l.tool_id = ?
                """,
                (tool_id,),
            ).fetchone()
            if not row:
                return None
            try:
                schema = json.loads(row[8]) if row[8] else {"type": "object"}
            except Exception:
                schema = {"type": "object"}
            return {
                "tool_id": row[0],
                "seller_id": row[1],
                "seller_name": row[2],
                "title": row[3],
                "description": row[4],
                "category": row[5],
                "price_usdc": round(float(row[6]), 6),
                "endpoint_url": row[7],
                "input_schema": schema,
                "calls_count": int(row[9]),
                "success_count": int(row[10]),
                "featured": bool(row[11]),
                "status": row[12],
            }

    def list_active_listings(self) -> List[Dict[str, Any]]:
        with db_transaction(self.db_target, read_only=True) as con:
            rows = con.execute(
                """
                SELECT l.tool_id, l.seller_id, s.seller_name, l.title, l.description,
                       l.category, l.price_usdc, l.input_schema_json,
                       l.calls_count, l.success_count, l.featured
                FROM marketplace_listings l
                JOIN marketplace_sellers s ON l.seller_id = s.seller_id
                WHERE l.status = 'ACTIVE' AND s.status = 'ACTIVE'
                ORDER BY l.featured DESC, l.calls_count DESC, l.created_at DESC
                """
            ).fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                try:
                    schema = json.loads(r[7]) if r[7] else {"type": "object"}
                except Exception:
                    schema = {"type": "object"}
                out.append({
                    "tool_id": r[0],
                    "seller_id": r[1],
                    "seller_name": r[2],
                    "title": r[3],
                    "description": r[4],
                    "category": r[5],
                    "price_usdc": round(float(r[6]), 6),
                    "input_schema": schema,
                    "calls_count": int(r[8]),
                    "success_count": int(r[9]),
                    "featured": bool(r[10]),
                    "revenue_split": "80% seller / 20% SOUQ",
                })
            return out

    def execute_external_tool(
        self,
        tool_id: str,
        payload: Dict[str, Any],
        timeout_s: float = 4.0,
    ) -> Dict[str, Any]:
        """
        Safely proxies a paid tool call to an approved third-party seller endpoint
        and inspects the response via Sayf's prompt-injection & secret-leak firewall.
        """
        listing = self.get_listing(tool_id)
        if not listing or listing["status"] != "ACTIVE":
            return {"status": "error", "error": "marketplace_tool_unavailable", "tool_id": tool_id}

        url = listing["endpoint_url"]
        url_ok, url_reason = validate_public_https_url(url, resolve_dns=self.resolve_dns)
        if not url_ok:
            return {"status": "error", "error": "ssrf_blocked", "message": url_reason}

        # Strip sensitive SOUQ auth fields before forwarding to third-party seller
        clean_args = {
            k: v for k, v in (payload or {}).items()
            if k not in ("api_key", "payment_tx", "tx_hash", "payer_signature", "payer_challenge", "tool")
        }

        try:
            resp = self._session.post(
                url,
                json={"tool": tool_id, "arguments": clean_args},
                timeout=timeout_s,
                allow_redirects=False,
            )
        except requests.Timeout:
            self._record_failure(tool_id)
            return {
                "status": "upstream_unavailable",
                "error": "seller_timeout",
                "message": f"Seller endpoint timed out after {timeout_s}s; buyer not charged.",
            }
        except Exception as exc:
            self._record_failure(tool_id)
            return {
                "status": "upstream_unavailable",
                "error": "seller_unreachable",
                "message": f"Seller endpoint unreachable: {exc}",
            }

        if resp.status_code >= 400:
            self._record_failure(tool_id)
            return {
                "status": "upstream_unavailable",
                "error": "seller_http_error",
                "http_status": resp.status_code,
                "message": f"Seller returned HTTP {resp.status_code}; buyer not charged.",
            }

        try:
            seller_data = resp.json()
        except Exception:
            self._record_failure(tool_id)
            return {
                "status": "upstream_unavailable",
                "error": "seller_invalid_json",
                "message": "Seller endpoint returned non-JSON response; buyer not charged.",
            }

        # Sayf Firewall: Protect buyer agents against prompt injection or secret leaks from third-party sellers
        serialized = json.dumps(seller_data, ensure_ascii=False)[:12000]
        pi_check = self.prompt_firewall.scan_prompt(serialized, strict_mode=True)
        if (
            pi_check.get("verdict") == "ATTACK_DETECTED"
            or pi_check.get("is_safe_to_execute") is False
            or int(pi_check.get("findings_count", 0)) > 0
        ):
            self._record_failure(tool_id)
            return {
                "status": "error",
                "error": "sayf_firewall_blocked_seller_response",
                "message": "Sayf Cyber Sentinel blocked a suspicious prompt-injection payload from seller; buyer refunded.",
            }

        sec_check = self.secret_scanner.scan_for_secrets(serialized)
        if (
            sec_check.get("verdict") == "LEAKS_DETECTED"
            or sec_check.get("safe_to_publish") is False
            or int(sec_check.get("total_leaks", 0)) > 0
        ):
            self._record_failure(tool_id)
            return {
                "status": "error",
                "error": "sayf_firewall_blocked_secret_leak",
                "message": "Sayf Cyber Sentinel blocked an exposed credential/secret in seller output; buyer refunded.",
            }

        return {
            "status": "ok",
            "marketplace_tool": tool_id,
            "seller_id": listing["seller_id"],
            "seller_name": listing["seller_name"],
            "result": seller_data,
        }

    def _record_failure(self, tool_id: str) -> None:
        with db_transaction(self.db_target, read_only=False) as con:
            row = con.execute(
                """
                UPDATE marketplace_listings
                SET consecutive_failures = consecutive_failures + 1
                WHERE tool_id = ?
                RETURNING consecutive_failures
                """,
                (tool_id,),
            ).fetchone()
            if row and int(row[0]) >= MAX_CONSECUTIVE_FAILURES:
                con.execute(
                    "UPDATE marketplace_listings SET status = 'SUSPENDED' WHERE tool_id = ?",
                    (tool_id,),
                )
                logger.warning(f"Ra'is Auto-Prune: Suspended '{tool_id}' after {row[0]} consecutive failures.")

    def record_split_settlement(
        self,
        tool_id: str,
        gross_usd: float,
        payment_rail: str = "prepaid_api_key",
    ) -> Dict[str, Any]:
        """
        Atomically splits gross_usd into 20% SOUQ platform profit and 80% seller earning,
        and resets consecutive_failures on success.
        """
        gross = round(float(gross_usd), 6)
        platform_fee = round(gross * self.commission_rate, 6)
        seller_earning = round(gross - platform_fee, 6)
        settlement_id = f"mset_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc)

        with db_transaction(self.db_target, read_only=False) as con:
            row = con.execute(
                "SELECT seller_id FROM marketplace_listings WHERE tool_id = ?",
                (tool_id,),
            ).fetchone()
            if not row:
                return {"error": "Unknown marketplace tool", "tool_id": tool_id}
            seller_id = row[0]

            con.execute(
                """
                INSERT INTO marketplace_settlements (
                    settlement_id, tool_id, seller_id, gross_amount_usd,
                    platform_fee_usd, seller_earning_usd, payment_rail, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (settlement_id, tool_id, seller_id, gross, platform_fee, seller_earning, payment_rail, now),
            )
            con.execute(
                """
                UPDATE marketplace_sellers
                SET earned_balance_usd = earned_balance_usd + ?,
                    total_earned_usd = total_earned_usd + ?
                WHERE seller_id = ?
                """,
                (seller_earning, seller_earning, seller_id),
            )
            con.execute(
                """
                UPDATE marketplace_listings
                SET calls_count = calls_count + 1,
                    success_count = success_count + 1,
                    consecutive_failures = 0
                WHERE tool_id = ?
                """,
                (tool_id,),
            )

        return {
            "settlement_id": settlement_id,
            "tool_id": tool_id,
            "seller_id": seller_id,
            "gross_usd": gross,
            "souq_commission_usd": platform_fee,
            "seller_earning_usd": seller_earning,
            "payment_rail": payment_rail,
        }

    def get_seller_dashboard(self, seller_raw_key: str) -> Optional[Dict[str, Any]]:
        if not seller_raw_key or not seller_raw_key.strip():
            return None
        sk_hash = self._hash_seller_key(seller_raw_key)
        with db_transaction(self.db_target, read_only=True) as con:
            srow = con.execute(
                """
                SELECT seller_id, seller_name, payout_wallet_base, earned_balance_usd,
                       total_earned_usd, total_paid_out_usd, status, created_at
                FROM marketplace_sellers WHERE seller_key_hash = ?
                """,
                (sk_hash,),
            ).fetchone()
            if not srow:
                return None
            seller_id = srow[0]
            lrows = con.execute(
                """
                SELECT tool_id, title, price_usdc, calls_count, success_count, status, featured
                FROM marketplace_listings WHERE seller_id = ?
                ORDER BY created_at DESC
                """,
                (seller_id,),
            ).fetchall()
            return {
                "seller_id": seller_id,
                "seller_name": srow[1],
                "payout_wallet_base": srow[2],
                "earned_balance_usd": round(float(srow[3]), 6),
                "total_earned_usd": round(float(srow[4]), 6),
                "total_paid_out_usd": round(float(srow[5]), 6),
                "min_payout_usd": MIN_PAYOUT_USD,
                "payout_eligible": float(srow[3]) >= MIN_PAYOUT_USD,
                "status": srow[6],
                "listings": [
                    {
                        "tool_id": lr[0],
                        "title": lr[1],
                        "price_usdc": round(float(lr[2]), 6),
                        "calls_count": int(lr[3]),
                        "success_count": int(lr[4]),
                        "status": lr[5],
                        "featured": bool(lr[6]),
                    }
                    for lr in lrows
                ],
            }

    def request_seller_payout(
        self,
        seller_raw_key: str,
        amount_usd: Optional[float] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Queues a Base L2 USDC payout once seller balance meets the $10.00 minimum."""
        if not seller_raw_key or not seller_raw_key.strip():
            return False, {"error": "Missing X-Seller-Key"}
        sk_hash = self._hash_seller_key(seller_raw_key)
        now = datetime.now(timezone.utc)

        with db_transaction(self.db_target, read_only=False) as con:
            srow = con.execute(
                """
                SELECT seller_id, payout_wallet_base, earned_balance_usd, status
                FROM marketplace_sellers WHERE seller_key_hash = ?
                """,
                (sk_hash,),
            ).fetchone()
            if not srow:
                return False, {"error": "Invalid X-Seller-Key"}
            seller_id, wallet, bal_dec, status = srow
            if status != "ACTIVE":
                return False, {"error": f"Seller account status is '{status}'"}
            bal = round(float(bal_dec), 6)
            req_amt = bal if amount_usd is None else round(float(amount_usd), 6)

            if not math.isfinite(req_amt) or req_amt < MIN_PAYOUT_USD:
                return False, {
                    "error": "Minimum payout threshold not met",
                    "earned_balance_usd": bal,
                    "min_payout_usd": MIN_PAYOUT_USD,
                }
            if req_amt > bal:
                return False, {
                    "error": "Requested amount exceeds earned_balance_usd",
                    "earned_balance_usd": bal,
                    "requested_usd": req_amt,
                }

            payout_id = f"mpay_{secrets.token_hex(8)}"
            payout_gate = WalletEnforcementGate(
                allowed_recipients=[wallet],
                max_per_call_usd=float(os.getenv("SOUQ_PAYOUT_MAX_PER_CALL_USD", "250.0")),
                max_daily_spend_usd=float(os.getenv("SOUQ_PAYOUT_MAX_DAILY_USD", "1000.0")),
                ledger_path=self.payout_ledger_path,
            )
            # Enforce policy BEFORE deducting seller balance so a gate rejection never corrupts balances
            try:
                payout_gate.check_policy(
                    recipient=wallet,
                    amount_usdc=req_amt,
                    work_order_id=payout_id,
                )
            except WalletGateError as gate_err:
                return False, {"error": "WalletEnforcementGate rejected payout", "reason": str(gate_err)}

            updated = con.execute(
                """
                UPDATE marketplace_sellers
                SET earned_balance_usd = earned_balance_usd - ?,
                    total_paid_out_usd = total_paid_out_usd + ?
                WHERE seller_id = ? AND earned_balance_usd >= ?
                RETURNING earned_balance_usd
                """,
                (req_amt, req_amt, seller_id, req_amt),
            ).fetchone()
            if not updated:
                return False, {"error": "Concurrent payout conflict; retry."}

            con.execute(
                """
                INSERT INTO marketplace_payouts (
                    payout_id, seller_id, amount_usd, payout_wallet_base, status, created_at
                ) VALUES (?, ?, ?, ?, 'QUEUED', ?)
                """,
                (payout_id, seller_id, req_amt, wallet, now),
            )
            payout_gate.record_execution(
                recipient=wallet,
                amount_usdc=req_amt,
                work_order_id=payout_id,
            )
            remaining = round(float(updated[0]), 6)

        return True, {
            "status": "PAYOUT_QUEUED",
            "payout_id": payout_id,
            "seller_id": seller_id,
            "amount_usdc": req_amt,
            "payout_wallet_base": wallet,
            "chain": "Base L2 (USDC)",
            "remaining_balance_usd": remaining,
        }

    def get_marketplace_kpis(self) -> Dict[str, Any]:
        with db_transaction(self.db_target, read_only=True) as con:
            sellers = int(con.execute("SELECT COUNT(*) FROM marketplace_sellers WHERE status = 'ACTIVE'").fetchone()[0])
            listings = int(con.execute("SELECT COUNT(*) FROM marketplace_listings WHERE status = 'ACTIVE'").fetchone()[0])
            row = con.execute(
                """
                SELECT COUNT(*),
                       COALESCE(SUM(gross_amount_usd), 0.0),
                       COALESCE(SUM(platform_fee_usd), 0.0),
                       COALESCE(SUM(seller_earning_usd), 0.0)
                FROM marketplace_settlements
                """
            ).fetchone()
            return {
                "active_sellers": sellers,
                "active_listings": listings,
                "total_marketplace_calls": int(row[0]),
                "gross_volume_usd": round(float(row[1]), 6),
                "souq_commission_profit_usd": round(float(row[2]), 6),
                "seller_earnings_usd": round(float(row[3]), 6),
            }

    def audit_active_listings(self, timeout_s: float = 3.0) -> Dict[str, Any]:
        """Ra'is Health Sentinel: checks active external listings and suspends dead endpoints."""
        checked = 0
        suspended = 0
        with db_transaction(self.db_target, read_only=True) as con:
            rows = con.execute(
                "SELECT tool_id, endpoint_url FROM marketplace_listings WHERE status = 'ACTIVE'"
            ).fetchall()
        for tool_id, url in rows:
            checked += 1
            try:
                r = self._session.head(url, timeout=timeout_s, allow_redirects=False)
                if r.status_code >= 500:
                    self._record_failure(tool_id)
            except Exception:
                self._record_failure(tool_id)
            listing = self.get_listing(tool_id)
            if listing and listing["status"] == "SUSPENDED":
                suspended += 1
        return {"checked_listings": checked, "suspended_listings": suspended}
