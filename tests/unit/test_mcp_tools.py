import pytest
from agents.production.mcp_tool_builder import (
    MarketMicrostructureEngine,
    ASTSecurityScanner,
    SyntheticSchemaVerifier,
    CrossExchangeArbitrageScanner,
    OrderBookSlippageSimulator,
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


