import os
import pytest
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine


@pytest.fixture
def temp_receipt_engine(tmp_path):
    db_file = str(tmp_path / "test_treasury.duckdb")
    receipts_dir = str(tmp_path / "receipts")
    return CryptoReceiptEngine(db_path=db_file, receipts_dir=receipts_dir)


def test_receipt_generation_and_verification(temp_receipt_engine):
    tx_hash = "0x9876543210abcdef9876543210abcdef9876543210abcdef9876543210abcdef"
    receipt = temp_receipt_engine.generate_receipt(
        tx_hash=tx_hash,
        payer_address="0xPayer1234567890",
        recipient_address="0xRecipient987654321",
        amount_usdc=0.02,
        product_id="quant_microstructure_radar",
        service_rendered="Live Order Book Microstructure Depth",
        payload_data={"symbol": "BTC/USDT"}
    )

    assert receipt["receipt_id"].startswith("REC-")
    assert receipt["transaction_details"]["amount_token"] == 0.02
    assert receipt["transaction_details"]["token_symbol"] == "USDC"
    assert "receipt_signature" in receipt["audit_verification"]

    # Verify anti-replay check
    assert temp_receipt_engine.is_tx_already_redeemed(tx_hash) is True
    assert temp_receipt_engine.is_tx_already_redeemed("0xUnseenTxHash") is False


def test_tax_export_functionality(temp_receipt_engine, tmp_path):
    temp_receipt_engine.generate_receipt(
        tx_hash="0xTx1",
        payer_address="0xPayer1",
        recipient_address="0xRecipient1",
        amount_usdc=0.05,
        product_id="test_tool",
        service_rendered="Test Service",
        payload_data={}
    )

    export_res = temp_receipt_engine.export_tax_ledger(output_dir=str(tmp_path / "exports"))
    assert export_res["total_records"] == 1
    assert os.path.exists(export_res["csv_report"])
    assert os.path.exists(export_res["json_report"])
