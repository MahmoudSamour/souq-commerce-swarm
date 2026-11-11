import pytest
from agents.production.mcp_tool_builder import (
    MarketMicrostructureEngine,
    ASTSecurityScanner,
    SyntheticSchemaVerifier,
    CrossExchangeArbitrageScanner,
    OrderBookSlippageSimulator,
    SmartMoneyWhaleRadar,
    PredictionMarketArbitrageRadar,
)
from agents.production.dev_intelligence_vault import (
    DevAPICheatSheetVault,
    DailyTechTrendsRadar,
)


def test_market_microstructure_calculation():
    engine = MarketMicrostructureEngine()
    res = engine.get_microstructure_metrics("BTC/USDT")
    assert res["status"] in ("success", "simulated_fallback")
    assert "metrics" in res
    assert "spread_bps" in res["metrics"]
    assert "order_book_imbalance_obi" in res["metrics"]
    assert "disclaimer" in res or "notice" in res


def test_ast_security_scanner():
    scanner = ASTSecurityScanner()
    
    # Safe code
    clean_res = scanner.scan_python_code("def add(a, b):\n    return a + b\n")
    assert clean_res["analysis_verdict"] == "CLEAN"
    assert clean_res["total_vulnerabilities"] == 0

    # Dangerous code
    dangerous_res = scanner.scan_python_code("import os\nos.system('rm -rf /')\neval('1+1')\n")
    assert dangerous_res["analysis_verdict"] == "VULNERABILITIES_DETECTED"
    assert dangerous_res["total_vulnerabilities"] == 2


def test_synthetic_schema_verifier():
    verifier = SyntheticSchemaVerifier()
    schema = {"name": "str", "age": "int", "active": "bool"}

    # Valid instance
    valid_res = verifier.verify_schema_conformity(
        {"name": "Dobby", "age": 3, "active": True},
        schema
    )
    assert valid_res["is_valid"] is True

    # Invalid instance
    invalid_res = verifier.verify_schema_conformity(
        {"name": "Dobby", "age": "three"},
        schema
    )
    assert invalid_res["is_valid"] is False
    assert len(invalid_res["missing_fields"]) == 1  # missing active
    assert len(invalid_res["type_errors"]) == 1      # age is str instead of int


def test_cross_exchange_arbitrage_scanner():
    scanner = CrossExchangeArbitrageScanner()
    res = scanner.scan_arbitrage_and_funding("BTC/USDT")
    assert res["status"] in ("success", "simulated_fallback")
    assert "arbitrage_metrics" in res
    assert "basis_spread_bps" in res["arbitrage_metrics"]
    assert "annualized_funding_apr_pct" in res["arbitrage_metrics"]


def test_orderbook_slippage_simulator():
    simulator = OrderBookSlippageSimulator()
    res = simulator.simulate_slippage("BTC/USDT", side="BUY", trade_size_usd=5000.0)
    assert res["status"] in ("success", "simulated_fallback")
    assert "simulation" in res
    assert "expected_vwap" in res["simulation"]
    assert "slippage_bps" in res["simulation"]
    assert "execution_safety_grade" in res["simulation"]


def test_smart_money_whale_radar():
    radar = SmartMoneyWhaleRadar()
    res = radar.get_whale_flow_telemetry("BTC/USDT", block_threshold_usd=50000.0)
    assert res["status"] in ("success", "simulated_fallback")
    assert "smart_money_signals" in res
    assert "whale_accumulation_index" in res["smart_money_signals"]
    assert "regime_verdict" in res["smart_money_signals"]
    assert "liquidation_hazard_clusters" in res["smart_money_signals"]


def test_dev_api_cheatsheet_vault():
    vault = DevAPICheatSheetVault()
    res = vault.get_api_cheatsheet("openai")
    assert res["status"] == "success"
    assert "cheatsheet" in res
    assert res["cheatsheet"]["title"] == "OpenAI Structured Outputs & Tools Spec"
    assert res["tokens_saved_estimate"] >= 35000

    # Test unknown ecosystem graceful handling
    err_res = vault.get_api_cheatsheet("unknown_framework")
    assert err_res["status"] == "error"
    assert "available_ecosystems" in err_res


def test_daily_tech_ai_trends_radar():
    radar = DailyTechTrendsRadar()
    res = radar.refresh_cache_and_get(force_refresh=True)
    assert res["status"] == "success"
    assert "trending_github_ai_repos" in res
    assert len(res["trending_github_ai_repos"]) >= 2
    assert "hackernews_breakouts" in res
    assert "arxiv_landmark_papers" in res
    assert res["tokens_saved_estimate"] >= 20000


def test_prediction_market_arbitrage_radar():
    radar = PredictionMarketArbitrageRadar()
    res = radar.scan_prediction_arbitrage("BTC")
    assert res["status"] == "success"
    assert res["asset"] == "BTC"
    assert "benchmark_spot_price" in res
    assert "market_discrepancies" in res
    assert len(res["market_discrepancies"]) == 3
    first = res["market_discrepancies"][0]
    assert "market_title" in first
    assert "target_strike_usd" in first
    assert "spot_implied_prob" in first
    assert "arbitrage_edge_bps" in first
    assert "signal" in first
    assert res["tokens_saved_estimate"] >= 30000




