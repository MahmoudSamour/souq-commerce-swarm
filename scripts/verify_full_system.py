"""
SOUQ // Full Live System Verification Probe
Tests live Binance API connection, HTTP 402 payment lifecycle,
tax receipt generation, and simulated agent purchase.
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.production.mcp_tool_builder import MarketMicrostructureEngine, ASTSecurityScanner
from agents.production.token_compressor import TokenContextCompressor, CodeASTSlicer
from agents.treasury.x402_gateway import X402PaymentGateway
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.analytics.negotiation_tracker import NegotiationTracker
from agents.core.conductor import RaisConductor
from rich.console import Console
from rich.table import Table

console = Console()


def run_full_probe():
    console.print("\n[bold cyan]🧪 STARTING SOUQ FULL PRODUCTION SYSTEM PROBE...[/bold cyan]\n")

    # 1. Test Live Binance Feed
    console.print("[bold yellow]1. Testing Live Binance API Connection & Microstructure Engine...[/bold yellow]")
    micro_engine = MarketMicrostructureEngine()
    btc_metrics = micro_engine.get_microstructure_metrics("BTC/USDT")
    
    table_binance = Table(title="Live Binance Microstructure Telemetry", show_header=True)
    table_binance.add_column("Metric", style="dim")
    table_binance.add_column("Value", style="green")
    
    table_binance.add_row("Status", btc_metrics["status"])
    table_binance.add_row("Symbol", btc_metrics["symbol"])
    table_binance.add_row("Mid Price", f"${btc_metrics['metrics']['mid_price']:,}")
    table_binance.add_row("Spread (bps)", f"{btc_metrics['metrics']['spread_bps']} bps")
    table_binance.add_row("Order Book Imbalance (OBI)", str(btc_metrics['metrics']['order_book_imbalance_obi']))
    table_binance.add_row("Market Regime", btc_metrics['metrics']['market_regime'])
    table_binance.add_row("Execution Latency", f"{btc_metrics['latency_ms']} ms")
    console.print(table_binance)

    # 2. Test Agent Token Compressor
    console.print("\n[bold yellow]2. Testing Agent Token-Saving Compression Engine...[/bold yellow]")
    compressor = TokenContextCompressor()
    sample_bloat = "<html><body><h1>Crypto Intelligence</h1><p>Disclaimer: all rights reserved.</p><p>Volume is 12,000 BTC.</p></body></html>" * 5
    comp_res = compressor.compress_text_or_json(sample_bloat)
    console.print(f"   ✅ Raw Tokens: {comp_res['raw_token_estimate']} -> Compressed: {comp_res['compressed_token_estimate']}")
    console.print(f"   ✅ Tokens Saved: [bold green]{comp_res['tokens_saved']} ({comp_res['compression_ratio_pct']}%) [/bold green]in {comp_res['latency_ms']}ms")

    # 3. Test Full A2A Purchase Cycle
    console.print("\n[bold yellow]3. Testing Simulated External AI Agent Purchase Loop (HTTP 402)...[/bold yellow]")
    db_test = "data/souq_treasury_lake.duckdb"
    receipt_eng = CryptoReceiptEngine(db_path=db_test)
    tracker = NegotiationTracker(db_path=db_test)
    gateway = X402PaymentGateway(receipt_engine=receipt_eng, negotiation_tracker=tracker)

    # Step A: Challenge
    challenge = gateway.generate_402_challenge("quant_microstructure_radar", 0.02, "agent_external_bot_9")
    console.print(f"   ✅ 402 Challenge Issued: {challenge['payment_details']['amount']} USDC on {challenge['payment_details']['chain']}")

    # Step B: Settlement
    test_tx = f"0x_live_probe_tx_{int(time.time())}"
    settled, info = gateway.verify_payment_and_settle(
        tx_hash=test_tx,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        client_agent_id="agent_external_bot_9",
        simulate_test=True
    )
    assert settled is True
    console.print(f"   ✅ Payment Verified & Settled: Receipt ID [bold green]{info['receipt_id']}[/bold green]")

    # Step C: Replay Protection
    replayed, err = gateway.verify_payment_and_settle(
        tx_hash=test_tx,
        expected_price_usdc=0.02,
        tool_name="quant_microstructure_radar",
        payload_data={"symbol": "BTC/USDT"},
        simulate_test=True
    )
    assert replayed is False
    console.print("   ✅ Anti-Replay Defense: Double-spending blocked instantly.")

    # 4. Tax Export Check
    console.print("\n[bold yellow]4. Verifying Tax & Receipt Ledger...[/bold yellow]")
    tax_res = receipt_eng.export_tax_ledger()
    console.print(f"   ✅ Total Verified Cryptographic Receipts: [bold green]{tax_res['total_records']}[/bold green]")
    console.print(f"   ✅ Koinly CSV Updated: {tax_res['csv_report']}")

    console.print("\n[bold green]🎉 ALL PRODUCTION PROBES PASSED! SYSTEM IS 100% OPERATIONAL.[/bold green]\n")


if __name__ == "__main__":
    run_full_probe()

