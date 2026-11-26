"""
SOUQ // Deterministic Request-Bound Wallet Enforcement Gate & eth_call Pre-Simulation
Intercepts every outbound Base L2 USDC transaction to enforce:
1. Strict recipient whitelist
2. Per-call USDC cap (default $0.10)
3. Rolling 24h daily spend cap (default $2.00)
4. work_order_id idempotency ledger (0 duplicate USDC transfers)
5. Mandatory eth_call pre-simulation before send_raw_transaction
"""

import json
import math
import os
import re
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Set

EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DEFAULT_RECIPIENT = "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF"


class WalletGateError(PermissionError):
    """Raised when an outbound wallet transaction violates WalletEnforcementGate policy."""


class WalletEnforcementGate:
    """
    Deterministic policy & simulation gate for Base L2 USDC transfers and payouts.
    """

    def __init__(
        self,
        allowed_recipients: Optional[Iterable[str]] = None,
        max_per_call_usd: Optional[float] = None,
        max_daily_spend_usd: Optional[float] = None,
        ledger_path: Optional[str] = None,
    ):
        if allowed_recipients is None:
            env_list = os.getenv(
                "SOUQ_WALLET_ALLOWED_RECIPIENTS",
                os.getenv("BASE_RECIPIENT_WALLET_ADDRESS", DEFAULT_RECIPIENT),
            )
            raw_addrs = [a.strip() for a in env_list.split(",") if a.strip()]
        else:
            raw_addrs = [str(a).strip() for a in allowed_recipients if str(a).strip()]

        self.allowed_recipients: Set[str] = {
            addr.lower() for addr in raw_addrs if EVM_ADDRESS_RE.match(addr)
        }
        self.max_per_call_usd = (
            float(max_per_call_usd)
            if max_per_call_usd is not None
            else float(os.getenv("SOUQ_WALLET_MAX_PER_CALL_USD", "0.10"))
        )
        self.max_daily_spend_usd = (
            float(max_daily_spend_usd)
            if max_daily_spend_usd is not None
            else float(os.getenv("SOUQ_WALLET_MAX_DAILY_USD", "2.00"))
        )
        self.ledger_path = ledger_path
        self._lock = threading.RLock()
        self._work_orders: Dict[str, Dict[str, Any]] = {}
        self._spend_log: List[Dict[str, Any]] = []
        if self.ledger_path:
            self._load_ledger()

    def _load_ledger(self) -> None:
        if not self.ledger_path or not os.path.exists(self.ledger_path):
            return
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._work_orders = dict(data.get("work_orders") or {})
                self._spend_log = list(data.get("spend_log") or [])
        except Exception:
            pass

    def _persist_ledger(self) -> None:
        if not self.ledger_path:
            return
        parent = os.path.dirname(os.path.abspath(self.ledger_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp_path = f"{self.ledger_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(
                {"work_orders": self._work_orders, "spend_log": self._spend_log},
                f,
                indent=2,
            )
        os.replace(tmp_path, self.ledger_path)

    def daily_spend_usd(self, now_ts: Optional[float] = None) -> float:
        now = time.time() if now_ts is None else float(now_ts)
        cutoff = now - 86400.0
        with self._lock:
            return round(
                sum(float(entry.get("amount_usdc", 0.0)) for entry in self._spend_log if float(entry.get("ts", 0.0)) > cutoff),
                6,
            )

    def check_policy(
        self,
        recipient: str,
        amount_usdc: float,
        work_order_id: str,
        quote_hash: Optional[str] = None,
        now_ts: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Deterministically enforces recipient whitelist, per-call cap, daily cap,
        and work_order_id idempotency. Raises WalletGateError on any violation.
        """
        now = time.time() if now_ts is None else float(now_ts)
        wo_id = (work_order_id or "").strip()
        if not wo_id:
            raise WalletGateError("Missing required work_order_id for idempotent wallet execution.")

        rec = (recipient or "").strip()
        if not EVM_ADDRESS_RE.match(rec):
            raise WalletGateError(f"Invalid EVM recipient address: '{rec}'")
        if rec.lower() not in self.allowed_recipients:
            raise WalletGateError(f"Recipient '{rec}' is not in the WalletEnforcementGate whitelist.")

        try:
            amt = float(amount_usdc)
        except (TypeError, ValueError) as exc:
            raise WalletGateError(f"Invalid amount_usdc: {amount_usdc}") from exc

        if not math.isfinite(amt) or amt <= 0.0:
            raise WalletGateError(f"amount_usdc must be positive and finite (got {amt}).")
        if amt > self.max_per_call_usd + 1e-12:
            raise WalletGateError(
                f"Requested transfer ${amt:.4f} USDC exceeds max per-call cap ${self.max_per_call_usd:.4f} USDC."
            )

        with self._lock:
            if wo_id in self._work_orders:
                raise WalletGateError(f"Duplicate work_order_id '{wo_id}' blocked by idempotency ledger.")

            spent_24h = self.daily_spend_usd(now_ts=now)
            if spent_24h + amt > self.max_daily_spend_usd + 1e-12:
                raise WalletGateError(
                    f"Daily spend cap exceeded: 24h spend ${spent_24h:.4f} + ${amt:.4f} > ${self.max_daily_spend_usd:.4f} USDC."
                )

        return {
            "status": "POLICY_CLEARED",
            "recipient": rec,
            "amount_usdc": round(amt, 6),
            "work_order_id": wo_id,
            "quote_hash": quote_hash,
            "daily_spend_before_usd": spent_24h,
            "daily_spend_after_usd": round(spent_24h + amt, 6),
        }

    @staticmethod
    def simulate_eth_call(w3: Any, tx: Dict[str, Any]) -> bytes:
        """
        Executes read-only eth_call pre-simulation before any transaction is broadcast.
        Aborts with WalletGateError if the EVM simulation reverts or returns ERC-20 false.
        """
        call_params: Dict[str, Any] = {
            "from": tx.get("from"),
            "to": tx.get("to"),
            "data": tx.get("data", b""),
            "value": tx.get("value", 0),
        }
        try:
            sim_result = w3.eth.call(call_params)
        except Exception as exc:
            raise WalletGateError(f"eth_call pre-simulation failed/reverted: {exc}") from exc

        if sim_result is not None:
            raw_bytes: bytes
            if isinstance(sim_result, (bytes, bytearray)):
                raw_bytes = bytes(sim_result)
            elif isinstance(sim_result, str) and sim_result.startswith("0x"):
                try:
                    raw_bytes = bytes.fromhex(sim_result[2:])
                except ValueError:
                    raw_bytes = b""
            else:
                raw_bytes = b""

            if len(raw_bytes) == 32 and int.from_bytes(raw_bytes, "big") == 0:
                raise WalletGateError("eth_call pre-simulation returned ERC-20 false (0x00..00).")

        return sim_result if isinstance(sim_result, (bytes, bytearray)) else b""

    def record_execution(
        self,
        recipient: str,
        amount_usdc: float,
        work_order_id: str,
        tx_hash: Optional[str] = None,
        quote_hash: Optional[str] = None,
        now_ts: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Atomically validates policy and commits a work_order_id + spend entry to the ledger."""
        now = time.time() if now_ts is None else float(now_ts)
        with self._lock:
            check = self.check_policy(
                recipient=recipient,
                amount_usdc=amount_usdc,
                work_order_id=work_order_id,
                quote_hash=quote_hash,
                now_ts=now,
            )
            entry = {
                "work_order_id": check["work_order_id"],
                "quote_hash": quote_hash,
                "recipient": check["recipient"],
                "amount_usdc": check["amount_usdc"],
                "tx_hash": tx_hash,
                "ts": now,
            }
            self._work_orders[check["work_order_id"]] = entry
            self._spend_log.append(entry)
            self._persist_ledger()
            return entry

    def authorize_and_broadcast(
        self,
        w3: Any,
        tx: Dict[str, Any],
        sign_fn: Callable[[Dict[str, Any]], bytes],
        recipient: str,
        amount_usdc: float,
        work_order_id: str,
        quote_hash: Optional[str] = None,
        now_ts: Optional[float] = None,
    ) -> str:
        """
        Full deterministic outbound wallet pipeline:
        1. Policy check (recipient whitelist, per-call cap, daily cap, work_order_id idempotency)
        2. eth_call pre-simulation (must succeed before signing/broadcast)
        3. Sign & broadcast via w3.eth.send_raw_transaction
        4. Commit work_order_id and spend entry to idempotency ledger
        """
        now = time.time() if now_ts is None else float(now_ts)
        with self._lock:
            self.check_policy(
                recipient=recipient,
                amount_usdc=amount_usdc,
                work_order_id=work_order_id,
                quote_hash=quote_hash,
                now_ts=now,
            )
            self.simulate_eth_call(w3, tx)

            raw_tx = sign_fn(tx)
            tx_hash_bytes = w3.eth.send_raw_transaction(raw_tx)
            tx_hash_hex = tx_hash_bytes.hex() if hasattr(tx_hash_bytes, "hex") else str(tx_hash_bytes)
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = f"0x{tx_hash_hex}"

            entry = {
                "work_order_id": work_order_id.strip(),
                "quote_hash": quote_hash,
                "recipient": recipient.strip(),
                "amount_usdc": round(float(amount_usdc), 6),
                "tx_hash": tx_hash_hex,
                "ts": now,
            }
            self._work_orders[entry["work_order_id"]] = entry
            self._spend_log.append(entry)
            self._persist_ledger()
            return tx_hash_hex
