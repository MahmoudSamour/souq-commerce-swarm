import pytest
from agents.treasury.x402_gateway import X402PaymentGateway
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.analytics.negotiation_tracker import NegotiationTracker


@pytest.fixture
def temp_gateway(tmp_path):
    db_file = str(tmp_path / "test_gw.duckdb")
    receipts_dir = str(tmp_path / "receipts")
    receipt_engine = CryptoReceiptEngine(db_path=db_file, receipts_dir=receipts_dir)
    tracker = NegotiationTracker(db_path=db_file)
    return X402PaymentGateway(receipt_engine=receipt_engine, negotiation_tracker=tracker)


def test_402_challenge_generation(temp_gateway):
    challenge = temp_gateway.generate_402_challenge(
        tool_name="quant_microstructure_radar",
        price_usdc=0.02,
        client_agent_id="test_agent"
    )

    assert challenge["status_code"] == 402
    assert challenge["payment_details"]["amount"] == "0.0200"
    assert challenge["payment_details"]["token"] == "USDC"
    assert challenge["payment_details"]["chain"] == "Base"


def test_payment_verification_and_replay_prevention(temp_gateway):
    tx_hash = "0x_simulated_valid_tx_123456"

    # First attempt: succeeds
    settled, info = temp_gateway.verify_payment_and_settle(
        tx_hash=tx_hash,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        simulate_test=True
    )
    assert settled is True
    assert info["status"] == "SETTLED"
    assert "receipt_id" in info

    # Second attempt with same tx_hash: rejected as replay attack
    replayed, err = temp_gateway.verify_payment_and_settle(
        tx_hash=tx_hash,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        simulate_test=True
    )
    assert replayed is False
    assert err["error"] == "Payment Nullified"

