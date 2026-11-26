import os
import re
import json
import secrets
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple

try:
    from agents.treasury.wallet_gate import WalletEnforcementGate, WalletGateError
except ImportError:  # Standalone PyPI install without swarm repo
    WalletEnforcementGate = None  # type: ignore[assignment]
    WalletGateError = PermissionError  # type: ignore[assignment]

DEFAULT_EDGE_ENDPOINT = os.getenv(
    "SOUQ_ENDPOINT",
    "https://written-emera-arapython-bf7436a4.apps.mistral.run",
)
PINNED_TREASURY_WALLET = "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF"
DEFAULT_WALLET_GATE_LEDGER = os.path.expanduser("~/.cache/souq_mcp/wallet_gate_ledger.json")


class PaymentRequiredError(PermissionError):
    """Raised when an HTTP 402 payment challenge requires funding or automatic settlement."""


class _SouqHTTPError(Exception):
    """Internal normalized HTTP error carrying parsed JSON or summarized proxy text."""

    def __init__(
        self,
        status_code: int,
        headers: Dict[str, str],
        payload: Optional[Dict[str, Any]],
        summary: str,
    ):
        super().__init__(summary)
        self.status_code = status_code
        self.headers = headers
        self.payload = payload
        self.summary = summary


class SouqClient:
    """
    Zero-dependency Python Client SDK for SOUQ Autonomous Commerce Swarm.
    Supports:
    - 1 daily free evaluation call per client IP
    - Prepaid X-API-Key micro-credits (SOUQ_API_KEY)
    - Autonomous x402 Base L2 USDC on-chain settlement (SOUQ_AGENT_PRIVATE_KEY)
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        private_key: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        allowed_recipients: Optional[Any] = None,
        wallet_ledger_path: Optional[str] = None,
    ):
        chosen_endpoint = endpoint or os.getenv("SOUQ_ENDPOINT") or DEFAULT_EDGE_ENDPOINT
        self.endpoint = chosen_endpoint.rstrip("/")
        self.api_url = f"{self.endpoint}/api/tools/call"
        self.private_key = private_key or os.getenv("SOUQ_AGENT_PRIVATE_KEY")
        self.api_key = api_key or os.getenv("SOUQ_API_KEY")
        self.timeout = timeout
        if allowed_recipients is not None:
            self.allowed_recipients = [str(a).strip() for a in allowed_recipients if str(a).strip()]
        else:
            env_allowed = os.getenv("SOUQ_ALLOWED_RECIPIENTS", "").strip()
            self.allowed_recipients = (
                [a.strip() for a in env_allowed.split(",") if a.strip()]
                if env_allowed
                else [PINNED_TREASURY_WALLET]
            )
        self.wallet_ledger_path = (
            wallet_ledger_path
            or os.getenv("SOUQ_WALLET_GATE_LEDGER")
            or DEFAULT_WALLET_GATE_LEDGER
        )

    def _base_headers(self, include_auth: bool = True) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "souq-mcp-client/0.3.0",
        }
        if include_auth and self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    @staticmethod
    def _decode_body(raw_bytes: Optional[bytes]) -> str:
        if not raw_bytes:
            return ""
        return raw_bytes.decode("utf-8", errors="replace")

    @staticmethod
    def _summarize_error_body(status_code: int, body_text: str) -> Tuple[Optional[Dict[str, Any]], str]:
        stripped = (body_text or "").strip()
        if not stripped:
            return None, f"Empty response body (HTTP {status_code})"
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                msg = parsed.get("message") or parsed.get("error")
                if msg:
                    details = parsed.get("details")
                    return parsed, f"{msg} ({details})" if details else str(msg)
                return parsed, json.dumps(parsed)[:240]
            return None, str(parsed)[:240]
        except Exception:
            title_match = re.search(r"<title[^>]*>(.*?)</title>", stripped, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = re.sub(r"\s+", " ", title_match.group(1)).strip()
                if title:
                    return None, f"Non-JSON response (HTTP {status_code}): {title}"
            plain = re.sub(r"<[^>]+>", " ", stripped)
            plain = re.sub(r"\s+", " ", plain).strip()
            return None, f"Non-JSON response (HTTP {status_code}): {plain[:240]}"

    def _request_json(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        allow_empty_200: bool = False,
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        req_data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=req_data, headers=headers or {}, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status_code = getattr(resp, "status", 200)
                headers_dict = dict(resp.headers) if resp.headers else {}
                body_text = self._decode_body(resp.read())
        except urllib.error.HTTPError as e:
            err_headers = dict(e.headers) if e.headers else {}
            raw_err = e.read() if hasattr(e, "read") else b""
            err_body = self._decode_body(raw_err)
            parsed, summary = self._summarize_error_body(e.code, err_body)
            raise _SouqHTTPError(e.code, err_headers, parsed, summary) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error calling {url}: {e.reason}") from e
        except TimeoutError as e:
            raise RuntimeError(f"Request timed out after {self.timeout}s calling {url}") from e

        if status_code >= 400:
            parsed, summary = self._summarize_error_body(status_code, body_text)
            raise _SouqHTTPError(status_code, headers_dict, parsed, summary)

        if not body_text.strip():
            if allow_empty_200:
                return status_code, headers_dict, {}
            raise RuntimeError(f"Empty response from {url} (HTTP {status_code})")

        try:
            parsed = json.loads(body_text)
        except Exception as e:
            _, summary = self._summarize_error_body(status_code, body_text)
            raise RuntimeError(f"Invalid JSON from {url}: {summary}") from e

        if not isinstance(parsed, dict):
            return status_code, headers_dict, {"result": parsed}

        return status_code, headers_dict, parsed

    def call_tool(
        self,
        tool: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Executes a remote SOUQ tool call.
        Accepts both dict syntax `call_tool("name", {"arg": val})` and kwargs `call_tool("name", arg=val)`.
        """
        merged: Dict[str, Any] = {}
        if params is not None:
            if not isinstance(params, dict):
                raise TypeError("params must be a dictionary of tool arguments")
            merged.update(params)
        merged.update(kwargs)

        payload = {"tool": tool, **merged}
        headers = self._base_headers(include_auth=True)

        try:
            status_code, headers_dict, result = self._request_json(
                self.api_url,
                method="POST",
                headers=headers,
                payload=payload,
                allow_empty_200=True,
            )
            return {
                "data": result,
                "billing": headers_dict.get("X-Souq-Billing", "PAID"),
                "tokens_saved": headers_dict.get("X-Souq-Tokens-Saved"),
                "net_roi": headers_dict.get("X-Souq-Net-ROI"),
                "credit_remaining_usd": headers_dict.get("X-Souq-Credit-Remaining-USD"),
                "status_code": status_code,
            }
        except _SouqHTTPError as e:
            if e.status_code == 402:
                err_headers = e.headers
                challenge = e.payload or {"raw_error": e.summary}
                payment_details = challenge.get("payment_details") or {}
                price = (
                    err_headers.get("X-Souq-Price-USDC")
                    or payment_details.get("amount")
                    or "0.02"
                )
                recipient = (
                    err_headers.get("X-Souq-Recipient")
                    or payment_details.get("recipient_address")
                    or challenge.get("recipient")
                    or challenge.get("x402_recipient")
                )
                network = (
                    err_headers.get("X-Souq-Network")
                    or payment_details.get("chain")
                    or "Base"
                )

                if not self.private_key:
                    raise PaymentRequiredError(
                        f"SOUQ HTTP 402 Payment Required: {price} USDC on {network} -> recipient {recipient}. "
                        f"Fund a prepaid SOUQ_API_KEY at {self.endpoint}/#topup "
                        f"(API: POST {self.endpoint}/api/credits/topup) "
                        f"or set SOUQ_AGENT_PRIVATE_KEY / private_key for automatic Base USDC settlement."
                    )

                if not recipient:
                    raise RuntimeError(f"402 challenge missing recipient address: {challenge}")

                work_order_id = (
                    err_headers.get("X-Souq-Work-Order-Id")
                    or payment_details.get("work_order_id")
                    or challenge.get("work_order_id")
                    or f"wo_client_{secrets.token_hex(8)}"
                )
                quote_hash = (
                    err_headers.get("X-Souq-Quote-Hash")
                    or payment_details.get("quote_hash")
                    or challenge.get("quote_hash")
                )

                tx_hash = self._settle_usdc_payment(
                    recipient=recipient,
                    amount_usdc=float(price),
                    work_order_id=work_order_id,
                    quote_hash=quote_hash,
                )
                retry_payload = {
                    **payload,
                    "payment_tx_hash": tx_hash,
                    "tx_hash": tx_hash,
                    "work_order_id": work_order_id,
                }
                if quote_hash:
                    retry_payload["quote_hash"] = quote_hash
                retry_headers = {**self._base_headers(include_auth=False), "X-Payment-Tx": tx_hash}
                if work_order_id:
                    retry_headers["X-Souq-Work-Order-Id"] = str(work_order_id)
                if quote_hash:
                    retry_headers["X-Souq-Quote-Hash"] = str(quote_hash)
                try:
                    paid_status, _, paid_result = self._request_json(
                        self.api_url,
                        method="POST",
                        headers=retry_headers,
                        payload=retry_payload,
                    )
                except _SouqHTTPError as retry_err:
                    raise RuntimeError(
                        f"HTTP {retry_err.status_code} after payment settlement: {retry_err.summary}"
                    ) from retry_err
                return {
                    "data": paid_result,
                    "billing": "PAID_USDC_BASE",
                    "tx_hash": tx_hash,
                    "status_code": paid_status,
                }

            raise RuntimeError(f"HTTP {e.status_code}: {e.summary}") from e

    def call(
        self,
        tool: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Alias for `call_tool`."""
        return self.call_tool(tool, params, **kwargs)

    def list_tools(self) -> Dict[str, Any]:
        """Fetches the live SOUQ MCP tool manifest from `/.well-known/mcp.json`."""
        try:
            _, _, data = self._request_json(
                f"{self.endpoint}/.well-known/mcp.json",
                headers={"User-Agent": "souq-mcp-client/0.3.0"},
                method="GET",
            )
            return data
        except _SouqHTTPError as e:
            raise RuntimeError(f"HTTP {e.status_code}: {e.summary}") from e

    def balance(self) -> Dict[str, Any]:
        """Checks current balance & stats for the configured SOUQ_API_KEY, or returns public rail info."""
        if not self.api_key:
            try:
                _, _, catalog = self._request_json(
                    f"{self.endpoint}/api/catalog",
                    headers={"User-Agent": "souq-mcp-client/0.3.0"},
                    method="GET",
                )
            except _SouqHTTPError as e:
                raise RuntimeError(f"HTTP {e.status_code}: {e.summary}") from e
            return {
                "authenticated": False,
                "message": (
                    f"No SOUQ_API_KEY configured. Free daily 1-call trial per IP is active, "
                    f"or fund a prepaid API key at {self.endpoint}/#topup."
                ),
                "recipient_wallet": catalog.get("recipient_wallet"),
                "topup_url": f"{self.endpoint}/#topup",
                "topup_endpoint": f"{self.endpoint}/api/credits/topup",
                "tools_count": len(catalog.get("tools", [])),
            }

        try:
            _, _, data = self._request_json(
                f"{self.endpoint}/api/credits/balance",
                headers={"X-API-Key": self.api_key, "User-Agent": "souq-mcp-client/0.3.0"},
                method="GET",
            )
            return {"authenticated": True, **data}
        except _SouqHTTPError as e:
            raise RuntimeError(f"HTTP {e.status_code}: {e.summary}") from e

    def topup_credits(
        self,
        tx_hash: Optional[str] = None,
        amount_usdc: float = 5.0,
        label: str = "python-sdk",
    ) -> Dict[str, Any]:
        """
        Submits a Base USDC transfer (or uses an existing tx_hash) to /api/credits/topup,
        minting or refilling a prepaid X-API-Key on this SouqClient instance.
        """
        if not tx_hash:
            if not self.private_key:
                raise PermissionError(
                    "Pass an existing Base USDC tx_hash or set SOUQ_AGENT_PRIVATE_KEY to send USDC automatically."
                )
            try:
                _, _, catalog = self._request_json(
                    f"{self.endpoint}/api/catalog",
                    headers={"User-Agent": "souq-mcp-client/0.3.0"},
                    method="GET",
                )
            except _SouqHTTPError as e:
                raise RuntimeError(f"HTTP {e.status_code}: {e.summary}") from e
            recipient = catalog["recipient_wallet"]
            tx_hash = self._settle_usdc_payment(
                recipient=recipient,
                amount_usdc=amount_usdc,
                work_order_id=f"wo_topup_{secrets.token_hex(8)}",
                max_per_call_usd=max(float(amount_usdc), 5.0),
            )

        body: Dict[str, Any] = {"tx_hash": tx_hash, "label": label}
        if self.api_key:
            body["api_key"] = self.api_key

        try:
            _, _, res = self._request_json(
                f"{self.endpoint}/api/credits/topup",
                method="POST",
                headers=self._base_headers(include_auth=False),
                payload=body,
            )
        except _SouqHTTPError as e:
            raise RuntimeError(f"HTTP {e.status_code}: {e.summary}") from e

        if res.get("api_key"):
            self.api_key = res["api_key"]
        return res

    def _settle_usdc_payment(
        self,
        recipient: str,
        amount_usdc: float,
        work_order_id: Optional[str] = None,
        quote_hash: Optional[str] = None,
        max_per_call_usd: Optional[float] = None,
    ) -> str:
        """
        Signs, pre-simulates (eth_call), broadcasts, and confirms a Base L2 ERC-20 USDC transfer
        guarded by WalletEnforcementGate.
        """
        try:
            from web3 import Web3
            from eth_account import Account
        except ImportError:
            raise ImportError(
                "Automated x402 wallet settlement requires 'web3' and 'eth-account'. "
                "Install via: pip install 'souq-mcp[wallet]'"
            )

        wo_id = (work_order_id or f"wo_sdk_{secrets.token_hex(8)}").strip()
        gate = None
        if WalletEnforcementGate is not None:
            gate = WalletEnforcementGate(
                allowed_recipients=self.allowed_recipients,
                max_per_call_usd=max_per_call_usd,
                ledger_path=self.wallet_ledger_path,
            )
            gate.check_policy(
                recipient=recipient,
                amount_usdc=amount_usdc,
                work_order_id=wo_id,
                quote_hash=quote_hash,
            )

        rpc_url = os.getenv("BASE_RPC_URL", "https://base-rpc.publicnode.com")
        w3 = Web3(
            Web3.HTTPProvider(
                rpc_url,
                request_kwargs={"timeout": 15, "headers": {"User-Agent": "souq-mcp-client/0.3.0"}},
            )
        )
        account = Account.from_key(self.private_key)

        usdc_address = Web3.to_checksum_address(
            os.getenv("BASE_USDC_CONTRACT", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        )
        erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"},
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function",
            }
        ]

        usdc_contract = w3.eth.contract(address=usdc_address, abi=erc20_abi)
        amount_units = int(round(amount_usdc * 1_000_000))

        nonce = w3.eth.get_transaction_count(account.address, "pending")
        base_gas_price = max(int(w3.eth.gas_price), w3.to_wei(0.01, "gwei"))
        max_priority = w3.to_wei(0.005, "gwei")
        max_fee = int(base_gas_price * 2 + max_priority)

        tx = usdc_contract.functions.transfer(
            Web3.to_checksum_address(recipient),
            amount_units,
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 75000,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority,
            "chainId": 8453,
        })

        def _sign_tx(unsigned_tx: Dict[str, Any]) -> bytes:
            signed = account.sign_transaction(unsigned_tx)
            raw_tx = getattr(signed, "raw_transaction", getattr(signed, "rawTransaction", None))
            if raw_tx is None:
                raise RuntimeError("Unable to extract signed raw transaction bytes from eth-account object.")
            return raw_tx

        if gate is not None:
            tx_hash_hex = gate.authorize_and_broadcast(
                w3=w3,
                tx=tx,
                sign_fn=_sign_tx,
                recipient=recipient,
                amount_usdc=amount_usdc,
                work_order_id=wo_id,
                quote_hash=quote_hash,
            )
        else:
            # Standalone fallback: still enforce eth_call pre-simulation before broadcast
            w3.eth.call({"from": tx["from"], "to": tx["to"], "data": tx.get("data", b""), "value": tx.get("value", 0)})
            tx_hash_bytes = w3.eth.send_raw_transaction(_sign_tx(tx))
            tx_hash_hex = tx_hash_bytes.hex()
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = f"0x{tx_hash_hex}"

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=45)
        if receipt.get("status") != 1:
            raise RuntimeError(f"Base USDC transfer failed on-chain (tx={tx_hash_hex})")

        return tx_hash_hex

    # Convenience Tool Methods
    def compress(
        self,
        raw_content: str,
        max_compression: bool = True,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        extra: Dict[str, Any] = {"max_compression": max_compression}
        if mode is not None:
            extra["mode"] = mode
        return self.call_tool("token_context_compressor", raw_content=raw_content, **extra)

    def ast_slice(self, source_code: str, target_symbol: str) -> Dict[str, Any]:
        return self.call_tool("ast_structural_slicer", source_code=source_code, target_symbol=target_symbol)

    def microstructure(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        return self.call_tool("quant_microstructure_radar", symbol=symbol)

    def funding_arbitrage(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        return self.call_tool("cross_exchange_arbitrage_scanner", symbol=symbol)

    def simulate_slippage(self, symbol: str = "BTC/USDT", side: str = "BUY", trade_size_usd: float = 10000.0) -> Dict[str, Any]:
        return self.call_tool("orderbook_slippage_simulator", symbol=symbol, side=side, trade_size_usd=trade_size_usd)

    def whale_flow(self, symbol: str = "BTC/USDT", block_threshold_usd: float = 50000.0) -> Dict[str, Any]:
        return self.call_tool("smart_money_whale_flow_radar", symbol=symbol, block_threshold_usd=block_threshold_usd)

    def dev_cheatsheet(self, ecosystem: str = "openai") -> Dict[str, Any]:
        return self.call_tool("dev_api_cheatsheet_vault", ecosystem=ecosystem)

    def tech_trends(self, force_refresh: bool = False) -> Dict[str, Any]:
        return self.call_tool("daily_tech_ai_trends_radar", force_refresh=force_refresh)

    def prediction_arbitrage(self, asset: str = "BTC", limit: int = 5) -> Dict[str, Any]:
        return self.call_tool("prediction_market_arbitrage_radar", asset=asset, limit=limit)

    def security_scan(self, source_code: str) -> Dict[str, Any]:
        return self.call_tool("deep_ast_vulnerability_auditor", source_code=source_code)

    def verify_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        return self.call_tool("synthetic_schema_verifier", data=data, schema=schema)

    def prompt_firewall(self, text: str, strict_mode: bool = False) -> Dict[str, Any]:
        return self.call_tool("prompt_injection_firewall", text=text, strict_mode=strict_mode)

    def honeypot_radar(self, source_code: str = "", token_symbol: str = "TKN", contract_address: Optional[str] = None) -> Dict[str, Any]:
        return self.call_tool(
            "smart_contract_honeypot_radar",
            source_code=source_code,
            token_symbol=token_symbol,
            contract_address=contract_address,
        )

    def secret_scan(self, content: str, entropy_threshold: float = 4.2) -> Dict[str, Any]:
        return self.call_tool("secret_leak_scanner", content=content, entropy_threshold=entropy_threshold)

    def deep_ast_audit(self, source_code: str) -> Dict[str, Any]:
        return self.call_tool("deep_ast_vulnerability_auditor", source_code=source_code)

    def api_attack_surface(self, target_url: str, headers_to_check: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self.call_tool("api_attack_surface_scanner", target_url=target_url, headers_to_check=headers_to_check)
