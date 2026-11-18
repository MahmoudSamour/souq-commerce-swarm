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


def test_invalid_live_tx_hash_rejected(temp_gateway):
    ok, err = temp_gateway.verify_payment_and_settle(
        tx_hash="not_a_real_hash",
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={},
        simulate_test=False,
    )
    assert ok is False
    assert "Invalid" in err["error"]


def test_erc20_transfer_units_and_cross_rail_replay(temp_gateway):
    from agents.treasury.x402_gateway import ERC20_TRANSFER_TOPIC

    recipient = temp_gateway.recipient_wallet.lower().replace("0x", "").rjust(64, "0")
    payer = "0x" + "ab" * 20
    payer_topic = "0x" + payer.replace("0x", "").rjust(64, "0")
    receipt = {
        "status": 1,
        "logs": [
            {
                "address": temp_gateway.usdc_contract,
                "topics": [ERC20_TRANSFER_TOPIC, payer_topic, "0x" + recipient],
                "data": hex(5_000_000),  # 5.0 USDC
            }
        ],
    }
    valid, verified_payer, units, err = temp_gateway._verify_erc20_usdc_transfer_units(receipt, 20_000)
    assert valid is True
    assert verified_payer.lower() == payer.lower()
    assert units == 5_000_000

    # Redeem topup once, then verify replay across direct x402 is blocked
    tx = "0x" + "1" * 64
    ok_topup, credited_payer, amt, _ = temp_gateway.verify_usdc_topup(
        tx, min_usd=0.50, simulate_test=True, simulated_amount_usd=5.0
    )
    assert ok_topup is True
    assert amt == 5.0
    issued, _ = temp_gateway.api_key_ledger.issue_or_topup_key(
        reference_id=tx, amount_usd=amt, rail="base_usdc", owner_label=credited_payer
    )
    assert issued is True

    replayed_direct, err_replay = temp_gateway.verify_payment_and_settle(
        tx_hash=tx,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={},
        simulate_test=True,
    )
    assert replayed_direct is False
    assert err_replay["error"] == "Payment Nullified"


