"""
Sprint 4 Verification Suite:
(a) SOUQ_FREE_TRIAL_DAILY_LIMIT == 1 default + /mcp metadata
(b) HMAC quote_hash / work_order_id binding & replay rejection
(c) Coinbase x402 v1 EIP-3009 X-PAYMENT / PAYMENT-SIGNATURE header parsing & verification
(d) WalletEnforcementGate blocking unwhitelisted recipient / >$0.10 / duplicate work_order_id / failed eth_call
(e) AminAuditor.audit_tool_source rejecting fapi.binance.com, unsafe eval/exec, and PII collection
(f) Catalog consolidation (5 High-Alpha Live Feeds, ast_security_scanner removed), real funnel telemetry, Polar assets & register_marketplaces
"""

import base64
import json
import os
import time
import zipfile
from unittest.mock import MagicMock

import pytest
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

from agents.compliance.amin_auditor import AminAuditor
from agents.discovery.market_researcher import MarketResearchAgent
from agents.analytics.negotiation_tracker import NegotiationTracker
from agents.analytics.traffic_telemetry import TrafficTelemetryEngine
from agents.treasury.api_key_ledger import APIKeyLedger
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.treasury.wallet_gate import WalletEnforcementGate, WalletGateError
from agents.treasury.x402_gateway import X402PaymentGateway


RECIPIENT = "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"


def _make_gateway(tmp_path) -> X402PaymentGateway:
    db_file = str(tmp_path / "sprint4_gw.duckdb")
    receipt_eng = CryptoReceiptEngine(db_path=db_file)
    neg_tracker = NegotiationTracker(db_path=db_file)
    ledger = APIKeyLedger(db_path=db_file)
    return X402PaymentGateway(
        receipt_engine=receipt_eng,
        negotiation_tracker=neg_tracker,
        recipient_wallet=RECIPIENT,
        api_key_ledger=ledger,
    )


def _sign_eip3009_header(
    acct,
    recipient: str,
    value_units: int,
    nonce_hex: str,
    valid_after: int,
    valid_before: int,
    extra: dict | None = None,
) -> str:
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
            "verifyingContract": Web3.to_checksum_address(USDC_BASE),
        },
        "message": {
            "from": Web3.to_checksum_address(acct.address),
            "to": Web3.to_checksum_address(recipient),
            "value": value_units,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": bytes.fromhex(nonce_hex[2:]),
        },
    }
    signable = encode_typed_data(full_message=typed_data)
    signed = acct.sign_message(signable)
    sig_hex = signed.signature.hex()
    if not sig_hex.startswith("0x"):
        sig_hex = "0x" + sig_hex

    payload = {
        "x402Version": 1,
        "scheme": "exact",
        "network": "base",
        "payload": {
            "signature": sig_hex,
            "authorization": {
                "from": acct.address,
                "to": recipient,
                "value": str(value_units),
                "validAfter": str(valid_after),
                "validBefore": str(valid_before),
                "nonce": nonce_hex,
            },
        },
    }
    if extra:
        payload["extra"] = extra
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


# (a) SOUQ_FREE_TRIAL_DAILY_LIMIT == 1 default + catalog consolidation
def test_free_trial_daily_limit_default_is_one(monkeypatch):
    monkeypatch.delenv("SOUQ_FREE_TRIAL_DAILY_LIMIT", raising=False)
    import scripts.koyeb_server as ks

    assert ks._get_free_trial_daily_limit() == 1
    assert "ast_security_scanner" not in ks.TOOL_ECONOMICS
    assert "deep_ast_vulnerability_auditor" in ks.TOOL_ECONOMICS
    assert len(ks.HIGH_ALPHA_LIVE_FEEDS) == 5
    for feed in ks.HIGH_ALPHA_LIVE_FEEDS:
        assert ks.TOOL_ECONOMICS[feed]["tier"] == "PAID_HIGH_ALPHA_LIVE_FEED"


