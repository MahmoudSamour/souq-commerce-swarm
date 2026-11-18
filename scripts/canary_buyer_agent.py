#!/usr/bin/env python3
"""
SOUQ // Canary Buyer Agent
Autonomous buyer agent executing an end-to-end canary verification cycle:
1. Inspects remote discovery manifest (/.well-known/mcp.json)
2. Supports prepaid --api-key mode OR x402 Base L2 USDC payment flow
3. Defaults to low-cost deterministic `token_context_compressor` ($0.01 USDC)
4. Compatible with both web3 v6 (`rawTransaction`) and web3 v7 (`raw_transaction`)
5. Strictly asserts HTTP 200 settlement and exits non-zero on error/non-200
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

DEFAULT_EDGE_URL = os.getenv(
    "SOUQ_EDGE_URL",
    "https://written-emera-arapython-bf7436a4.apps.mistral.run",
)
EXPECTED_RECIPIENT = "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF"
EXPECTED_NETWORK = "Base"
DEFAULT_CANARY_TOOL = "token_context_compressor"


def build_default_tool_payload(tool_name: str) -> Dict[str, Any]:
    """Returns a low-cost deterministic sample payload for the requested canary tool."""
    samples: Dict[str, Dict[str, Any]] = {
        "token_context_compressor": {
            "tool": "token_context_compressor",
            "raw_content": (
                "LOG 2026-11-15T10:00:01Z INFO worker-1 request started\n"
                "LOG 2026-11-15T10:00:02Z DEBUG worker-1 session verified\n"
                "LOG 2026-11-15T10:00:03Z INFO worker-1 settled 200 OK\n"
            ),
            "mode": "auto",
            "max_compression": True,
        },
        "prompt_injection_firewall": {
            "tool": "prompt_injection_firewall",
            "text": "Explain ERC-20 token transfers cleanly.",
            "strict_mode": False,
        },
        "prediction_market_arbitrage_radar": {
            "tool": "prediction_market_arbitrage_radar",
            "asset": "BTC",
            "limit": 3,
        },
    }
    return dict(samples.get(tool_name, {"tool": tool_name}))


class CanaryBuyerAgent:
    def __init__(
        self,
        base_url: str = DEFAULT_EDGE_URL,
        buyer_id: str = "canary_trading_bot_01",
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/tools/call"
        self.buyer_id = buyer_id
        self.api_key = api_key if api_key is not None else os.getenv("SOUQ_API_KEY")
        self.buyer_private_key = os.getenv("CANARY_BUYER_PRIVATE_KEY")

    def log(self, stage: str, msg: str) -> None:
        print(f"[{stage}] {msg}")

    def call_api(self, payload: Dict[str, Any], extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"SouqCanaryBuyer/1.0 ({self.buyer_id})",
            "X-Client-Agent-Id": self.buyer_id,
        }
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(self.api_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=25.0) as resp:
                body = resp.read().decode("utf-8")
                return {
                    "status_code": resp.status,
                    "headers": dict(resp.headers),
                    "data": json.loads(body) if body else {},
                }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                err_data = json.loads(body)
            except Exception:
                err_data = {"raw_error": body}
            return {
                "status_code": exc.code,
                "headers": dict(exc.headers),
                "data": err_data,
            }

    @staticmethod
    def _extract_raw_tx(signed_tx: Any) -> bytes:
        raw_tx = getattr(signed_tx, "raw_transaction", None)
        if raw_tx is None:
            raw_tx = getattr(signed_tx, "rawTransaction", None)
        if raw_tx is None:
            raise RuntimeError("Signed transaction object exposes neither raw_transaction nor rawTransaction.")
        return raw_tx

    def _send_live_base_usdc(self, recipient: str, price_usdc: str) -> str:
        from eth_account import Account
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(os.getenv("BASE_RPC_URL", "https://mainnet.base.org")))
        acct = Account.from_key(self.buyer_private_key)
        usdc = w3.eth.contract(
            address=Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
            abi=[
                {
                    "constant": False,
                    "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                    "name": "transfer",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function",
                }
            ],
        )
        amount_units = int(round(float(price_usdc) * 1_000_000))
        nonce = w3.eth.get_transaction_count(acct.address, "pending")
        base_gas_price = max(int(w3.eth.gas_price), w3.to_wei(0.01, "gwei"))
        max_priority = w3.to_wei(0.005, "gwei")
        max_fee = int(base_gas_price * 2 + max_priority)

        tx = usdc.functions.transfer(Web3.to_checksum_address(recipient), amount_units).build_transaction(
            {
                "from": acct.address,
                "nonce": nonce,
                "gas": 75000,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_priority,
                "chainId": 8453,
            }
        )
        signed = acct.sign_transaction(tx)
        raw_tx = self._extract_raw_tx(signed)
        tx_hash_hex = w3.eth.send_raw_transaction(raw_tx).hex()
        if not tx_hash_hex.startswith("0x"):
            tx_hash_hex = f"0x{tx_hash_hex}"

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_hex, timeout=45)
        if receipt.get("status") != 1:
            raise RuntimeError(f"Base USDC transfer reverted on-chain (tx={tx_hash_hex})")
        return tx_hash_hex

    def _verify_discovery(self) -> Dict[str, Any]:
        self.log("STAGE 1", "Inspecting remote discovery manifest (/.well-known/mcp.json)...")
        mcp_manifest_url = f"{self.base_url}/.well-known/mcp.json"
        with urllib.request.urlopen(mcp_manifest_url, timeout=15) as r:
            manifest = json.loads(r.read().decode("utf-8"))
        assert "tools" in manifest and len(manifest["tools"]) >= 16, "Manifest missing complete tool catalog"
        assert manifest["settlement"]["recipient"] == EXPECTED_RECIPIENT, "Manifest recipient mismatch"
        self.log(
            "STAGE 1",
            f"Discovered {len(manifest['tools'])} tools; recipient={manifest['settlement']['recipient']}",
        )
        return manifest

    def run_full_canary_test(self, tool_name: str = DEFAULT_CANARY_TOOL, simulate: bool = False) -> Dict[str, Any]:
        print("====================================================================")
        print("SOUQ CANARY BUYER AGENT // END-TO-END VERIFICATION")
        print(f"Target Edge Host: {self.base_url}")
        print(f"Agent Identity  : {self.buyer_id}")
        print(f"Target Tool     : {tool_name}")
        print("====================================================================\n")

        self._verify_discovery()
        tool_req = build_default_tool_payload(tool_name)

        # Prepaid X-API-Key fast-path canary verification
        if self.api_key:
            self.log("STAGE 2", f"Executing prepaid X-API-Key canary call for '{tool_name}'...")
            res = self.call_api(tool_req, extra_headers={"X-API-Key": self.api_key})
            status_code = res["status_code"]
            if status_code != 200:
                raise RuntimeError(
                    f"Prepaid API key canary call failed with HTTP {status_code}: {res['data']}"
                )
            billing = res["headers"].get("x-souq-billing", res["headers"].get("X-Souq-Billing", "PREPAID"))
            self.log("STAGE 2", f"HTTP 200 settled via prepaid X-API-Key (billing={billing})")
            return {
                "status": "CANARY_TEST_PASSED",
                "mode": "api_key",
                "tool": tool_name,
                "status_code": status_code,
                "billing": billing,
            }

        # Standard HTTP 402 discovery + Base USDC x402 settlement check
        self.log("STAGE 2", f"Invoking '{tool_name}' (freemium trial probe)...")
        res1 = self.call_api(tool_req)
        status1 = res1["status_code"]
        if status1 == 200:
            billing = res1["headers"].get("x-souq-billing", res1["headers"].get("X-Souq-Billing", "UNKNOWN"))
            self.log("STAGE 2", f"HTTP 200 Received on initial call (billing={billing})")
        elif status1 == 402:
            self.log("STAGE 2", "HTTP 402 Challenge received (daily free trial already used).")
        else:
            raise RuntimeError(f"Unexpected initial status: {status1} - {res1['data']}")

        self.log("STAGE 3", "Triggering follow-up call to verify HTTP 402 economic challenge headers...")
        res2 = self.call_api(tool_req)
        status2 = res2["status_code"]
        headers2 = res2["headers"]
        if status2 != 402:
            raise RuntimeError(f"Expected HTTP 402 challenge on second call, got {status2}: {res2['data']}")

        price = headers2.get("x-souq-price-usdc", headers2.get("X-Souq-Price-USDC"))
        recipient = headers2.get("x-souq-recipient", headers2.get("X-Souq-Recipient"))
        assert recipient == EXPECTED_RECIPIENT, f"Mismatch recipient: {recipient}"
        assert price is not None, "Missing X-Souq-Price-USDC header"
        self.log("STAGE 3", f"HTTP 402 Verified: price={price} USDC, recipient={recipient}")

        self.log("STAGE 4", "Executing paid settlement...")
        if self.buyer_private_key:
            tx_hash = self._send_live_base_usdc(recipient=recipient, price_usdc=price)
            self.log("STAGE 4", f"Live Base USDC tx confirmed: {tx_hash}")
        elif simulate:
            tx_hash = f"0x_simulated_canary_{int(time.time() * 1000)}"
            self.log("STAGE 4", f"Submitting simulated canary tx hash: {tx_hash}")
        else:
            raise RuntimeError(
                "No settlement credentials provided: pass --api-key, set CANARY_BUYER_PRIVATE_KEY, "
                "or pass --simulate against a non-production test server."
            )

        res3 = self.call_api(tool_req, extra_headers={"X-Payment-Tx": tx_hash})
        if res3["status_code"] != 200:
            raise RuntimeError(
                f"Expected HTTP 200 settlement response, got HTTP {res3['status_code']}: {res3['data']}"
            )
        self.log("STAGE 4", f"HTTP 200 settlement verified for tx={tx_hash}")

        self.log("STAGE 5", "Attempting replay attack with identical X-Payment-Tx...")
        res_replay = self.call_api(tool_req, extra_headers={"X-Payment-Tx": tx_hash})
        if res_replay["status_code"] not in (400, 402, 409):
            raise RuntimeError(
                f"Replay attack was not rejected cleanly! Got HTTP {res_replay['status_code']}: {res_replay['data']}"
            )
        self.log("STAGE 5", f"Replay attack blocked with HTTP {res_replay['status_code']}")

        return {
            "status": "CANARY_TEST_PASSED",
            "mode": "x402_simulated" if (simulate and not self.buyer_private_key) else "x402_base_usdc",
            "tool": tool_name,
            "free_trial_verified": status1 == 200 or status2 == 402,
            "402_challenge_verified": True,
            "economic_headers_verified": True,
            "recipient_verified": recipient == EXPECTED_RECIPIENT,
            "price_usdc": price,
            "tx_hash": tx_hash,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute SOUQ end-to-end canary buyer verification.")
    parser.add_argument("--endpoint", default=DEFAULT_EDGE_URL, help="Target SOUQ base URL")
    parser.add_argument("--buyer-id", default="canary_trading_bot_01", help="Canary client agent identifier")
    parser.add_argument("--tool", default=DEFAULT_CANARY_TOOL, help="Tool name to invoke (default: token_context_compressor)")
    parser.add_argument("--api-key", default=None, help="Optional prepaid souq_live_... X-API-Key to test fast-path settlement")
    parser.add_argument("--simulate", action="store_true", help="Use simulated 0x_simulated_... tx hash (non-production test servers only)")
    args = parser.parse_args()

    agent = CanaryBuyerAgent(base_url=args.endpoint, buyer_id=args.buyer_id, api_key=args.api_key)
    try:
        result = agent.run_full_canary_test(tool_name=args.tool, simulate=args.simulate)
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "CANARY_TEST_PASSED" else 1
    except Exception as exc:
        sys.stderr.write(f"[ERROR] Canary buyer verification failed: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
