"""
SOUQ // Polar.sh Merchant of Record & Automated License Delivery Adapter
Handles programmatic digital product creation, checkout link generation,
HMAC webhook verification, and automated prepaid API key / license fulfillment.
"""

import os
import hmac
import math
import time
import base64
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
import requests
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

from agents.treasury.api_key_ledger import APIKeyLedger
from agents.treasury.db_backend import (
    resolve_db_target,
    db_transaction,
    ensure_parent_dir,
)

load_dotenv("config/.env")

_CLAIMS_TTL_HOURS = 24


def _as_utc_datetime(val: Any) -> Optional[datetime]:
    if isinstance(val, datetime):
        return val.astimezone(timezone.utc) if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str) and val:
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


POLAR_PRODUCTS: Dict[str, Dict[str, Any]] = {
    "api_credit_pack_5": {
        "name": "SOUQ Prepaid API Credits ($5 Pack)",
        "description": "Prepaid $5.00 credit key (~250 tool calls across all 16+ MCP quant, token-compression, and security endpoints). Pass via X-API-Key or SOUQ_API_KEY.",
        "price_usd": 5.00,
        "credit_usd": 5.00,
        "kind": "api_credits",
        "product_id_env": "POLAR_PRODUCT_ID_CREDIT_5",
        "checkout_url_env": "POLAR_CHECKOUT_URL_CREDIT_5",
    },
    "api_credit_pack_15": {
        "name": "SOUQ Prepaid API Credits ($15 Pack + 20% Bonus)",
        "description": "Prepaid $18.00 API credit balance for $15.00 (~900 calls across all MCP endpoints). No wallet setup required.",
        "price_usd": 15.00,
        "credit_usd": 18.00,
        "kind": "api_credits",
        "product_id_env": "POLAR_PRODUCT_ID_CREDIT_15",
        "checkout_url_env": "POLAR_CHECKOUT_URL_CREDIT_15",
    },
    "crypto_5y_microstructure_lake": {
        "name": "5-Year High-Frequency Crypto Microstructure & Volatility Lake",
        "description": "Cleaned historical order-book imbalance, funding rates, and volatility datasets in Parquet + DuckDB format.",
        "price_usd": 49.00,
        "credit_usd": 0.0,
        "kind": "digital_data_lake",
        "product_id_env": "POLAR_PRODUCT_ID_DATA_LAKE",
        "checkout_url_env": "POLAR_CHECKOUT_URL_DATA_LAKE",
        "asset_url_env": "SOUQ_ASSET_URL_MICROSTRUCTURE",
    },
    "agent_guardrail_eval_suite": {
        "name": "Agent Guardrail & Prompt Injection Eval Suite (50K Pairs)",
        "description": "50,000 adversarial prompt-response stress-testing pairs for validating LLM & MCP firewalls.",
        "price_usd": 79.00,
        "credit_usd": 0.0,
        "kind": "digital_data_lake",
        "product_id_env": "POLAR_PRODUCT_ID_EVAL_SUITE",
        "checkout_url_env": "POLAR_CHECKOUT_URL_EVAL_SUITE",
        "asset_url_env": "SOUQ_ASSET_URL_GUARDRAILS",
    },
    "sovereign_swarm_boilerplate": {
        "name": "Sovereign Commerce Swarm Boilerplate (x402 + FastMCP + DuckDB)",
        "description": "Production template for monetizing AI tools via x402 Base USDC, Polar MoR, and prepaid API keys.",
        "price_usd": 39.00,
        "credit_usd": 0.0,
        "kind": "code_boilerplate",
        "product_id_env": "POLAR_PRODUCT_ID_BOILERPLATE",
        "checkout_url_env": "POLAR_CHECKOUT_URL_BOILERPLATE",
        "asset_url_env": "SOUQ_ASSET_URL_BOILERPLATE",
    },
}