# (b) HMAC quote_hash / work_order_id binding & replay rejection
def test_hmac_quote_hash_and_work_order_replay_rejection(tmp_path):
    gw = _make_gateway(tmp_path)
    challenge = gw.generate_402_challenge(
        tool_name="quant_microstructure_radar",
        price_usdc=0.02,
    )
    wo_id = challenge["work_order_id"]
    q_hash = challenge["quote_hash"]
    assert wo_id.startswith("wo_")
    assert len(q_hash) == 64
    assert challenge["x402Version"] == 1
    assert challenge["accepts"][0]["scheme"] == "exact"
    assert challenge["accepts"][0]["network"] == "base"

    # Cross-tool replay must be rejected
    ok_cross, err_cross = gw.verify_quote_binding(
        work_order_id=wo_id,
        quote_hash=q_hash,
        tool_name="prediction_market_arbitrage_radar",
        expected_price_usdc=0.02,
    )
    assert ok_cross is False
    assert "Cross-tool" in err_cross

    # Tampered quote_hash must be rejected
    ok_tamper, err_tamper = gw.verify_quote_binding(
        work_order_id=wo_id,
        quote_hash="0" * 64,
        tool_name="quant_microstructure_radar",
        expected_price_usdc=0.02,
    )
    assert ok_tamper is False
    assert "tampered" in err_tamper.lower() or "invalid" in err_tamper.lower()

    # Valid settlement consumes work_order_id
    settled_ok, settle_info = gw.verify_payment_and_settle(
        tx_hash="0x_simulated_quote_test_1",
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        simulate_test=True,
        work_order_id=wo_id,
        quote_hash=q_hash,
    )
    assert settled_ok is True
    assert settle_info["work_order_id"] == wo_id

    # Replaying same work_order_id with a different tx_hash must be rejected
    replay_ok, replay_info = gw.verify_payment_and_settle(
        tx_hash="0x_simulated_quote_test_2",
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        simulate_test=True,
        work_order_id=wo_id,
        quote_hash=q_hash,
    )
    assert replay_ok is False
    assert replay_info["error"] == "Quote Binding Rejected"


# (c) Coinbase x402 v1 EIP-3009 X-PAYMENT header parsing & verification
def test_x402_v1_eip3009_header_parsing_and_verification(tmp_path):
    gw = _make_gateway(tmp_path)
    buyer = Account.create()
    now_ts = int(time.time())
    nonce_hex = "0x" + "ab" * 32

    challenge = gw.generate_402_challenge(
        tool_name="prediction_market_arbitrage_radar",
        price_usdc=0.03,
        payer_address=buyer.address,
    )
    header_b64 = _sign_eip3009_header(
        acct=buyer,
        recipient=RECIPIENT,
        value_units=30000,  # $0.03 USDC
        nonce_hex=nonce_hex,
        valid_after=now_ts - 10,
        valid_before=now_ts + 300,
        extra={
            "work_order_id": challenge["work_order_id"],
            "quote_hash": challenge["quote_hash"],
        },
    )

    parsed = gw.parse_x402_payment_header(header_b64)
    assert parsed is not None
    assert parsed["scheme"] == "exact"
    assert parsed["network"] == "base"

    # Mocked facilitator response for gasless 1-RTT verification
    def fake_facilitator_post(url, json=None, timeout=8):
        resp = MagicMock()
        resp.status_code = 200
        if url.endswith("/verify"):
            resp.json.return_value = {"isValid": True}
        else:
            resp.json.return_value = {"success": True, "txHash": "0x" + "ef" * 32}
        return resp

    ok, info = gw.verify_x402_eip3009_payment(
        payment_header=header_b64,
        expected_price_usdc=0.03,
        tool_name="prediction_market_arbitrage_radar",
        verify_with_facilitator=True,
        facilitator_post=fake_facilitator_post,
    )
    assert ok is True
    assert info["payer_address"] == buyer.address.lower()
    assert info["payment_protocol"] == "x402_eip3009"
    assert info["tx_hash"] == "0x" + "ef" * 32

    # Tampered amount below required price must fail
    low_header = _sign_eip3009_header(
        acct=buyer,
        recipient=RECIPIENT,
        value_units=1000,  # $0.001 < $0.03
        nonce_hex="0x" + "cd" * 32,
        valid_after=now_ts - 10,
        valid_before=now_ts + 300,
    )
    ok_low, err_low = gw.verify_x402_eip3009_payment(
        payment_header=low_header,
        expected_price_usdc=0.03,
        tool_name="prediction_market_arbitrage_radar",
        verify_with_facilitator=False,
    )
    assert ok_low is False
    assert "Insufficient" in err_low["error"]


