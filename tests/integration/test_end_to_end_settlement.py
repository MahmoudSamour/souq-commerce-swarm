import json
import time
from unittest.mock import MagicMock

import pytest
from agents.core.conductor import RaisConductor
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.treasury.x402_gateway import ERC20_TRANSFER_TOPIC, X402PaymentGateway
from agents.analytics.negotiation_tracker import NegotiationTracker
from agents.production.mcp_tool_builder import MarketMicrostructureEngine


def test_full_agent_to_agent_purchase_and_tax_loop(tmp_path):
    """
    Simulates a complete real-world autonomous interaction:
    1. External Agent requests paid tool without payment -> receives 402 challenge
    2. External Agent sends on-chain Base USDC transaction -> payment verified
    3. Mathematical order book calculation executed and returned to agent
    4. Immutable cryptographic receipt generated and logged in Treasury Lake
    5. Replay attack blocked if agent re-submits same transaction hash
    6. Tax report export generated with Koinly-compliant CSV
    """
    db_file = str(tmp_path / "souq_lake.duckdb")
    receipts_dir = str(tmp_path / "receipts")
    exports_dir = str(tmp_path / "exports")

    receipt_engine = CryptoReceiptEngine(db_path=db_file, receipts_dir=receipts_dir)
    tracker = NegotiationTracker(db_path=db_file)
    gateway = X402PaymentGateway(receipt_engine=receipt_engine, negotiation_tracker=tracker)
    micro_engine = MarketMicrostructureEngine()

    # Step 1: Agent calls without payment
    challenge = gateway.generate_402_challenge(
        tool_name="quant_microstructure_radar",
        price_usdc=0.02,
        client_agent_id="external_trading_agent_01"
    )
    assert challenge["status_code"] == 402
    assert challenge["payment_details"]["amount"] == "0.0200"

    # Step 2: Agent signs simulated transaction and pays
    tx_hash = "0x_simulated_agent_payment_abc123"
    settled, settlement_info = gateway.verify_payment_and_settle(
        tx_hash=tx_hash,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        client_agent_id="external_trading_agent_01",
        simulate_test=True
    )
    assert settled is True
    assert settlement_info["status"] == "SETTLED"
    receipt_id = settlement_info["receipt_id"]

    # Step 3: Service executes
    calc_result = micro_engine.get_microstructure_metrics("BTC/USDT")
    assert "metrics" in calc_result

    # Step 4: Replay attack blocked
    replayed, replay_info = gateway.verify_payment_and_settle(
        tx_hash=tx_hash,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        client_agent_id="external_trading_agent_01",
        simulate_test=True
    )
    assert replayed is False
    assert replay_info["error"] == "Payment Nullified"

    # Verify simulated receipt was persisted with audit_verification.is_simulated=True
    with open(tmp_path / "receipts" / f"{receipt_id}.json", "r", encoding="utf-8") as rf:
        sim_receipt = json.load(rf)
    assert sim_receipt["audit_verification"]["is_simulated"] is True

    # Step 5: Export Tax Ledger - simulated receipts MUST be excluded from IRS tax export
    tax_exports_sim = receipt_engine.export_tax_ledger(output_dir=exports_dir)
    assert tax_exports_sim["total_records"] == 0

    # Step 5b: Non-simulated on-chain USDC settlement (mocked Base L2 Web3 RPC) IS exported
    real_tx_hash = "0x" + "ab" * 32
    payer_addr = "0x" + "11" * 20
    payer_topic = "0x" + payer_addr.replace("0x", "").rjust(64, "0")
    recipient_topic = "0x" + gateway.recipient_wallet.lower().replace("0x", "").rjust(64, "0")

    mock_w3 = MagicMock()
    mock_w3.eth.chain_id = 8453
    mock_w3.eth.block_number = 25_000_010
    mock_w3.eth.get_block.return_value = {"timestamp": int(time.time()) - 15}
    mock_w3.eth.get_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 25_000_005,
        "gasUsed": 50_000,
        "effectiveGasPrice": 1_000_000_000,
        "logs": [
            {
                "address": gateway.usdc_contract,
                "topics": [ERC20_TRANSFER_TOPIC, payer_topic, recipient_topic],
                "data": hex(20_000),  # 0.020000 USDC
            }
        ],
    }
    gateway.web3 = mock_w3

    settled_real, real_info = gateway.verify_payment_and_settle(
        tx_hash=real_tx_hash,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        client_agent_id="external_trading_agent_02",
        simulate_test=False,
    )
    assert settled_real is True
    assert real_info["status"] == "SETTLED"
    with open(tmp_path / "receipts" / f"{real_info['receipt_id']}.json", "r", encoding="utf-8") as rf:
        real_receipt = json.load(rf)
    assert real_receipt["audit_verification"]["is_simulated"] is False

    exports_dir_real = str(tmp_path / "exports_real")
    tax_exports_real = receipt_engine.export_tax_ledger(output_dir=exports_dir_real)
    assert tax_exports_real["total_records"] == 1
    with open(tax_exports_real["json_report"], "r", encoding="utf-8") as jf:
        exported_records = json.load(jf)
    assert len(exported_records) == 1
    assert exported_records[0]["tx_hash"] == real_tx_hash

    # Step 6: Verify Conductor Cycle Runs Cleanly
    conductor = RaisConductor(db_path=db_file)
    cycle_report = conductor.run_daily_cycle()
    assert cycle_report["status"] == "OPERATIONAL_AND_REVENUE_READY"
    assert len(cycle_report["active_catalog"]) >= 3

