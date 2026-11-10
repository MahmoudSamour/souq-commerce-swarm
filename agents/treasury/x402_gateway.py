"""
SOUQ // HTTP 402 ("x402") Base USDC Payment Gateway Middleware
Handles cryptographic 402 payment challenges, strict ERC-20 Transfer log verification,
and anti-replay nullification for autonomous agent clients.
"""

import os
import time
from typing import Dict, Any, Tuple, Optional
from web3 import Web3
from dotenv import load_dotenv

from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.analytics.negotiation_tracker import NegotiationTracker

load_dotenv("config/.env")

# Keccak-256 topic for ERC-20 Transfer(address indexed from, address indexed to, uint256 value)
ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


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
        rpc_url: Optional[str] = None
    ):
        self.receipt_engine = receipt_engine or CryptoReceiptEngine()
        self.negotiation_tracker = negotiation_tracker or NegotiationTracker()
        
        self.recipient_wallet = (
            recipient_wallet or
            os.getenv("BASE_RECIPIENT_WALLET_ADDRESS", "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF")
        )
        self.rpc_url = rpc_url or os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
        self.usdc_contract = os.getenv("BASE_USDC_CONTRACT", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

    def generate_402_challenge(
        self,
        tool_name: str,
        price_usdc: float,
        client_agent_id: str = "anonymous_agent",
        client_user_agent: str = "AI-Agent-Client/1.0"
    ) -> Dict[str, Any]:
        """
        Creates the standardized x402 payment challenge JSON payload.
        """
        challenge = {
            "status_code": 402,
            "error": "Payment Required",
            "protocol": "x402-v1.0",
            "payment_details": {
                "chain": "Base",
                "chain_id": 8453,
                "token": "USDC",
                "token_contract": self.usdc_contract,
                "amount": f"{price_usdc:.4f}",
                "amount_units": int(round(price_usdc * 1e6)),  # USDC has 6 decimals
                "recipient_address": self.recipient_wallet,
                "valid_for_seconds": 180,
                "created_at_epoch": int(time.time())
            },
            "instructions": "Transfer exact USDC amount on Base to recipient_address and retry with header [X-Payment-Tx: <tx_hash>]"
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

    def _verify_erc20_usdc_transfer(self, tx_receipt: Any, expected_units: int) -> Tuple[bool, str, str]:
        """
        Forensically inspects transaction logs to confirm:
        1. Emitted by official Base USDC contract
        2. ERC-20 Transfer event to our exact recipient wallet
        3. Amount transferred >= expected_units
        Returns: (is_valid, payer_address, error_message)
        """
        target_contract = self.usdc_contract.lower()
        target_recipient_clean = self.recipient_wallet.lower().replace("0x", "").rjust(64, "0")

        logs = tx_receipt.get("logs", [])
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

            if transferred_units >= expected_units:
                from_topic = topics[1].replace("0x", "")
                payer = "0x" + from_topic[-40:]
                return True, payer, ""

        return False, "", "No matching Base USDC transfer to recipient wallet found in transaction logs."

    def verify_payment_and_settle(
        self,
        tx_hash: str,
        expected_price_usdc: float,
        tool_name: str,
        payload_data: Any,
        client_agent_id: str = "anonymous_agent",
        client_user_agent: str = "AI-Agent-Client/1.0",
        simulate_test: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies on-chain Base USDC payment or explicit local test simulation,
        executes anti-replay check, and generates an immutable tax receipt.
        """
        start_t = time.time()

        # 1. Anti-Replay Nullifier Check
        if self.receipt_engine.is_tx_already_redeemed(tx_hash):
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
                rejection_reason=f"Transaction {tx_hash} already redeemed."
            )
            return False, {
                "error": "Payment Nullified",
                "message": "This transaction hash has already been redeemed.",
                "tx_hash": tx_hash
            }

        payer_address = "0xMockClientPayerAddress123456789012345678"
        expected_units = int(round(expected_price_usdc * 1e6))

        # 2. On-Chain Verification on Base Mainnet
        if not simulate_test:
            try:
                tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                if not tx_receipt or tx_receipt.get("status") != 1:
                    return False, {"error": "Invalid or unconfirmed transaction on Base."}
                
                valid_transfer, verified_payer, err_msg = self._verify_erc20_usdc_transfer(tx_receipt, expected_units)
                if not valid_transfer:
                    return False, {"error": err_msg}
                payer_address = verified_payer
            except Exception as e:
                return False, {"error": f"On-chain Base verification failed: {str(e)}"}
        else:
            payer_address = "0xSimulatedClientAgentWallet999"

        # 3. Generate Cryptographic Receipt & Log in Treasury Lake
        receipt = self.receipt_engine.generate_receipt(
            tx_hash=tx_hash,
            payer_address=payer_address,
            recipient_address=self.recipient_wallet,
            amount_usdc=expected_price_usdc,
            product_id=tool_name,
            service_rendered=f"FastMCP Tool Invocation: {tool_name}",
            payload_data=payload_data,
            chain="Base",
            token_contract=self.usdc_contract
        )

        latency = int((time.time() - start_t) * 1000)

        # 4. Log Successful Settlement into Negotiation Tracker
        self.negotiation_tracker.log_negotiation(
            client_agent_id=client_agent_id,
            client_user_agent=client_user_agent,
            tool_requested=tool_name,
            initial_quote_usd=expected_price_usdc,
            settled_price_usd=expected_price_usdc,
            payment_protocol="x402_http",
            outcome="SETTLED",
            latency_ms=latency,
            metadata={"receipt_id": receipt["receipt_id"]}
        )

        return True, {
            "status": "SETTLED",
            "receipt_id": receipt["receipt_id"],
            "amount_paid_usdc": expected_price_usdc,
            "tx_hash": tx_hash
        }