# (d) Wallet Enforcement Gate blocking unwhitelisted recipient / >$0.10 / duplicate work_order_id / failed eth_call
def test_wallet_enforcement_gate_hard_blocks(tmp_path):
    gate = WalletEnforcementGate(
        allowed_recipients=[RECIPIENT],
        max_per_call_usd=0.10,
        max_daily_spend_usd=2.00,
        ledger_path=str(tmp_path / "wallet_ledger.json"),
    )

    # 1. Unwhitelisted recipient blocked
    with pytest.raises(WalletGateError, match="whitelist"):
        gate.check_policy(
            recipient="0x000000000000000000000000000000000000dEaD",
            amount_usdc=0.03,
            work_order_id="wo_unwhitelisted",
        )

    # 2. Per-call cap > $0.10 blocked
    with pytest.raises(WalletGateError, match="per-call cap"):
        gate.check_policy(
            recipient=RECIPIENT,
            amount_usdc=0.15,
            work_order_id="wo_overcap",
        )

    # 3. Failed eth_call simulation aborts before send_raw_transaction
    mock_w3_fail = MagicMock()
    mock_w3_fail.eth.call.side_effect = RuntimeError("execution reverted: ERC20: transfer amount exceeds balance")
    with pytest.raises(WalletGateError, match="eth_call pre-simulation"):
        gate.authorize_and_broadcast(
            w3=mock_w3_fail,
            tx={"from": "0x" + "1" * 40, "to": USDC_BASE, "data": b"\x01", "value": 0},
            sign_fn=lambda tx: b"raw_signed",
            recipient=RECIPIENT,
            amount_usdc=0.03,
            work_order_id="wo_sim_fail",
        )
    mock_w3_fail.eth.send_raw_transaction.assert_not_called()

    # 4. Successful eth_call allows broadcast & records work_order_id
    mock_w3_ok = MagicMock()
    mock_w3_ok.eth.call.return_value = (1).to_bytes(32, "big")
    mock_w3_ok.eth.send_raw_transaction.return_value = bytes.fromhex("aa" * 32)
    tx_hex = gate.authorize_and_broadcast(
        w3=mock_w3_ok,
        tx={"from": "0x" + "1" * 40, "to": USDC_BASE, "data": b"\x01", "value": 0},
        sign_fn=lambda tx: b"raw_signed",
        recipient=RECIPIENT,
        amount_usdc=0.03,
        work_order_id="wo_unique_1",
    )
    assert tx_hex == "0x" + "aa" * 32
    mock_w3_ok.eth.send_raw_transaction.assert_called_once()

    # 5. Duplicate work_order_id blocked by idempotency ledger
    with pytest.raises(WalletGateError, match="Duplicate work_order_id"):
        gate.authorize_and_broadcast(
            w3=mock_w3_ok,
            tx={"from": "0x" + "1" * 40, "to": USDC_BASE, "data": b"\x01", "value": 0},
            sign_fn=lambda tx: b"raw_signed",
            recipient=RECIPIENT,
            amount_usdc=0.03,
            work_order_id="wo_unique_1",
        )


# (e) AminAuditor.audit_tool_source rejecting fapi.binance.com, eval/exec, PII
def test_amin_auditor_static_ast_rejects_binance_and_unsafe_code(tmp_path):
    auditor = AminAuditor()

    bad_binance = tmp_path / "bad_binance_tool.py"
    bad_binance.write_text('URL = "https://fapi.binance.com/fapi/v1/premiumIndex"\n', encoding="utf-8")
    ok_bin, rep_bin = auditor.audit_tool_source(str(bad_binance))
    assert ok_bin is False
    assert rep_bin["checks"]["no_forbidden_endpoints"] is False
    assert rep_bin["clearance_token"] is None

    bad_eval = tmp_path / "bad_eval_tool.py"
    bad_eval.write_text('def run(x):\n    return eval(x)\n', encoding="utf-8")
    ok_eval, rep_eval = auditor.audit_tool_source(str(bad_eval))
    assert ok_eval is False
    assert rep_eval["checks"]["no_unsafe_exec"] is False

    clean_tool = tmp_path / "clean_tool.py"
    clean_tool.write_text('URL = "https://api.coinbase.com/v2/prices/BTC-USD/spot"\ndef fetch(): return URL\n', encoding="utf-8")
    ok_clean, rep_clean = auditor.audit_tool_source(str(clean_tool))
    assert ok_clean is True
    assert rep_clean["clearance_token"] is not None