class PolarAdapter:
    """
    Automates digital product vending via Polar.sh Merchant of Record API.
    Handles product creation, checkout session creation, Standard Webhooks verification,
    sealed one-time key claims, and automatic prepaid API key provisioning.
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        api_key_ledger: Optional[APIKeyLedger] = None,
        db_path: Optional[str] = None,
    ):
        self.access_token = access_token if access_token is not None else os.getenv("POLAR_ACCESS_TOKEN", "")
        self.webhook_secret = webhook_secret if webhook_secret is not None else os.getenv("POLAR_WEBHOOK_SECRET", "")
        self.base_url = os.getenv("POLAR_API_BASE_URL", "https://api.polar.sh/v1").rstrip("/")
        self.api_key_ledger = api_key_ledger

        resolved_path = db_path or (
            api_key_ledger.db_path if api_key_ledger is not None else os.getenv("SOUQ_DUCKDB_PATH", "data/souq_treasury_lake.duckdb")
        )
        self.db_path = resolved_path
        self.db_target, self.is_postgres = resolve_db_target(resolved_path)
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "SOUQ-Commerce-Swarm/1.0"
        }

        if db_path is not None or api_key_ledger is not None:
            if not self.is_postgres:
                ensure_parent_dir(self.db_target)
            self._init_db()

    @staticmethod
    def _ensure_claims_table(con: Any) -> None:
        con.execute("""
            CREATE TABLE IF NOT EXISTS polar_checkout_claims (
                claim_token VARCHAR PRIMARY KEY,
                order_id VARCHAR UNIQUE,
                sku VARCHAR,
                sealed_key VARCHAR,
                key_prefix VARCHAR,
                amount_cents INTEGER,
                claimed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            );
        """)

    def _init_db(self) -> None:
        with db_transaction(self.db_target, read_only=False) as con:
            self._ensure_claims_table(con)

    @staticmethod
    def _get_seal_pepper() -> bytes:
        pepper = os.getenv("SOUQ_API_KEY_PEPPER") or "souq_sovereign_pepper_2026"
        return pepper.encode("utf-8")

    @classmethod
    def _derive_stream_keys(cls, claim_token: str) -> Tuple[bytes, bytes]:
        pepper = cls._get_seal_pepper()
        token_bytes = claim_token.encode("utf-8")
        enc_key = hmac.new(pepper, b"souq_polar_seal_enc:" + token_bytes, hashlib.sha256).digest()
        mac_key = hmac.new(pepper, b"souq_polar_seal_mac:" + token_bytes, hashlib.sha256).digest()
        return enc_key, mac_key

    @staticmethod
    def _xor_keystream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
        blocks = bytearray()
        counter = 0
        while len(blocks) < length:
            blocks.extend(hmac.new(enc_key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest())
            counter += 1
        return bytes(blocks[:length])

    @staticmethod
    def _opaque_key_id(key_id: Optional[str], material: Optional[str]) -> Optional[str]:
        """
        Returns a non-secret identifier safe to echo back to Polar's webhook server.
        Never returns raw `souq_live_` material; hashes it instead.
        """
        if key_id and not str(key_id).startswith("souq_"):
            return str(key_id)
        if not material:
            return None
        return "kid_" + hashlib.sha256(str(material).encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _seal_key(cls, raw_key: str, claim_token: str) -> str:
        """Seals a raw API key using an HMAC-authenticated XOR stream keyed by SOUQ_API_KEY_PEPPER."""
        enc_key, mac_key = cls._derive_stream_keys(claim_token)
        nonce = secrets.token_bytes(16)
        plaintext = raw_key.encode("utf-8")
        keystream = cls._xor_keystream(enc_key, nonce, len(plaintext))
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, keystream))
        tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(nonce + ciphertext + tag).decode("ascii")

    @classmethod
    def _unseal_key(cls, sealed_blob: str, claim_token: str) -> Optional[str]:
        """Verifies HMAC tag and unseals a sealed API key."""
        try:
            raw = base64.urlsafe_b64decode(sealed_blob.encode("ascii"))
        except Exception:
            return None
        if len(raw) < 48:  # 16-byte nonce + 32-byte HMAC tag minimum
            return None
        nonce = raw[:16]
        tag = raw[-32:]
        ciphertext = raw[16:-32]
        enc_key, mac_key = cls._derive_stream_keys(claim_token)
        expected_tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            return None
        keystream = cls._xor_keystream(enc_key, nonce, len(ciphertext))
        plaintext = bytes(c ^ k for c, k in zip(ciphertext, keystream))
        try:
            return plaintext.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def list_catalog(self) -> Dict[str, Any]:
        """Returns Polar fiat SKUs alongside live configuration readiness."""
        catalog = {}
        for sku, spec in POLAR_PRODUCTS.items():
            checkout_override = os.getenv(spec["checkout_url_env"], "").strip()
            product_id = os.getenv(spec["product_id_env"], "").strip()
            checkout_ready = bool(checkout_override or (product_id and self.access_token))
            asset_env = spec.get("asset_url_env")
            asset_ready = True if not asset_env else bool(os.getenv(asset_env, "").strip())
            catalog[sku] = {
                "sku": sku,
                "name": spec["name"],
                "description": spec["description"],
                "price_usd": spec["price_usd"],
                "credit_usd": spec["credit_usd"],
                "kind": spec["kind"],
                "ready": bool(checkout_ready and asset_ready),
            }
        return catalog

    def create_digital_product(
        self,
        name: str,
        description: str,
        price_usd: float,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a recurring/one-time product on Polar.sh.
        """
        org_id = organization_id or os.getenv("POLAR_ORGANIZATION_ID", "")
        price_cents = int(round(price_usd * 100))

        payload = {
            "name": name,
            "description": description,
            "prices": [
                {
                    "type": "one_time",
                    "amount_type": "fixed",
                    "price_amount": price_cents,
                    "price_currency": "usd",
                }
            ],
            "organization_id": org_id,
        }

        if not self.access_token or self.access_token.startswith("polar_pat_pending"):
            return {
                "status": "configured_pending_key",
                "product_id": f"polar_prod_{abs(hash(name)) % 1000000}",
                "name": name,
                "price_usd": price_usd,
                "tax_handling": "Handled by Polar.sh MoR (Global VAT/GST/Sales Tax)",
            }

        try:
            resp = requests.post(f"{self.base_url}/products/", json=payload, headers=self.headers, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "status": "success",
                    "product_id": data.get("id"),
                    "name": name,
                    "price_usd": price_usd,
                }
            return {"status": "error", "code": resp.status_code, "details": resp.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _append_claim_to_url(success_url: str, claim_token: str) -> str:
        parsed = urllib.parse.urlsplit(success_url)
        query_params = [
            (k, v)
            for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            if k != "claim"
        ]
        query_params.append(("claim", claim_token))
        new_query = urllib.parse.urlencode(query_params)
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    def create_checkout_session(
        self,
        sku: str,
        success_url: str,
        customer_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates or resolves a Polar.sh hosted checkout URL for a catalog SKU.
        Gates downloadable SKUs on explicit asset URL configuration and embeds a one-time claim token.
        """
        spec = POLAR_PRODUCTS.get(sku)
        if not spec:
            return {"status": "error", "error": f"Unknown SKU '{sku}'", "available_skus": list(POLAR_PRODUCTS.keys())}

        asset_env = spec.get("asset_url_env")
        if asset_env and not os.getenv(asset_env, "").strip():
            return {
                "error": "sku_not_yet_configured",
                "status": "unavailable",
                "sku": sku,
                "message": f"Downloadable SKU '{sku}' requires {asset_env} to be configured.",
            }

        claim_token = secrets.token_urlsafe(24)
        augmented_success_url = self._append_claim_to_url(success_url, claim_token)

        direct_url = os.getenv(spec["checkout_url_env"], "").strip()
        if direct_url:
            return {
                "status": "ready",
                "sku": sku,
                "name": spec["name"],
                "price_usd": spec["price_usd"],
                "checkout_url": direct_url,
                "success_url": augmented_success_url,
                "claim_token": claim_token,
                "provider": "polar_sh_direct_link",
            }

        product_id = os.getenv(spec["product_id_env"], "").strip()
        if not product_id or not self.access_token:
            return {
                "status": "fiat_checkout_unavailable",
                "sku": sku,
                "price_usd": spec["price_usd"],
                "message": (
                    "Fiat checkout requires a valid Polar organization/product configuration on the server. "
                    "You can use Base USDC directly right now via /api/credits/topup or X-Payment-Tx."
                ),
            }

        payload: Dict[str, Any] = {
            "products": [product_id],
            "success_url": augmented_success_url,
            "metadata": {
                "souq_claim_token": claim_token,
                "sku": sku,
                "souq_sku": sku,
            },
        }
        if customer_email:
            payload["customer_email"] = customer_email

        try:
            resp = requests.post(f"{self.base_url}/checkouts/", json=payload, headers=self.headers, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "status": "ready",
                    "sku": sku,
                    "checkout_id": data.get("id"),
                    "checkout_url": data.get("url"),
                    "success_url": augmented_success_url,
                    "claim_token": claim_token,
                    "price_usd": spec["price_usd"],
                    "provider": "polar_sh",
                }
            return {
                "status": "error",
                "code": resp.status_code,
                "error": "Polar checkout creation failed",
                "details": resp.text[:400],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        headers: Dict[str, str],
    ) -> bool:
        """
        Verifies Standard Webhooks (webhook-id, webhook-timestamp, webhook-signature)
        with a strict 300-second replay window, or fallback HMAC-SHA256 x-polar-signature header.
        """
        if not self.webhook_secret:
            return False

        norm_headers = {str(k).lower(): v for k, v in headers.items()}
        wh_id = norm_headers.get("webhook-id", "")
        wh_ts = norm_headers.get("webhook-timestamp", "")
        wh_sig = norm_headers.get("webhook-signature", "")

        if wh_id and wh_ts and wh_sig:
            try:
                ts_val = float(wh_ts)
            except (TypeError, ValueError):
                return False
            if not math.isfinite(ts_val) or abs(time.time() - ts_val) > 300:
                return False

            try:
                body_text = raw_body.decode("utf-8")
            except UnicodeDecodeError:
                return False

            signed_content = f"{wh_id}.{wh_ts}.{body_text}".encode("utf-8")
            secret_str = self.webhook_secret
            try:
                if secret_str.startswith("whsec_"):
                    secret_bytes = base64.b64decode(secret_str[len("whsec_"):])
                else:
                    secret_bytes = secret_str.encode("utf-8")
            except Exception:
                return False

            expected_b64 = base64.b64encode(
                hmac.new(secret_bytes, signed_content, hashlib.sha256).digest()
            ).decode("utf-8")
            for part in wh_sig.split():
                if "," in part:
                    ver, sig_val = part.split(",", 1)
                    if ver == "v1" and hmac.compare_digest(sig_val, expected_b64):
                        return True
            return False

        legacy_sig = norm_headers.get("x-polar-signature", "")
        if legacy_sig:
            expected_hex = hmac.new(
                self.webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(legacy_sig.replace("sha256=", ""), expected_hex)

        return False

    @staticmethod
    def _resolve_validated_sku(data: Dict[str, Any], metadata: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Strictly resolves SKU from metadata or product_id without unsafe fallback defaults.
        Returns (sku, rejection_reason).
        """
        meta_sku = str(metadata.get("sku") or metadata.get("souq_sku") or "").strip()
        data_product_id = str(
            data.get("product_id") or (data.get("product") or {}).get("id") or ""
        ).strip()

        if meta_sku:
            if meta_sku not in POLAR_PRODUCTS:
                return None, f"invalid_sku:{meta_sku}"
            expected_prod_id = os.getenv(POLAR_PRODUCTS[meta_sku]["product_id_env"], "").strip()
            if expected_prod_id and data_product_id and data_product_id != expected_prod_id:
                return None, f"product_id_mismatch:{data_product_id}"
            return meta_sku, None

        if data_product_id:
            for candidate_sku, spec in POLAR_PRODUCTS.items():
                configured_pid = os.getenv(spec["product_id_env"], "").strip()
                if configured_pid and configured_pid == data_product_id:
                    return candidate_sku, None
            return None, f"unknown_product_id:{data_product_id}"

        return None, "missing_sku_or_product_id"

    def handle_order_webhook(self, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes Polar.sh order.created / order.paid webhooks:
        - Strictly validates settlement state, SKU/product mapping, and amount paid.
        - Seals newly minted prepaid API keys for one-time claim; never leaks raw api_key in webhook JSON.
        """
        event_type = webhook_payload.get("type", "")
        data = webhook_payload.get("data", {}) or {}

        if event_type not in ("order.created", "order.paid"):
            return {"status": "IGNORED", "reason": f"Unhandled event type: {event_type}"}

        order_id = str(data.get("id") or data.get("checkout_id") or "").strip()
        paid_flag = data.get("paid")
        status_str = str(data.get("status", "")).lower().strip()
        rejected_statuses = ("pending", "open", "unpaid", "incomplete", "canceled", "cancelled", "refunded", "failed")

        if paid_flag is False or status_str in rejected_statuses:
            return {"status": "REJECTED", "reason": "order_not_paid", "order_id": order_id}

        is_paid = (
            paid_flag is True
            or status_str in ("paid", "succeeded", "completed")
            or (event_type == "order.paid" and paid_flag is not False)
        )
        if not is_paid:
            return {"status": "REJECTED", "reason": "order_payment_unconfirmed", "order_id": order_id}

        metadata = data.get("metadata") or {}
        sku, sku_err = self._resolve_validated_sku(data, metadata)
        if not sku:
            return {"status": "REJECTED", "reason": sku_err or "invalid_sku", "order_id": order_id}

        spec = POLAR_PRODUCTS[sku]
        expected_amount_cents = int(round(float(spec["price_usd"]) * 100))
        raw_amount = data.get("total_amount")
        if raw_amount is None:
            raw_amount = data.get("amount")
        try:
            amount_cents = int(raw_amount if raw_amount is not None else 0)
        except (TypeError, ValueError):
            amount_cents = 0

        if amount_cents < expected_amount_cents:
            return {
                "status": "REJECTED",
                "reason": "underpaid_order_amount",
                "order_id": order_id,
                "sku": sku,
                "expected_amount_cents": expected_amount_cents,
                "received_amount_cents": amount_cents,
            }

        customer = data.get("customer", {}) or {}
        customer_email = customer.get("email") or data.get("customer_email")
        github_username = data.get("custom_field_github_username")

        credit_provisioning: Optional[Dict[str, Any]] = None
        if spec["kind"] == "api_credits" and order_id and self.api_key_ledger is not None:
            credit_usd = float(spec["credit_usd"])
            claim_token = str(metadata.get("souq_claim_token") or "").strip() or secrets.token_urlsafe(24)

            ok, res = self.api_key_ledger.issue_or_topup_key(
                reference_id=f"polar:{order_id}",
                amount_usd=credit_usd,
                rail="polar_fiat",
                owner_label=customer_email or order_id,
            )

            if ok and res.get("api_key"):
                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(hours=_CLAIMS_TTL_HOURS)
                sealed = self._seal_key(res["api_key"], claim_token)
                with db_transaction(self.db_target, read_only=False) as con:
                    self._ensure_claims_table(con)
                    con.execute(
                        """
                        INSERT INTO polar_checkout_claims (
                            claim_token, order_id, sku, sealed_key, key_prefix,
                            amount_cents, claimed, created_at, expires_at
                        ) VALUES (?, ?, ?, ?, ?, ?, FALSE, ?, ?)
                        ON CONFLICT (order_id) DO NOTHING
                        """,
                        (
                            claim_token,
                            order_id,
                            sku,
                            sealed,
                            res["key_prefix"],
                            amount_cents,
                            now,
                            expires_at,
                        ),
                    )
                opaque_key_id = self._opaque_key_id(
                    res.get("key_id"),
                    res.get("api_key") or res.get("key_prefix") or order_id,
                )
                credit_provisioning = {
                    "key_id": opaque_key_id,
                    "key_prefix": "souq_***",
                    "credits_added_usd": credit_usd,
                    "claim_ready": True,
                    "already_redeemed": False,
                }
            elif "Already Redeemed" in res.get("error", ""):
                with db_transaction(self.db_target, read_only=True) as con:
                    self._ensure_claims_table(con)
                    existing_claim = con.execute(
                        "SELECT key_prefix, claimed, sealed_key FROM polar_checkout_claims WHERE order_id = ?",
                        (order_id,),
                    ).fetchone()
                existing_prefix = existing_claim[0] if existing_claim else None
                credit_provisioning = {
                    "key_id": self._opaque_key_id(None, existing_prefix),
                    "key_prefix": "souq_***" if existing_prefix else None,
                    "credits_added_usd": credit_usd,
                    "claim_ready": bool(existing_claim and not existing_claim[1] and existing_claim[2]),
                    "already_redeemed": True,
                }

        return {
            "status": "PROCESSED",
            "order_id": order_id,
            "sku": sku,
            "amount_usd": round(float(amount_cents) / 100.0, 2),
            "customer_email": customer_email,
            "github_username": github_username,
            "credit_provisioning": credit_provisioning,
            "action": "PREPAID_API_KEY_ISSUED" if credit_provisioning else "AUTOMATIC_DELIVERY_DISPATCHED",
        }

    def claim_checkout_key(
        self,
        claim_token: Optional[str] = None,
        order_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        One-time secure retrieval of a sealed prepaid API key after Polar checkout.
        Verifies unclaimed and non-expired (<= 24h), atomically wipes sealed_key, and returns api_key once.
        """
        tok = (claim_token or "").strip()
        ord_id = (order_id or "").strip()
        if not tok:
            return False, {"error": "Missing claim_token"}

        now = datetime.now(timezone.utc)
        with db_transaction(self.db_target, read_only=False) as con:
            self._ensure_claims_table(con)
            if ord_id:
                row = con.execute(
                    """
                    SELECT claim_token, order_id, sku, sealed_key, key_prefix,
                           amount_cents, claimed, created_at, expires_at
                    FROM polar_checkout_claims
                    WHERE claim_token = ? AND order_id = ?
                    """,
                    (tok, ord_id),
                ).fetchone()
            else:
                row = con.execute(
                    """
                    SELECT claim_token, order_id, sku, sealed_key, key_prefix,
                           amount_cents, claimed, created_at, expires_at
                    FROM polar_checkout_claims
                    WHERE claim_token = ?
                    """,
                    (tok,),
                ).fetchone()

            if not row:
                return False, {"error": "Claim not found"}

            row_token, row_order_id, sku, sealed_key, key_prefix, amount_cents, claimed, _, expires_raw = row
            if bool(claimed) or not sealed_key:
                return False, {"error": "Claim already redeemed"}

            expires_at = _as_utc_datetime(expires_raw)
            if expires_at is not None and now > expires_at:
                con.execute(
                    "UPDATE polar_checkout_claims SET sealed_key = NULL WHERE claim_token = ?",
                    (row_token,),
                )
                return False, {"error": "Claim expired"}

            raw_key = self._unseal_key(sealed_key, row_token)
            if not raw_key:
                return False, {"error": "Failed to unseal API key"}

            updated = con.execute(
                """
                UPDATE polar_checkout_claims
                SET claimed = TRUE, sealed_key = NULL
                WHERE claim_token = ? AND claimed = FALSE AND sealed_key IS NOT NULL
                RETURNING claim_token
                """,
                (row_token,),
            ).fetchone()
            if not updated:
                return False, {"error": "Claim already redeemed"}

        return True, {
            "status": "CLAIMED",
            "api_key": raw_key,
            "key_prefix": key_prefix,
            "sku": sku,
            "order_id": row_order_id,
            "amount_cents": int(amount_cents) if amount_cents is not None else 0,
        }

