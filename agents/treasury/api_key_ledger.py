"""
SOUQ // Prepaid API Key & Micro-Credit Ledger (Sayrafi Treasury)
Eliminates per-call crypto signing friction by allowing agents & developers to:
1. Top up prepaid USD/USDC credit balances once (via Base USDC or Polar.sh fiat checkout)
2. Authenticate seamlessly across MCP (Claude/Cursor), Python SDK, npm, and HTTP REST using X-API-Key
"""

import os
import hmac
import math
import hashlib
import secrets
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from agents.treasury.db_backend import (
    resolve_db_target,
    db_transaction,
    ensure_parent_dir,
)

logger = logging.getLogger("souq.api_key_ledger")
_DEFAULT_PEPPER = "souq_sovereign_pepper_2026"


def normalize_reference_id(ref: str) -> str:
    """Normalizes payment references: strips whitespace and lowercases 0x hex hashes."""
    cleaned = (ref or "").strip()
    return cleaned.lower() if cleaned.lower().startswith("0x") else cleaned


class APIKeyLedger:
    """
    DuckDB/PostgreSQL-backed prepaid API key and balance ledger with atomic anti-replay top-ups.
    """

    def __init__(self, db_path: str = "data/souq_treasury_lake.duckdb"):
        self.db_path = db_path
        self.db_target, self.is_postgres = resolve_db_target(db_path)
        if not self.is_postgres:
            ensure_parent_dir(self.db_target)

        pepper_env = os.getenv("SOUQ_API_KEY_PEPPER", "")
        self._secret_pepper = pepper_env or _DEFAULT_PEPPER
        is_prod = os.getenv("ENV", "").lower() == "production" or bool(os.getenv("KOYEB_APP_ID"))
        if is_prod and (not pepper_env or pepper_env == _DEFAULT_PEPPER):
            logger.warning(
                "SOUQ_API_KEY_PEPPER is unset or using the default insecure pepper in production; "
                "configure a strong random SOUQ_API_KEY_PEPPER secret."
            )
        self._init_db()

    def _init_db(self) -> None:
        with db_transaction(self.db_target, read_only=False) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_hash VARCHAR PRIMARY KEY,
                    key_prefix VARCHAR NOT NULL,
                    owner_label VARCHAR NOT NULL,
                    balance_usd DECIMAL(18, 6) NOT NULL DEFAULT 0.0,
                    total_credited_usd DECIMAL(18, 6) NOT NULL DEFAULT 0.0,
                    total_spent_usd DECIMAL(18, 6) NOT NULL DEFAULT 0.0,
                    calls_count INTEGER NOT NULL DEFAULT 0,
                    status VARCHAR NOT NULL DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS credit_topups (
                    reference_id VARCHAR PRIMARY KEY,
                    key_hash VARCHAR NOT NULL,
                    rail VARCHAR NOT NULL,
                    amount_usd DECIMAL(18, 6) NOT NULL,
                    payer_identifier VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def _hash_key(self, raw_key: str) -> str:
        return hmac.new(
            self._secret_pepper.encode("utf-8"),
            raw_key.strip().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def is_reference_redeemed(self, reference_id: str) -> bool:
        ref_norm = normalize_reference_id(reference_id)
        if not ref_norm:
            return False
        with db_transaction(self.db_target, read_only=True) as con:
            row = con.execute(
                "SELECT 1 FROM credit_topups WHERE reference_id = ?",
                (ref_norm,),
            ).fetchone()
            return row is not None

    def issue_or_topup_key(
        self,
        reference_id: str,
        amount_usd: float,
        rail: str = "base_usdc",
        owner_label: str = "anonymous",
        existing_api_key: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Credits an existing API key or mints a new prepaid API key.
        Idempotent & atomically anti-replay guarded on reference_id (tx_hash or Polar order ID).
        """
        ref_norm = normalize_reference_id(reference_id)
        if not ref_norm:
            return False, {"error": "Missing payment reference_id"}
        if not math.isfinite(amount_usd) or amount_usd <= 0:
            return False, {"error": "Invalid top-up amount", "amount_usd": amount_usd}

        amount_val = round(float(amount_usd), 6)
        now = datetime.now(timezone.utc)
        raw_key: Optional[str] = None

        with db_transaction(self.db_target, read_only=False) as con:
            already = con.execute(
                "SELECT 1 FROM credit_topups WHERE reference_id = ?",
                (ref_norm,),
            ).fetchone()
            if already:
                return False, {
                    "error": "Reference Already Redeemed",
                    "message": "This payment reference has already been credited.",
                    "reference_id": ref_norm,
                }

            if existing_api_key:
                key_hash = self._hash_key(existing_api_key)
                existing_row = con.execute(
                    "SELECT key_prefix, balance_usd, status FROM api_keys WHERE key_hash = ?",
                    (key_hash,),
                ).fetchone()
                if not existing_row:
                    return False, {"error": "Unknown existing_api_key"}
                if existing_row[2] != "ACTIVE":
                    return False, {"error": "API key is not active"}
                key_prefix = existing_row[0]
            else:
                raw_key = f"souq_live_{secrets.token_urlsafe(24)}"
                key_hash = self._hash_key(raw_key)
                key_prefix = raw_key[:16]

            inserted_ref = con.execute(
                """
                INSERT INTO credit_topups (reference_id, key_hash, rail, amount_usd, payer_identifier, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (reference_id) DO NOTHING
                RETURNING reference_id
                """,
                (ref_norm, key_hash, rail, amount_val, owner_label[:120], now),
            ).fetchone()
            if not inserted_ref:
                return False, {
                    "error": "Reference Already Redeemed",
                    "message": "This payment reference has already been credited.",
                    "reference_id": ref_norm,
                }

            if existing_api_key:
                con.execute(
                    """
                    UPDATE api_keys
                    SET balance_usd = balance_usd + ?,
                        total_credited_usd = total_credited_usd + ?
                    WHERE key_hash = ? AND status = 'ACTIVE'
                    """,
                    (amount_val, amount_val, key_hash),
                )
            else:
                con.execute(
                    """
                    INSERT INTO api_keys (
                        key_hash, key_prefix, owner_label, balance_usd,
                        total_credited_usd, total_spent_usd, calls_count, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, 0.0, 0, 'ACTIVE', ?)
                    """,
                    (key_hash, key_prefix, owner_label[:120], amount_val, amount_val, now),
                )

            bal_row = con.execute(
                "SELECT balance_usd FROM api_keys WHERE key_hash = ?",
                (key_hash,),
            ).fetchone()
            new_balance = float(bal_row[0]) if bal_row else amount_val

        result: Dict[str, Any] = {
            "status": "CREDITED",
            "reference_id": ref_norm,
            "rail": rail,
            "amount_credited_usd": amount_val,
            "balance_usd": round(new_balance, 6),
            "key_id": key_hash[:16],
            "key_prefix": key_prefix,
        }
        if raw_key:
            result["api_key"] = raw_key
            result["note"] = "Store this API key securely; it is shown once. Pass via header X-API-Key or env SOUQ_API_KEY."
        return True, result

    def validate_and_debit(
        self,
        raw_key: str,
        price_usd: float,
        tool_name: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies an API key is active with sufficient balance and atomically debits price_usd.
        """
        if not raw_key or not raw_key.strip():
            return False, {"error": "Missing API key"}
        if not math.isfinite(price_usd) or price_usd < 0:
            return False, {"error": "Invalid debit amount"}

        debit_val = round(float(price_usd), 6)
        key_hash = self._hash_key(raw_key)
        now = datetime.now(timezone.utc)

        with db_transaction(self.db_target, read_only=False) as con:
            updated = con.execute(
                """
                UPDATE api_keys
                SET balance_usd = balance_usd - ?,
                    total_spent_usd = total_spent_usd + ?,
                    calls_count = calls_count + 1,
                    last_used_at = ?
                WHERE key_hash = ? AND status = 'ACTIVE' AND balance_usd >= ?
                RETURNING key_prefix, balance_usd
                """,
                (debit_val, debit_val, now, key_hash, debit_val),
            ).fetchone()

            if not updated:
                row = con.execute(
                    "SELECT key_prefix, balance_usd, status FROM api_keys WHERE key_hash = ?",
                    (key_hash,),
                ).fetchone()
                if not row:
                    return False, {"error": "Invalid API Key"}
                _, balance_dec, status = row
                balance = float(balance_dec)
                if status != "ACTIVE":
                    return False, {"error": f"API Key status is '{status}'"}
                return False, {
                    "error": "Insufficient Credits",
                    "balance_usd": round(balance, 6),
                    "required_usd": debit_val,
                    "tool": tool_name,
                }

            key_prefix, remaining_dec = updated
            remaining = max(0.0, round(float(remaining_dec), 6))

        return True, {
            "status": "SETTLED_PREPAID_CREDIT",
            "key_prefix": key_prefix,
            "amount_debited_usd": debit_val,
            "balance_remaining_usd": remaining,
            "tool": tool_name,
        }

    def refund_debit(
        self,
        raw_key: str,
        price_usd: float,
        reason: str = "tool_execution_failed",
    ) -> Tuple[bool, Dict[str, Any]]:
        """Atomically refunds a prior debit back to an active prepaid API key."""
        if not raw_key or not raw_key.strip():
            return False, {"error": "Missing API key"}
        if not math.isfinite(price_usd) or price_usd <= 0:
            return False, {"error": "Invalid refund amount"}

        refund_val = round(float(price_usd), 6)
        key_hash = self._hash_key(raw_key)

        with db_transaction(self.db_target, read_only=False) as con:
            updated = con.execute(
                """
                UPDATE api_keys
                SET balance_usd = balance_usd + ?,
                    total_spent_usd = GREATEST(0.0, total_spent_usd - ?),
                    calls_count = GREATEST(0, calls_count - 1)
                WHERE key_hash = ? AND status = 'ACTIVE'
                RETURNING key_prefix, balance_usd
                """,
                (refund_val, refund_val, key_hash),
            ).fetchone()

            if not updated:
                row = con.execute(
                    "SELECT status FROM api_keys WHERE key_hash = ?",
                    (key_hash,),
                ).fetchone()
                if not row:
                    return False, {"error": "Invalid API Key"}
                return False, {"error": f"API Key status is '{row[0]}'"}

            key_prefix, new_bal = updated

        return True, {
            "status": "REFUNDED",
            "key_prefix": key_prefix,
            "amount_refunded_usd": refund_val,
            "balance_usd": round(float(new_bal), 6),
            "reason": reason,
        }

    def get_key_status(self, raw_key: str) -> Optional[Dict[str, Any]]:
        if not raw_key or not raw_key.strip():
            return None
        key_hash = self._hash_key(raw_key)
        with db_transaction(self.db_target, read_only=True) as con:
            row = con.execute(
                """
                SELECT key_prefix, owner_label, balance_usd, total_credited_usd,
                       total_spent_usd, calls_count, status, created_at, last_used_at
                FROM api_keys WHERE key_hash = ?
                """,
                (key_hash,),
            ).fetchone()
            if not row:
                return None
            return {
                "key_prefix": row[0],
                "owner_label": row[1],
                "balance_usd": round(float(row[2]), 6),
                "total_credited_usd": round(float(row[3]), 6),
                "total_spent_usd": round(float(row[4]), 6),
                "calls_count": int(row[5]),
                "status": row[6],
                "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
                "last_used_at": row[8].isoformat() if row[8] and hasattr(row[8], "isoformat") else row[8],
            }