# (f) Real DB funnel telemetry + packaged Polar assets + marketplace verifier
def test_real_funnel_telemetry_and_polar_assets(tmp_path):
    db_file = str(tmp_path / "funnel.duckdb")
    neg = NegotiationTracker(db_path=db_file)
    tel = TrafficTelemetryEngine(db_path=db_file)

    neg.log_negotiation("a1", "UA", "quant_microstructure_radar", 0.02, None, "x402_http", "CHALLENGED_402", 5)
    neg.log_negotiation("a2", "UA", "quant_microstructure_radar", 0.02, None, "x402_http", "CHALLENGED_402", 5)
    neg.log_negotiation("a2", "UA", "quant_microstructure_radar", 0.02, 0.02, "x402_http", "SETTLED", 12)
    tel.record_request("POST", "/api/tools/call", 404, "1.2.3.4", "Bot", tool_name="missing_alpha_tool", billing_status="UNKNOWN_TOOL")

    researcher = MarketResearchAgent()
    funnel = researcher.query_funnel_telemetry(db_file)
    assert funnel["funnel_dropoffs_402_to_settled"]["quant_microstructure_radar"]["challenged_402_count"] == 2
    assert funnel["funnel_dropoffs_402_to_settled"]["quant_microstructure_radar"]["settled_count"] == 1
    assert funnel["unknown_tool_demand"][0]["requested_tool"] == "missing_alpha_tool"

    # Verify packaged Polar ZIP assets exist and contain clean files
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    eval_zip = os.path.join(repo_root, "dist", "polar_assets", "agent_guardrail_eval_suite_v1.zip")
    micro_zip = os.path.join(repo_root, "dist", "polar_assets", "crypto_microstructure_sample_v1.zip")
    assert os.path.isfile(eval_zip)
    assert os.path.isfile(micro_zip)
    with zipfile.ZipFile(eval_zip) as zf:
        assert {"README.md", "eval_cases.jsonl", "run_eval.py", "manifest.json"}.issubset(set(zf.namelist()))
    with zipfile.ZipFile(micro_zip) as zf:
        assert {"README.md", "schema.json", "sample_microstructure.jsonl", "sample_microstructure.parquet", "analyze_microstructure.py", "manifest.json"}.issubset(set(zf.namelist()))
        raw_jsonl = zf.read("sample_microstructure.jsonl").decode("utf-8").lower()
        assert "binance" not in raw_jsonl

    # Verify register_marketplaces offline mode
    from scripts.register_marketplaces import verify_marketplaces

    report = verify_marketplaces(offline=True)
    assert report["total_directories"] == 6
    assert report["offline_mode"] is True


# ---------------------------------------------------------------------------
# Pro Critic Surgical Regression Tests (Defects 1–5)
# ---------------------------------------------------------------------------

def test_souq_client_pins_recipient_whitelist_and_persists_ledger(tmp_path):
    """Defect 1 & 2: SouqClient must NEVER whitelist untrusted 402 recipients and must persist ledger."""
    import sys
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    py_client_dir = os.path.join(repo_root, "clients", "python")
    if py_client_dir not in sys.path:
        sys.path.insert(0, py_client_dir)
    from souq_mcp.client import SouqClient

    ledger_file = str(tmp_path / "client_wallet_ledger.json")
    client = SouqClient(
        endpoint="https://test.souq.run",
        private_key="0x" + "1" * 64,
        wallet_ledger_path=ledger_file,
    )
    assert client.wallet_ledger_path == ledger_file
    assert RECIPIENT in client.allowed_recipients

    # Rogue 402 pointing to attacker wallet must be hard-rejected before any RPC call
    with pytest.raises(WalletGateError, match="whitelist"):
        client._settle_usdc_payment(
            recipient="0x000000000000000000000000000000000000dEaD",
            amount_usdc=0.02,
            work_order_id="wo_rogue_402",
        )


