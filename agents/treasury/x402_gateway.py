"""
SOUQ // HTTP 402 ("x402") Base USDC Payment Gateway Middleware
Handles cryptographic 402 payment challenges, strict ERC-20 Transfer log verification,
and anti-replay nullification for autonomous agent clients.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import threading
import weakref
from typing import Dict, Any, Tuple, Optional, List, Callable, Set
import requests
import yaml
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct, encode_typed_data

from agents.treasury.db_backend import (
    load_souq_env,
    get_ephemeral_test_pepper,
    db_transaction,
)
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.treasury.api_key_ledger import APIKeyLedger
from agents.analytics.negotiation_tracker import NegotiationTracker

load_souq_env()

# Keccak-256 topic for ERC-20 Transfer(address indexed from, address indexed to, uint256 value)
ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TX_HASH_REGEX = re.compile(r"^0x[0-9a-fA-F]{64}$")
DEFAULT_BASE_RPCS = [
    "https://base-rpc.publicnode.com",
    "https://1rpc.io/base",
    "https://mainnet.base.org",
]
RPC_REQUEST_KWARGS = {
    "timeout": 8,
    "headers": {"User-Agent": "Mozilla/5.0 SOUQ-x402-Gateway/1.0"},
}


class _TxLockHolder:
    __slots__ = ("lock", "__weakref__")

    def __init__(self) -> None:
        self.lock = threading.RLock()


_TX_INFLIGHT_LOCKS: "weakref.WeakValueDictionary[str, _TxLockHolder]" = weakref.WeakValueDictionary()
_TX_LOCKS_GUARD = threading.Lock()


def _get_tx_lock(tx_hash: str) -> _TxLockHolder:
    key = (tx_hash or "").strip().lower()
    with _TX_LOCKS_GUARD:
        holder = _TX_INFLIGHT_LOCKS.get(key)
        if holder is None:
            holder = _TxLockHolder()
            _TX_INFLIGHT_LOCKS[key] = holder
        return holder


def _load_base_settlement_settings() -> Dict[str, Any]:
    settings_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "config", "settings.yaml")
    )
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        base_cfg = ((cfg.get("settlement") or {}).get("base") or {})
        return base_cfg if isinstance(base_cfg, dict) else {}
    except Exception:
        return {}


class X402PaymentGateway:
    """
    HTTP 402 Middleware intercepting unpaid agent requests, issuing machine-readable
    Base USDC payment challenges, and certifying settlements with cryptographic receipts.
    """

    def __init__(
        self,
        receipt_engine: Optional[CryptoReceiptEngine] = None,
        negotiation_tracker: Optional[NegotiationTracker] = None,
        recipient_wallet: Optional[str] = None,
        rpc_url: Optional[str] = None,
        api_key_ledger: Optional[APIKeyLedger] = None,
        facilitator_url: Optional[str] = None,
    ):
        self.receipt_engine = receipt_engine or CryptoReceiptEngine()
        self.negotiation_tracker = negotiation_tracker or NegotiationTracker()
        self.api_key_ledger = api_key_ledger or APIKeyLedger(db_path=self.receipt_engine.db_path)

        base_cfg = _load_base_settlement_settings()
        self.confirmation_blocks = int(
            os.getenv("SOUQ_CONFIRMATION_BLOCKS", str(base_cfg.get("confirmation_blocks", 1)))
        )
        self.max_tx_age_seconds = int(
            os.getenv("SOUQ_MAX_TX_AGE_SECONDS", str(base_cfg.get("max_tx_age_seconds", 180)))
        )
        self.max_topup_tx_age_seconds = int(
            os.getenv("SOUQ_MAX_TOPUP_TX_AGE_SECONDS", str(base_cfg.get("max_topup_tx_age_seconds", 86400)))
        )

        self.recipient_wallet = (
            recipient_wallet or
            os.getenv("BASE_RECIPIENT_WALLET_ADDRESS", "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF")
        )
        self._explicit_rpc = rpc_url is not None
        primary_rpc = rpc_url or os.getenv("BASE_RPC_URL", DEFAULT_BASE_RPCS[0])
        self.rpc_url = primary_rpc
        self.rpc_urls: List[str] = list(dict.fromkeys([primary_rpc] + ([] if rpc_url else DEFAULT_BASE_RPCS)))
        self.usdc_contract = os.getenv("BASE_USDC_CONTRACT", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs=RPC_REQUEST_KWARGS))
        self.facilitator_url = (
            facilitator_url
            or os.getenv("SOUQ_X402_FACILITATOR_URL", "https://x402.org/facilitator")
        ).rstrip("/")

        # AML / Compliance Deny-List for Restricted and Sanctioned Source Addresses
        self.restricted_addresses = set(
            addr.lower() for addr in os.getenv("RESTRICTED_SOURCE_ADDRESSES", "").split(",") if addr.strip()
        )

        # Request-bound quote & work_order_id anti-replay registry
        self._quote_lock = threading.RLock()
        self._issued_quotes: Dict[str, Dict[str, Any]] = {}
        self._consumed_work_orders: Set[str] = set()
        self._redeemed_nullifiers: Set[str] = set()
        self._init_eip3009_nullifiers_table()

    def _init_eip3009_nullifiers_table(self) -> None:
        db_target = getattr(self.receipt_engine, "db_target", None)
        if not db_target:
            return
        try:
            with db_transaction(db_target, read_only=False) as con:
                con.execute("""
                    CREATE TABLE IF NOT EXISTS x402_eip3009_nullifiers (
                        nullifier VARCHAR PRIMARY KEY,
                        tx_hash VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        except Exception:
            pass

    def _record_eip3009_nullifier(self, nullifier: Optional[str], tx_hash: str) -> None:
        norm = (nullifier or "").strip().lower()
        if not norm:
            return
        with self._quote_lock:
            self._redeemed_nullifiers.add(norm)
        db_target = getattr(self.receipt_engine, "db_target", None)
        if not db_target:
            return
        try:
            with db_transaction(db_target, read_only=False) as con:
                con.execute(
                    """
                    INSERT INTO x402_eip3009_nullifiers (nullifier, tx_hash)
                    VALUES (?, ?)
                    ON CONFLICT (nullifier) DO NOTHING
                    """,
                    (norm, (tx_hash or "").strip().lower()),
                )
        except Exception:
            pass

    def _is_eip3009_nullifier_used(self, nullifier: str) -> bool:
        norm = (nullifier or "").strip().lower()
        if not norm:
            return False
        with self._quote_lock:
            if norm in self._redeemed_nullifiers:
                return True
        db_target = getattr(self.receipt_engine, "db_target", None)
        if not db_target:
            return False
        try:
            with db_transaction(db_target, read_only=True) as con:
                row = con.execute(
                    "SELECT 1 FROM x402_eip3009_nullifiers WHERE nullifier = ?",
                    (norm,),
                ).fetchone()
                return row is not None
        except Exception:
            return False

    @staticmethod
    def _get_quote_signing_key() -> bytes:
        key = (
            os.getenv("SOUQ_HASH_PEPPER")
            or os.getenv("SOUQ_RECEIPT_SIGNING_KEY")
            or os.getenv("SOUQ_API_KEY_PEPPER")
            or get_ephemeral_test_pepper()
        )
        return key.encode("utf-8")

    def _compute_quote_hash(self, quote_fields: Dict[str, Any]) -> str:
        canonical = json.dumps(quote_fields, sort_keys=True, separators=(",", ":"))
        return hmac.new(
            self._get_quote_signing_key(),
            f"SOUQ_X402_QUOTE_V1:{canonical}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def generate_402_challenge(
        self,
        tool_name: str,
        price_usdc: float,
        client_agent_id: str = "anonymous_agent",
        client_user_agent: str = "AI-Agent-Client/1.0",
        payer_address: Optional[str] = None,
        work_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates the standardized Coinbase x402 v1 (EIP-3009) + direct Base USDC payment challenge
        bound with an HMAC-SHA256 quote_hash, unique work_order_id, and optional payer_address.
        """
        created_at_epoch = int(time.time())
        expires_at_epoch = created_at_epoch + self.max_tx_age_seconds
        amount_units = int(round(price_usdc * 1e6))  # USDC has 6 decimals
        wo_id = (work_order_id or f"wo_{secrets.token_hex(12)}").strip()
        bound_payer = payer_address.strip().lower() if isinstance(payer_address, str) and payer_address.strip() else None

        quote_fields = {
            "work_order_id": wo_id,
            "tool_name": tool_name,
            "amount_units": amount_units,
            "recipient_address": self.recipient_wallet.lower(),
            "token_contract": self.usdc_contract.lower(),
            "chain_id": 8453,
            "created_at_epoch": created_at_epoch,
            "expires_at_epoch": expires_at_epoch,
            "payer_address": bound_payer,
        }
        quote_hash = self._compute_quote_hash(quote_fields)

        with self._quote_lock:
            if len(self._issued_quotes) > 5000:
                now_cut = int(time.time())
                self._issued_quotes = {
                    k: v for k, v in self._issued_quotes.items()
                    if int(v.get("expires_at_epoch", 0)) >= now_cut
                }
            self._issued_quotes[wo_id] = {**quote_fields, "quote_hash": quote_hash}

        challenge = {
            "status_code": 402,
            "error": "Payment Required",
            "protocol": "x402-v1.0",
            "x402Version": 1,
            "work_order_id": wo_id,
            "quote_hash": quote_hash,
            "accepts": [
                {
                    "scheme": "exact",
                    "network": "base",
                    "maxAmountRequired": str(amount_units),
                    "resource": f"/api/tools/call/{tool_name}",
                    "description": f"SOUQ MCP Tool Invocation: {tool_name}",
                    "mimeType": "application/json",
                    "payTo": self.recipient_wallet,
                    "maxTimeoutSeconds": self.max_tx_age_seconds,
                    "asset": self.usdc_contract,
                    "extra": {
                        "name": "USD Coin",
                        "version": "2",
                        "work_order_id": wo_id,
                        "quote_hash": quote_hash,
                        "expires_at_epoch": expires_at_epoch,
                        "facilitator_url": self.facilitator_url,
                    },
                }
            ],
            "payment_details": {
                "chain": "Base",
                "chain_id": 8453,
                "token": "USDC",
                "token_contract": self.usdc_contract,
                "amount": f"{price_usdc:.4f}",
                "amount_units": amount_units,
                "recipient_address": self.recipient_wallet,
                "valid_for_seconds": self.max_tx_age_seconds,
                "created_at_epoch": created_at_epoch,
                "expires_at_epoch": expires_at_epoch,
                "work_order_id": wo_id,
                "quote_hash": quote_hash,
                "payer_address": bound_payer,
            },
            "instructions": (
                "Settle gaslessly in 1 RTT via x402 v1 EIP-3009 transferWithAuthorization in header "
                "[PAYMENT-SIGNATURE / X-PAYMENT], OR transfer exact USDC on Base and retry with "
                "[X-Payment-Tx: <tx_hash>], OR fund a prepaid key via /api/credits/topup [X-API-Key: <key>]."
            ),
            "prepaid_credit_topup": {
                "endpoint": "/api/credits/topup",
                "header": "X-API-Key",
                "min_topup_usd": 0.50,
                "note": "Send Base USDC once to mint a reusable prepaid SOUQ API key and avoid per-call gas.",
            },
        }

        # Log challenge into negotiation tracker
        self.negotiation_tracker.log_negotiation(
            client_agent_id=client_agent_id,
            client_user_agent=client_user_agent,
            tool_requested=tool_name,
            initial_quote_usd=price_usdc,
            settled_price_usd=None,
            payment_protocol="x402_http",
            outcome="CHALLENGED_402",
            latency_ms=2,
            metadata={"challenge": challenge}
        )

        return challenge

    def verify_quote_binding(
        self,
        work_order_id: str,
        quote_hash: str,
        tool_name: str,
        expected_price_usdc: float,
        payer_address: Optional[str] = None,
        now_epoch: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Verifies HMAC-signed quote_hash + work_order_id binding to prevent cross-tool replay
        and front-running. Rejects unknown, tampered, expired, mismatched, or already-consumed quotes.
        """
        wo_id = (work_order_id or "").strip()
        q_hash = (quote_hash or "").strip().lower()
        if not wo_id or not q_hash:
            return False, "Both work_order_id and quote_hash are required for quote binding."

        now_ts = int(time.time()) if now_epoch is None else int(now_epoch)
        expected_units = int(round(expected_price_usdc * 1e6))

        with self._quote_lock:
            if wo_id in self._consumed_work_orders:
                return False, f"work_order_id '{wo_id}' has already been consumed (replay rejected)."

            issued = self._issued_quotes.get(wo_id)
            if not issued:
                return False, f"Unknown or expired work_order_id '{wo_id}'."

            if now_ts > int(issued["expires_at_epoch"]):
                return False, f"Quote for work_order_id '{wo_id}' has expired."

            if issued["tool_name"] != tool_name:
                return (
                    False,
                    f"Cross-tool quote replay rejected: quote bound to '{issued['tool_name']}', not '{tool_name}'.",
                )

            if int(issued["amount_units"]) < expected_units:
                return False, "Quote amount_units is below expected tool price."

            bound_payer = issued.get("payer_address")
            if bound_payer and payer_address and payer_address.strip().lower() != bound_payer:
                return False, "Payer address does not match quote_hash bound payer_address."

            recomputed = self._compute_quote_hash({
                "work_order_id": issued["work_order_id"],
                "tool_name": issued["tool_name"],
                "amount_units": issued["amount_units"],
                "recipient_address": issued["recipient_address"],
                "token_contract": issued["token_contract"],
                "chain_id": issued["chain_id"],
                "created_at_epoch": issued["created_at_epoch"],
                "expires_at_epoch": issued["expires_at_epoch"],
                "payer_address": issued["payer_address"],
            })
            if not hmac.compare_digest(recomputed.lower(), q_hash):
                return False, "Invalid or tampered HMAC quote_hash."

        return True, "OK"

    def _consume_work_order(self, work_order_id: Optional[str]) -> None:
        wo_id = (work_order_id or "").strip()
        if not wo_id:
            return
        with self._quote_lock:
            self._consumed_work_orders.add(wo_id)

    @staticmethod
    def parse_x402_payment_header(header_value: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Parses Coinbase x402 v1 PAYMENT-SIGNATURE / X-PAYMENT base64-encoded JSON header.
        Returns normalized dict if valid x402 EIP-3009 payload, else None.
        """
        if not header_value or not isinstance(header_value, str):
            return None
        raw = header_value.strip()
        if not raw:
            return None

        parsed: Any = None
        if raw.startswith("{"):
            try:
                parsed = json.loads(raw)
            except Exception:
                return None
        else:
            # Pad base64 if needed
            padded = raw + "=" * (-len(raw) % 4)
            for decoder in (base64.b64decode, base64.urlsafe_b64decode):
                try:
                    decoded = decoder(padded.encode("ascii")).decode("utf-8")
                    parsed = json.loads(decoded)
                    break
                except Exception:
                    continue

        if not isinstance(parsed, dict):
            return None

        payload = parsed.get("payload")
        if not isinstance(payload, dict):
            return None
        auth = payload.get("authorization")
        sig = payload.get("signature")
        if not isinstance(auth, dict) or not isinstance(sig, str) or not sig.strip():
            return None

        required_auth = ("from", "to", "value", "validAfter", "validBefore", "nonce")
        if not all(k in auth for k in required_auth):
            return None

        return {
            "x402Version": int(parsed.get("x402Version", 1)),
            "scheme": str(parsed.get("scheme", "")).strip().lower(),
            "network": str(parsed.get("network", "")).strip().lower(),
            "signature": sig.strip(),
            "authorization": auth,
            "extra": parsed.get("extra") if isinstance(parsed.get("extra"), dict) else (
                payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
            ),
            "raw": parsed,
        }

    def verify_x402_eip3009_payment(
        self,
        payment_header: str,
        expected_price_usdc: float,
        tool_name: str,
        client_agent_id: str = "anonymous_agent",
        client_user_agent: str = "AI-Agent-Client/1.0",
        work_order_id: Optional[str] = None,
        quote_hash: Optional[str] = None,
        verify_with_facilitator: Optional[bool] = None,
        facilitator_post: Optional[Callable[..., Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies a Coinbase x402 v1 EIP-3009 transferWithAuthorization payment header
        (gasless 1-RTT settlement via EIP-712 signature + optional Facilitator /verify & /settle).
        """
        parsed = self.parse_x402_payment_header(payment_header)
        if not parsed:
            return False, {"error": "Invalid x402 v1 EIP-3009 PAYMENT-SIGNATURE / X-PAYMENT header."}

        if parsed["scheme"] != "exact":
            return False, {"error": f"Unsupported x402 scheme '{parsed['scheme']}'; expected 'exact'."}
        if parsed["network"] not in ("base", "eip155:8453", "base-mainnet"):
            return False, {"error": f"Unsupported x402 network '{parsed['network']}'; expected 'base'."}

        auth = parsed["authorization"]
        payer = str(auth.get("from", "")).strip()
        recipient = str(auth.get("to", "")).strip()
        nonce = str(auth.get("nonce", "")).strip()
        if not re.match(r"^0x[0-9a-fA-F]{40}$", payer) or not re.match(r"^0x[0-9a-fA-F]{40}$", recipient):
            return False, {"error": "Invalid EVM address in EIP-3009 authorization."}
        if not re.match(r"^0x[0-9a-fA-F]{64}$", nonce):
            return False, {"error": "Invalid 32-byte hex nonce in EIP-3009 authorization."}

        if recipient.lower() != self.recipient_wallet.lower():
            return False, {"error": "EIP-3009 authorization recipient does not match SOUQ recipient_wallet."}

        if payer.lower() in self.restricted_addresses:
            return False, {
                "error": "Payment Rejected: Restricted Source",
                "payer_address": payer,
            }

        try:
            value_units = int(str(auth["value"]))
            valid_after = int(str(auth["validAfter"]))
            valid_before = int(str(auth["validBefore"]))
        except (TypeError, ValueError):
            return False, {"error": "Invalid numeric fields in EIP-3009 authorization."}

        expected_units = int(round(expected_price_usdc * 1e6))
        if value_units < expected_units:
            return False, {
                "error": f"Insufficient EIP-3009 USDC value: received {value_units}, required {expected_units}."
            }

        now_ts = int(time.time())
        if now_ts < valid_after:
            return False, {"error": "EIP-3009 authorization is not yet valid (validAfter in future)."}
        if now_ts >= valid_before:
            return False, {"error": "EIP-3009 authorization has expired (validBefore passed)."}

        # Optional quote_hash / work_order_id binding
        extra = parsed.get("extra") or {}
        eff_wo = work_order_id or extra.get("work_order_id")
        eff_qh = quote_hash or extra.get("quote_hash")
        if eff_wo or eff_qh:
            q_ok, q_err = self.verify_quote_binding(
                work_order_id=str(eff_wo or ""),
                quote_hash=str(eff_qh or ""),
                tool_name=tool_name,
                expected_price_usdc=expected_price_usdc,
                payer_address=payer,
                now_epoch=now_ts,
            )
            if not q_ok:
                return False, {"error": "Quote Binding Rejected", "message": q_err}

        # Replay protection on EIP-3009 (payer, nonce)
        nullifier_key = f"eip3009:{payer.lower()}:{nonce.lower()}"
        if self._is_tx_already_used(nullifier_key):
            return False, {
                "error": "Payment Nullified",
                "message": "This EIP-3009 authorization nonce has already been redeemed.",
                "tx_hash": nullifier_key,
            }

        # Cryptographic EIP-712 TransferWithAuthorization signature verification
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "TransferWithAuthorization": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "validAfter", "type": "uint256"},
                    {"name": "validBefore", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"},
                ],
            },
            "primaryType": "TransferWithAuthorization",
            "domain": {
                "name": "USD Coin",
                "version": "2",
                "chainId": 8453,
                "verifyingContract": Web3.to_checksum_address(self.usdc_contract),
            },
            "message": {
                "from": Web3.to_checksum_address(payer),
                "to": Web3.to_checksum_address(recipient),
                "value": value_units,
                "validAfter": valid_after,
                "validBefore": valid_before,
                "nonce": bytes.fromhex(nonce[2:]),
            },
        }
        try:
            signable = encode_typed_data(full_message=typed_data)
            recovered = Account.recover_message(signable, signature=parsed["signature"])
        except Exception as exc:
            return False, {"error": f"Invalid EIP-712 TransferWithAuthorization signature: {exc}"}

        if not recovered or recovered.lower() != payer.lower():
            return False, {"error": "EIP-712 signature signer does not match EIP-3009 'from' address."}

        use_facilitator = (
            verify_with_facilitator
            if verify_with_facilitator is not None
            else os.getenv("SOUQ_X402_FACILITATOR_VERIFY", "false").strip().lower() == "true"
        )
        settlement_tx = nullifier_key
        if use_facilitator:
            post_fn = facilitator_post or requests.post
            req_payload = {
                "x402Version": 1,
                "paymentHeader": payment_header,
                "paymentRequirements": {
                    "scheme": "exact",
                    "network": "base",
                    "maxAmountRequired": str(expected_units),
                    "payTo": self.recipient_wallet,
                    "asset": self.usdc_contract,
                },
            }
            try:
                v_resp = post_fn(f"{self.facilitator_url}/verify", json=req_payload, timeout=8)
                v_data = v_resp.json() if hasattr(v_resp, "json") else {}
                if getattr(v_resp, "status_code", 500) >= 400 or not v_data.get("isValid"):
                    return False, {
                        "error": "Facilitator verification rejected EIP-3009 payment.",
                        "details": v_data,
                    }
                s_resp = post_fn(f"{self.facilitator_url}/settle", json=req_payload, timeout=12)
                s_data = s_resp.json() if hasattr(s_resp, "json") else {}
                if getattr(s_resp, "status_code", 500) >= 400 or not s_data.get("success", True):
                    return False, {
                        "error": "Facilitator settlement failed for EIP-3009 payment.",
                        "details": s_data,
                    }
                tx_from_fac = s_data.get("txHash") or s_data.get("transaction")
                if isinstance(tx_from_fac, str) and tx_from_fac.strip():
                    settlement_tx = tx_from_fac.strip().lower()
            except Exception as exc:
                return False, {"error": f"x402 Facilitator request failed: {exc}"}

        return True, {
            "status": "PRECHECK_VERIFIED",
            "tx_hash": settlement_tx,
            "eip3009_nullifier": nullifier_key,
            "payer_address": payer.lower(),
            "amount_paid_usdc": round(value_units / 1e6, 6),
            "gas_fee_eth": 0.0,
            "is_simulated": False,
            "tool_name": tool_name,
            "payment_protocol": "x402_eip3009",
            "work_order_id": eff_wo,
            "quote_hash": eff_qh,
        }

    @staticmethod
    def is_valid_tx_hash(tx_hash: Optional[str]) -> bool:
        if not tx_hash or not isinstance(tx_hash, str):
            return False
        canonical = tx_hash.strip().lower()
        return bool(TX_HASH_REGEX.match(canonical))

    def _is_tx_already_used(self, tx_hash: str) -> bool:
        tx_norm = (tx_hash or "").strip().lower()
        if not tx_norm:
            return False
        return (
            self.receipt_engine.is_tx_already_redeemed(tx_norm)
            or self.api_key_ledger.is_reference_redeemed(tx_norm)
            or self._is_eip3009_nullifier_used(tx_norm)
        )

    def _fetch_tx_context(self, tx_hash: str) -> Tuple[Any, Any]:
        """
        Fetches (tx_receipt, web3_instance) with multi-RPC failover on transport errors.
        Preserves mocked self.web3 behavior in offline tests without leaking live RPC calls.
        """
        tx_norm = (tx_hash or "").strip().lower()
        try:
            return self.web3.eth.get_transaction_receipt(tx_norm), self.web3
        except Exception as primary_err:
            is_mocked = (
                "unittest.mock" in type(self.web3).__module__
                or "unittest.mock" in type(self.web3.eth.get_transaction_receipt).__module__
            )
            if is_mocked or self._explicit_rpc:
                raise primary_err

            last_err: Exception = primary_err
            for fallback_url in self.rpc_urls:
                if fallback_url == self.rpc_url:
                    continue
                try:
                    w3 = Web3(Web3.HTTPProvider(fallback_url, request_kwargs=RPC_REQUEST_KWARGS))
                    receipt = w3.eth.get_transaction_receipt(tx_norm)
                    if receipt is not None:
                        return receipt, w3
                except Exception as err:
                    last_err = err
            raise last_err

    def _fetch_tx_receipt(self, tx_hash: str) -> Any:
        receipt, _ = self._fetch_tx_context(tx_hash)
        return receipt

    def _verify_onchain_receipt(
        self,
        tx_hash: str,
        expected_units: int,
        max_age_seconds: int,
        payer_signature: Optional[str] = None,
        payer_challenge: Optional[str] = None,
    ) -> Tuple[bool, str, int, float, str]:
        """
        Full Base L2 on-chain verification:
        status == 1, chain_id == 8453 (when numeric), confirmations >= confirmation_blocks,
        block timestamp freshness <= max_age_seconds, actual gas fee, ERC-20 USDC transfer,
        and optional EIP-191 payer ownership signature.
        """
        tx_receipt, w3 = self._fetch_tx_context(tx_hash)
        if not tx_receipt or tx_receipt.get("status") != 1:
            return False, "", 0, 0.00002, "Invalid or unconfirmed transaction on Base."

        try:
            chain_id = w3.eth.chain_id
        except Exception:
            chain_id = None
        if isinstance(chain_id, int) and not isinstance(chain_id, bool) and chain_id != 8453:
            return False, "", 0, 0.00002, f"Wrong chain ID {chain_id}; expected Base mainnet (8453)."

        receipt_block = tx_receipt.get("blockNumber")
        if isinstance(receipt_block, int) and not isinstance(receipt_block, bool):
            try:
                latest_block = w3.eth.block_number
            except Exception:
                latest_block = None
            if isinstance(latest_block, int) and not isinstance(latest_block, bool):
                confs = latest_block - receipt_block
                if confs < self.confirmation_blocks:
                    return (
                        False,
                        "",
                        0,
                        0.00002,
                        f"Transaction has {max(0, confs)} confirmations; requires at least {self.confirmation_blocks}.",
                    )

            try:
                block_info = w3.eth.get_block(receipt_block)
            except Exception:
                block_info = None
            if block_info is not None:
                ts = (
                    block_info.get("timestamp")
                    if isinstance(block_info, dict)
                    else getattr(block_info, "timestamp", None)
                )
                if isinstance(ts, (int, float)) and not isinstance(ts, bool):
                    age = time.time() - float(ts)
                    if age > max_age_seconds:
                        return (
                            False,
                            "",
                            0,
                            0.00002,
                            f"Transaction expired (age {int(age)}s exceeds max {max_age_seconds}s).",
                        )

        gas_used = tx_receipt.get("gasUsed")
        eff_gas_price = tx_receipt.get("effectiveGasPrice")
        if (
            isinstance(gas_used, (int, float))
            and not isinstance(gas_used, bool)
            and isinstance(eff_gas_price, (int, float))
            and not isinstance(eff_gas_price, bool)
        ):
            gas_fee_eth = float((gas_used * eff_gas_price) / 1e18)
        else:
            gas_fee_eth = 0.00002

        valid, payer, units, err_msg = self._verify_erc20_usdc_transfer_units(tx_receipt, expected_units)
        if not valid:
            return False, "", 0, gas_fee_eth, err_msg

        if payer_signature is not None:
            if not payer_challenge:
                return False, payer, 0, gas_fee_eth, "payer_challenge is required when payer_signature is provided."
            try:
                msg = encode_defunct(text=payer_challenge)
                recovered = Account.recover_message(msg, signature=payer_signature)
            except Exception as sig_err:
                return False, payer, 0, gas_fee_eth, f"Invalid EIP-191 payer_signature: {sig_err}"
            if not recovered or recovered.lower() != payer.lower():
                return False, payer, 0, gas_fee_eth, "EIP-191 payer_signature does not match on-chain USDC sender."

        return True, payer, units, gas_fee_eth, ""

    def _verify_erc20_usdc_transfer_units(
        self, tx_receipt: Any, expected_units: int
    ) -> Tuple[bool, str, int, str]:
        """
        Forensically inspects transaction logs to confirm:
        1. Emitted by official Base USDC contract
        2. ERC-20 Transfer event to our exact recipient wallet
        3. Total amount transferred >= expected_units
        Returns: (is_valid, payer_address, transferred_units, error_message)
        """
        target_contract = self.usdc_contract.lower()
        target_recipient_clean = self.recipient_wallet.lower().replace("0x", "").rjust(64, "0")

        logs = tx_receipt.get("logs", [])
        matching_units = 0
        primary_payer = ""

        for log in logs:
            log_address = str(log.get("address", "")).lower()
            if log_address != target_contract:
                continue

            topics = [
                t.hex().lower() if hasattr(t, "hex") else str(t).lower()
                for t in log.get("topics", [])
            ]
            if len(topics) < 3:
                continue

            topic0 = topics[0] if topics[0].startswith("0x") else f"0x{topics[0]}"
            if topic0 != ERC20_TRANSFER_TOPIC:
                continue

            to_topic = topics[2].replace("0x", "")
            if to_topic != target_recipient_clean:
                continue

            raw_data = log.get("data", "0x0")
            data_hex = raw_data.hex() if hasattr(raw_data, "hex") else str(raw_data)
            data_hex = data_hex.replace("0x", "") or "0"
            transferred_units = int(data_hex, 16)

            if transferred_units > 0:
                from_topic = topics[1].replace("0x", "")
                if not primary_payer:
                    primary_payer = "0x" + from_topic[-40:]
                matching_units += transferred_units

        if matching_units >= expected_units and primary_payer:
            return True, primary_payer, matching_units, ""

        if matching_units > 0:
            return (
                False,
                primary_payer,
                matching_units,
                f"Insufficient Base USDC transferred: received {matching_units / 1e6:.6f} USDC, required {expected_units / 1e6:.6f} USDC.",
            )

        return False, "", 0, "No matching Base USDC transfer to recipient wallet found in transaction logs."

    def _verify_erc20_usdc_transfer(self, tx_receipt: Any, expected_units: int) -> Tuple[bool, str, str]:
        """Backward-compatible wrapper returning (is_valid, payer_address, error_message)."""
        is_valid, payer, _, err_msg = self._verify_erc20_usdc_transfer_units(tx_receipt, expected_units)
        return is_valid, payer, err_msg

    def verify_usdc_topup(
        self,
        tx_hash: str,
        min_usd: float = 0.50,
        simulate_test: bool = False,
        simulated_amount_usd: float = 5.0,
        payer_signature: Optional[str] = None,
        payer_challenge: Optional[str] = None,
    ) -> Tuple[bool, str, float, str]:
        """
        Verifies a one-time Base USDC deposit for issuing or topping up a prepaid SOUQ API key.
        Returns: (is_valid, payer_address, credited_usd, error_message)
        """
        tx_hash = (tx_hash or "").strip().lower()
        if not tx_hash:
            return False, "", 0.0, "Missing tx_hash."

        tx_lock = _get_tx_lock(tx_hash)
        with tx_lock.lock:
            if self._is_tx_already_used(tx_hash):
                return False, "", 0.0, "Transaction hash has already been redeemed."

            if simulate_test:
                if simulated_amount_usd < min_usd:
                    return False, "", 0.0, f"Simulated top-up below minimum ${min_usd:.2f}."
                return True, "0x0000000000000000000000000000000000000000", round(float(simulated_amount_usd), 6), ""

            if not self.is_valid_tx_hash(tx_hash):
                return False, "", 0.0, "Invalid Base transaction hash format (expected 0x + 64 hex chars)."

            min_units = int(round(min_usd * 1e6))
            try:
                valid, payer, units, _, err_msg = self._verify_onchain_receipt(
                    tx_hash,
                    min_units,
                    max_age_seconds=self.max_topup_tx_age_seconds,
                    payer_signature=payer_signature,
                    payer_challenge=payer_challenge,
                )
                if not valid:
                    return False, "", 0.0, err_msg

                if payer.lower() in self.restricted_addresses:
                    return False, payer, 0.0, "Payment rejected from restricted source address."

                return True, payer, round(units / 1e6, 6), ""
            except Exception as e:
                return False, "", 0.0, f"On-chain Base verification failed: {str(e)}"

    def verify_payment_precheck(
        self,
        tx_hash: str,
        expected_price_usdc: float,
        tool_name: str,
        client_agent_id: str = "anonymous_agent",
        client_user_agent: str = "AI-Agent-Client/1.0",
        simulate_test: bool = False,
        payer_signature: Optional[str] = None,
        payer_challenge: Optional[str] = None,
        work_order_id: Optional[str] = None,
        quote_hash: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies anti-replay, optional HMAC quote_hash/work_order_id binding, and Base USDC settlement
        WITHOUT consuming the tx_hash receipt yet.
        Allows callers to execute the paid tool before committing the nullifier receipt.
        """
        start_t = time.time()
        tx_hash = (tx_hash or "").strip().lower()
        tx_lock = _get_tx_lock(tx_hash)

        with tx_lock.lock:
            if self._is_tx_already_used(tx_hash):
                latency = int((time.time() - start_t) * 1000)
                self.negotiation_tracker.log_negotiation(
                    client_agent_id=client_agent_id,
                    client_user_agent=client_user_agent,
                    tool_requested=tool_name,
                    initial_quote_usd=expected_price_usdc,
                    settled_price_usd=None,
                    payment_protocol="x402_http",
                    outcome="REJECTED_REPLAY_ATTEMPT",
                    latency_ms=latency,
                    rejection_reason=f"Transaction {tx_hash} already redeemed.",
                )
                return False, {
                    "error": "Payment Nullified",
                    "message": "This transaction hash has already been redeemed.",
                    "tx_hash": tx_hash,
                }

            if not simulate_test and not self.is_valid_tx_hash(tx_hash):
                return False, {
                    "error": "Invalid Transaction Hash",
                    "message": "Expected a valid 66-character Base transaction hash (0x + 64 hex chars).",
                    "tx_hash": tx_hash,
                }

            payer_address = ""
            gas_fee_eth = 0.00002
            expected_units = int(round(expected_price_usdc * 1e6))

            if simulate_test:
                payer_address = "0x0000000000000000000000000000000000000000"
            else:
                try:
                    valid_transfer, verified_payer, _, gas_fee_eth, err_msg = self._verify_onchain_receipt(
                        tx_hash,
                        expected_units,
                        max_age_seconds=self.max_tx_age_seconds,
                        payer_signature=payer_signature,
                        payer_challenge=payer_challenge,
                    )
                    if not valid_transfer:
                        return False, {"error": err_msg}

                    if verified_payer.lower() in self.restricted_addresses:
                        latency = int((time.time() - start_t) * 1000)
                        self.negotiation_tracker.log_negotiation(
                            client_agent_id=client_agent_id,
                            client_user_agent=client_user_agent,
                            tool_requested=tool_name,
                            initial_quote_usd=expected_price_usdc,
                            settled_price_usd=None,
                            payment_protocol="x402_http",
                            outcome="REJECTED_AML_RESTRICTED_SOURCE",
                            latency_ms=latency,
                            rejection_reason=f"Payer {verified_payer} is on the restricted source deny-list.",
                        )
                        return False, {
                            "error": "Payment Rejected: Restricted Source",
                            "message": "Funds from restricted or unverified third-party sources cannot be accepted under terms of use compliance.",
                            "payer_address": verified_payer,
                        }

                    payer_address = verified_payer
                except Exception as e:
                    return False, {"error": f"On-chain Base verification failed: {str(e)}"}

            if work_order_id or quote_hash:
                q_ok, q_err = self.verify_quote_binding(
                    work_order_id=str(work_order_id or ""),
                    quote_hash=str(quote_hash or ""),
                    tool_name=tool_name,
                    expected_price_usdc=expected_price_usdc,
                    payer_address=payer_address or None,
                )
                if not q_ok:
                    return False, {
                        "error": "Quote Binding Rejected",
                        "message": q_err,
                        "work_order_id": work_order_id,
                    }

            return True, {
                "status": "PRECHECK_VERIFIED",
                "tx_hash": tx_hash,
                "payer_address": payer_address,
                "amount_paid_usdc": expected_price_usdc,
                "gas_fee_eth": gas_fee_eth,
                "is_simulated": bool(simulate_test),
                "tool_name": tool_name,
                "work_order_id": work_order_id,
                "quote_hash": quote_hash,
            }

    def commit_payment_settlement(
        self,
        tx_hash: str,
        expected_price_usdc: float,
        tool_name: str,
        payload_data: Any,
        payer_address: str,
        gas_fee_eth: float = 0.00002,
        is_simulated: bool = False,
        client_agent_id: str = "anonymous_agent",
        client_user_agent: str = "AI-Agent-Client/1.0",
        start_t: Optional[float] = None,
        work_order_id: Optional[str] = None,
        quote_hash: Optional[str] = None,
        payment_protocol: str = "x402_http",
        eip3009_nullifier: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Atomically re-checks anti-replay (on both tx_hash and eip3009_nullifier), records the receipt
        nullifier, consumes work_order_id, and logs SETTLED telemetry.
        """
        t0 = start_t if start_t is not None else time.time()
        tx_hash = (tx_hash or "").strip().lower()
        norm_nullifier = (eip3009_nullifier or "").strip().lower()
        tx_lock = _get_tx_lock(norm_nullifier or tx_hash)

        with tx_lock.lock:
            if self._is_tx_already_used(tx_hash) or (norm_nullifier and self._is_tx_already_used(norm_nullifier)):
                latency = int((time.time() - t0) * 1000)
                self.negotiation_tracker.log_negotiation(
                    client_agent_id=client_agent_id,
                    client_user_agent=client_user_agent,
                    tool_requested=tool_name,
                    initial_quote_usd=expected_price_usdc,
                    settled_price_usd=None,
                    payment_protocol=payment_protocol,
                    outcome="REJECTED_REPLAY_ATTEMPT",
                    latency_ms=latency,
                    rejection_reason=f"Transaction {tx_hash} already redeemed.",
                )
                return False, {
                    "error": "Payment Nullified",
                    "message": "This transaction hash or EIP-3009 authorization has already been redeemed.",
                    "tx_hash": tx_hash,
                }

            if work_order_id or quote_hash:
                q_ok, q_err = self.verify_quote_binding(
                    work_order_id=str(work_order_id or ""),
                    quote_hash=str(quote_hash or ""),
                    tool_name=tool_name,
                    expected_price_usdc=expected_price_usdc,
                    payer_address=payer_address or None,
                )
                if not q_ok:
                    return False, {
                        "error": "Quote Binding Rejected",
                        "message": q_err,
                        "work_order_id": work_order_id,
                    }

            receipt = self.receipt_engine.generate_receipt(
                tx_hash=tx_hash,
                payer_address=payer_address,
                recipient_address=self.recipient_wallet,
                amount_usdc=expected_price_usdc,
                product_id=tool_name,
                service_rendered=f"FastMCP Tool Invocation: {tool_name}",
                payload_data=payload_data,
                chain="Base",
                token_contract=self.usdc_contract,
                gas_fee_eth=gas_fee_eth,
                is_simulated=bool(is_simulated),
            )
            self._consume_work_order(work_order_id)
            if norm_nullifier:
                self._record_eip3009_nullifier(norm_nullifier, tx_hash)

            latency = int((time.time() - t0) * 1000)
            self.negotiation_tracker.log_negotiation(
                client_agent_id=client_agent_id,
                client_user_agent=client_user_agent,
                tool_requested=tool_name,
                initial_quote_usd=expected_price_usdc,
                settled_price_usd=expected_price_usdc,
                payment_protocol=payment_protocol,
                outcome="SETTLED",
                latency_ms=latency,
                metadata={
                    "receipt_id": receipt["receipt_id"],
                    "work_order_id": work_order_id,
                    "quote_hash": quote_hash,
                },
            )

            return True, {
                "status": "SETTLED",
                "receipt_id": receipt["receipt_id"],
                "amount_paid_usdc": expected_price_usdc,
                "tx_hash": tx_hash,
                "work_order_id": work_order_id,
                "quote_hash": quote_hash,
                "payment_protocol": payment_protocol,
            }

    def verify_payment_and_settle(
        self,
        tx_hash: str,
        expected_price_usdc: float,
        tool_name: str,
        payload_data: Any,
        client_agent_id: str = "anonymous_agent",
        client_user_agent: str = "AI-Agent-Client/1.0",
        simulate_test: bool = False,
        payer_signature: Optional[str] = None,
        payer_challenge: Optional[str] = None,
        work_order_id: Optional[str] = None,
        quote_hash: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies on-chain Base USDC payment or explicit local test simulation,
        executes anti-replay check, and generates an immutable tax receipt atomically.
        """
        start_t = time.time()
        tx_hash = (tx_hash or "").strip().lower()
        tx_lock = _get_tx_lock(tx_hash)

        with tx_lock.lock:
            ok, precheck_info = self.verify_payment_precheck(
                tx_hash=tx_hash,
                expected_price_usdc=expected_price_usdc,
                tool_name=tool_name,
                client_agent_id=client_agent_id,
                client_user_agent=client_user_agent,
                simulate_test=simulate_test,
                payer_signature=payer_signature,
                payer_challenge=payer_challenge,
                work_order_id=work_order_id,
                quote_hash=quote_hash,
            )
            if not ok:
                return False, precheck_info

            return self.commit_payment_settlement(
                tx_hash=tx_hash,
                expected_price_usdc=expected_price_usdc,
                tool_name=tool_name,
                payload_data=payload_data,
                payer_address=precheck_info["payer_address"],
                gas_fee_eth=precheck_info["gas_fee_eth"],
                is_simulated=precheck_info["is_simulated"],
                client_agent_id=client_agent_id,
                client_user_agent=client_user_agent,
                start_t=start_t,
                work_order_id=work_order_id,
                quote_hash=quote_hash,
            )
