import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

DEFAULT_EDGE_ENDPOINT = os.getenv(
    "SOUQ_ENDPOINT",
    "https://written-emera-arapython-bf7436a4.apps.mistral.run"
)


class SouqClient:
    """
    Zero-dependency Python Client SDK for SOUQ Autonomous Commerce Swarm.
    Provides sub-cent algorithmic intelligence and token-saving services
    with automatic x402 settlement and freemium trial fallback.
    """

    def __init__(
        self,
        endpoint: str = DEFAULT_EDGE_ENDPOINT,
        private_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_url = f"{self.endpoint}/api/tools/call"
        self.private_key = private_key or os.getenv("SOUQ_AGENT_PRIVATE_KEY")
        self.timeout = timeout

    def call_tool(self, tool: str, **kwargs) -> Dict[str, Any]:
        """
        Executes a remote SOUQ tool call.
        Automatically leverages the 1-free-call-per-day evaluation hook.
        If an HTTP 402 challenge is received and private_key is configured,
        executes cryptographic Base L2 USDC settlement.
        """
        payload = {"tool": tool, **kwargs}
        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "souq-mcp-client/0.1.0"
        }

        req = urllib.request.Request(self.api_url, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status_code = resp.status
                headers_dict = dict(resp.headers)
                body = resp.read().decode("utf-8")
                result = json.loads(body) if body else {}

                billing = headers_dict.get("X-Souq-Billing", "PAID")
                tokens_saved = headers_dict.get("X-Souq-Tokens-Saved")
                net_roi = headers_dict.get("X-Souq-Net-ROI")
                return {
                    "data": result,
                    "billing": billing,
                    "tokens_saved": tokens_saved,
                    "net_roi": net_roi,
                    "status_code": status_code
                }
        except urllib.error.HTTPError as e:
            err_headers = dict(e.headers)
            err_body = e.read().decode("utf-8")
            try:
                challenge = json.loads(err_body)
            except Exception:
                challenge = {"raw_error": err_body}

            if e.code == 402:
                price = err_headers.get("X-Souq-Price-USDC", "0.02")
                recipient = err_headers.get("X-Souq-Recipient", challenge.get("recipient"))
                network = err_headers.get("X-Souq-Network", challenge.get("network", "Base"))

                if not self.private_key:
                    raise PermissionError(
                        f"SOUQ HTTP 402 Challenge: Free evaluation call already consumed for this IP. "
                        f"Payment of {price} USDC on {network} required to recipient {recipient}. "
                        f"Configure 'private_key' on SouqClient or set SOUQ_AGENT_PRIVATE_KEY."
                    )

                # Execute settlement and retry with tx_hash
                tx_hash = self._settle_usdc_payment(
                    recipient=recipient,
                    amount_usdc=float(price)
                )
                payload["tx_hash"] = tx_hash
                retry_data = json.dumps(payload).encode("utf-8")
                retry_req = urllib.request.Request(self.api_url, data=retry_data, headers=headers, method="POST")
                with urllib.request.urlopen(retry_req, timeout=self.timeout) as paid_resp:
                    paid_body = paid_resp.read().decode("utf-8")
                    return {
                        "data": json.loads(paid_body),
                        "billing": "PAID_USDC_BASE",
                        "tx_hash": tx_hash,
                        "status_code": 200
                    }

            raise RuntimeError(f"HTTP {e.code}: {challenge}")

    def _settle_usdc_payment(self, recipient: str, amount_usdc: float) -> str:
        """
        Signs and submits an ERC20 transfer of USDC on Base L2 using private_key.
        """
        try:
            from web3 import Web3
            from eth_account import Account
        except ImportError:
            raise ImportError(
                "Automated x402 wallet settlement requires 'web3' and 'eth-account'. "
                "Install via: pip install 'souq-mcp[wallet]'"
            )

        rpc_url = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(self.private_key)

        # Base USDC ERC20 Contract
        usdc_address = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]

        usdc_contract = w3.eth.contract(address=usdc_address, abi=erc20_abi)
        amount_units = int(amount_usdc * 1_000_000)  # USDC has 6 decimals

        nonce = w3.eth.get_transaction_count(account.address)
        tx = usdc_contract.functions.transfer(
            Web3.to_checksum_address(recipient),
            amount_units
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 65000,
            "maxFeePerGas": w3.to_wei(0.1, "gwei"),
            "maxPriorityFeePerGas": w3.to_wei(0.01, "gwei"),
            "chainId": 8453  # Base mainnet
        })

        signed = account.sign_transaction(tx)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed.rawTransaction)
        return tx_hash_bytes.hex()

    # Convenience Tool Methods
    def compress(self, raw_content: str) -> Dict[str, Any]:
        """Slashes LLM context bloat by 80-95% to save prompt tokens."""
        return self.call_tool("token_context_compressor", raw_content=raw_content)

    def ast_slice(self, source_code: str, target_symbol: str) -> Dict[str, Any]:
        """Surgically extracts an AST function or class without reading whole files."""
        return self.call_tool("ast_structural_slicer", source_code=source_code, target_symbol=target_symbol)

    def microstructure(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        """Fetches real-time Binance order book depth, Order Book Imbalance (OBI), and liquidation risk."""
        return self.call_tool("quant_microstructure_radar", symbol=symbol)

    def funding_arbitrage(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        """Calculates Spot vs Perp basis spreads and annualized delta-neutral funding APR."""
        return self.call_tool("cross_exchange_arbitrage_scanner", symbol=symbol)

    def simulate_slippage(self, symbol: str = "BTC/USDT", side: str = "BUY", trade_size_usd: float = 10000.0) -> Dict[str, Any]:
        """Simulates VWAP execution price, slippage bps, and price impact on top 100 levels."""
        return self.call_tool("orderbook_slippage_simulator", symbol=symbol, side=side, trade_size_usd=trade_size_usd)

    def whale_flow(self, symbol: str = "BTC/USDT", block_threshold_usd: float = 50000.0) -> Dict[str, Any]:
        """Detects institutional whale block flow (> $50k) and whale accumulation telemetry."""
        return self.call_tool("smart_money_whale_flow_radar", symbol=symbol, block_threshold_usd=block_threshold_usd)

    def dev_cheatsheet(self, ecosystem: str = "openai") -> Dict[str, Any]:
        """Zero-fluff API schemas and execution code snippets for major developer platforms."""
        return self.call_tool("dev_api_cheatsheet_vault", ecosystem=ecosystem)

    def tech_trends(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Daily synthesized intelligence snapshot of GitHub AI repos, HackerNews, and arXiv."""
        return self.call_tool("daily_tech_ai_trends_radar", force_refresh=force_refresh)

    def prediction_arbitrage(self, asset: str = "BTC") -> Dict[str, Any]:
        """Cross-market probability discrepancy engine between Polymarket consensus and Black-Scholes spot pricing."""
        return self.call_tool("prediction_market_arbitrage_radar", asset=asset)

    def security_scan(self, source_code: str) -> Dict[str, Any]:
        """Static AST code security linter for Python and Solidity."""
        return self.call_tool("ast_security_scanner", source_code=source_code)

    def verify_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validates JSON objects against standard schema constraints with zero hallucinations."""
        return self.call_tool("synthetic_schema_verifier", data=data, schema=schema)