def test_marketplace_payout_gate_rejection_does_not_corrupt_balance(tmp_path, monkeypatch):
    """Defect 2 & 3: WalletEnforcementGate rejection must NOT deduct seller earned_balance_usd."""
    from agents.treasury.marketplace_registry import MarketplaceRegistry

    db_file = str(tmp_path / "mkt_gate.duckdb")
    ledger_file = str(tmp_path / "mkt_payout_ledger.json")
    reg = MarketplaceRegistry(
        db_path=db_file,
        resolve_dns=False,
        payout_ledger_path=ledger_file,
    )
    ok, reg_info = reg.register_seller_and_listing(
        tool_slug="alpha_signal_v1",
        title="Alpha Signal Feed",
        description="Deterministic live alpha signal feed for testing payout gate safety.",
        endpoint_url="https://api.coinbase.com/v2/time",
        price_usdc=2.0,
        payout_wallet_base=RECIPIENT,
    )
    assert ok is True
    seller_key = reg_info["seller_api_key"]
    tool_id = reg_info["tool_id"]

    # Accumulate $16.00 seller earnings (10 calls * $2.00 * 80% = $16.00)
    for _ in range(10):
        reg.record_split_settlement(tool_id, 2.0, "prepaid_api_key")

    before = reg.get_seller_dashboard(seller_key)
    assert before["earned_balance_usd"] == pytest.approx(16.0, rel=1e-4)

    # Cap per-call payout to $12.00 -> requesting $15.00 must be rejected WITHOUT corrupting balance!
    monkeypatch.setenv("SOUQ_PAYOUT_MAX_PER_CALL_USD", "12.0")
    ok_pay, pay_err = reg.request_seller_payout(seller_key, amount_usd=15.0)
    assert ok_pay is False
    assert "WalletEnforcementGate" in pay_err["error"]

    after = reg.get_seller_dashboard(seller_key)
    assert after["earned_balance_usd"] == pytest.approx(16.0, rel=1e-4)
    assert after["total_paid_out_usd"] == pytest.approx(0.0, rel=1e-4)

    # Valid $11.00 payout succeeds and persists to ledger_file
    ok_pay2, pay_ok = reg.request_seller_payout(seller_key, amount_usd=11.0)
    assert ok_pay2 is True
    assert pay_ok["status"] == "PAYOUT_QUEUED"
    assert os.path.isfile(ledger_file)
    after2 = reg.get_seller_dashboard(seller_key)
    assert after2["earned_balance_usd"] == pytest.approx(5.0, rel=1e-4)


def test_eip3009_replay_blocked_when_facilitator_returns_tx_hash(tmp_path):
    """Defect 4: Recording BOTH eip3009:{payer}:{nonce} AND txHash blocks replaying signed EIP-3009 auth."""
    gw = _make_gateway(tmp_path)
    buyer = Account.create()
    now_ts = int(time.time())
    nonce_hex = "0x" + "55" * 32

    header_b64 = _sign_eip3009_header(
        acct=buyer,
        recipient=RECIPIENT,
        value_units=20000,
        nonce_hex=nonce_hex,
        valid_after=now_ts - 10,
        valid_before=now_ts + 300,
    )

    def fake_facilitator_post(url, json=None, timeout=8):
        resp = MagicMock()
        resp.status_code = 200
        if url.endswith("/verify"):
            resp.json.return_value = {"isValid": True}
        else:
            resp.json.return_value = {"success": True, "txHash": "0x" + "99" * 32}
        return resp

    ok1, pre1 = gw.verify_x402_eip3009_payment(
        payment_header=header_b64,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        verify_with_facilitator=True,
        facilitator_post=fake_facilitator_post,
    )
    assert ok1 is True
    assert pre1["tx_hash"] == "0x" + "99" * 32
    assert pre1["eip3009_nullifier"].startswith("eip3009:")

    settled_ok, _ = gw.commit_payment_settlement(
        tx_hash=pre1["tx_hash"],
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        payer_address=pre1["payer_address"],
        payment_protocol="x402_eip3009",
        eip3009_nullifier=pre1["eip3009_nullifier"],
    )
    assert settled_ok is True

    # Replaying the exact same EIP-3009 header MUST be blocked by _is_tx_already_used(nullifier_key)
    ok_replay, err_replay = gw.verify_x402_eip3009_payment(
        payment_header=header_b64,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        verify_with_facilitator=True,
        facilitator_post=fake_facilitator_post,
    )
    assert ok_replay is False
    assert err_replay["error"] == "Payment Nullified"


def test_ast_security_scanner_removed_from_all_surfaces():
    """Defect 5: Ensure ast_security_scanner is purged from server, npm, web, and pricing config."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    targets = [
        "scripts/run_mcp_server.py",
        "clients/npm/bin/souq-mcp.js",
        "web/index.html",
        "web/llms.txt",
        "web/llms-full.txt",
        "config/pricing_models.yaml",
    ]
    for rel in targets:
        text = open(os.path.join(repo_root, rel), "r", encoding="utf-8").read()
        assert "ast_security_scanner" not in text, f"Stale ast_security_scanner found in {rel}"
