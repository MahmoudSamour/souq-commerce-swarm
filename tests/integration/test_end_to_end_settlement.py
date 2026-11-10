import pytest
from agents.core.conductor import RaisConductor
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.treasury.x402_gateway import X402PaymentGateway
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

    # Step 5: Export Tax Ledger
    tax_exports = receipt_engine.export_tax_ledger(output_dir=exports_dir)
    assert tax_exports["total_records"] == 1

    # Step 6: Verify Conductor Cycle Runs Cleanly
    conductor = RaisConductor(db_path=db_file)
    cycle_report = conductor.run_daily_cycle()
    assert cycle_report["status"] == "OPERATIONAL_AND_REVENUE_READY"
    assert len(cycle_report["active_catalog"]) >= 3

