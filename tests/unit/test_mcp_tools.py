from unittest.mock import MagicMock
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
    assert res["status"] in ("success", "upstream_unavailable")
    if res["status"] == "success":
        assert "metrics" in res
        assert "spread_bps" in res["metrics"]
        assert "order_book_imbalance_obi" in res["metrics"]
        assert "disclaimer" in res or "notice" in res
    else:
        assert "metrics" not in res
        assert "providers_tried" in res


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
    assert res["status"] in ("success", "upstream_unavailable")
    if res["status"] == "success":
        assert "arbitrage_metrics" in res
        assert "basis_spread_bps" in res["arbitrage_metrics"]
        assert "annualized_funding_apr_pct" in res["arbitrage_metrics"]
    else:
        assert "arbitrage_metrics" not in res
        assert "providers_tried" in res


def test_orderbook_slippage_simulator():
    simulator = OrderBookSlippageSimulator()
    res = simulator.simulate_slippage("BTC/USDT", side="BUY", trade_size_usd=5000.0)
    assert res["status"] in ("success", "upstream_unavailable")
    if res["status"] == "success":
        assert "simulation" in res
        assert "expected_vwap" in res["simulation"]
        assert "slippage_bps" in res["simulation"]
        assert "execution_safety_grade" in res["simulation"]
    else:
        assert "simulation" not in res
        assert "providers_tried" in res


def test_smart_money_whale_radar():
    radar = SmartMoneyWhaleRadar()
    res = radar.get_whale_flow_telemetry("BTC/USDT", block_threshold_usd=50000.0)
    assert res["status"] in ("success", "upstream_unavailable")
    if res["status"] == "success":
        assert "smart_money_signals" in res
        assert "whale_accumulation_index" in res["smart_money_signals"]
        assert "regime_verdict" in res["smart_money_signals"]
        assert "liquidation_hazard_clusters" in res["smart_money_signals"]
    else:
        assert "smart_money_signals" not in res
        assert "providers_tried" in res


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


def test_daily_tech_ai_trends_radar(tmp_path, monkeypatch):
    monkeypatch.setattr(DailyTechTrendsRadar, "CACHE_PATH", str(tmp_path / "daily_tech_radar_latest.json"))
    radar = DailyTechTrendsRadar()
    res = radar.refresh_cache_and_get(force_refresh=True)
    assert res["status"] in ("success", "upstream_unavailable")
    if res["status"] == "success":
        assert "trending_github_ai_repos" in res
        assert len(res["trending_github_ai_repos"]) >= 1
        assert "hackernews_breakouts" in res
        assert "arxiv_landmark_papers" in res
        assert res["tokens_saved_estimate"] >= 20000
    else:
        assert res["trending_github_ai_repos"] == []


def test_prediction_market_arbitrage_radar():
    radar = PredictionMarketArbitrageRadar()
    res = radar.scan_prediction_arbitrage("BTC")
    assert res["status"] in ("success", "upstream_unavailable")
    if res["status"] == "success":
        assert res["asset"] == "BTC"
        assert "benchmark_spot_price" in res
        assert "market_discrepancies" in res
        assert len(res["market_discrepancies"]) <= 5
        if res["market_discrepancies"]:
            first = res["market_discrepancies"][0]
            assert "market_title" in first
            assert "target_strike_usd" in first
            assert "spot_implied_prob" in first
            assert "arbitrage_edge_bps" in first
            assert "signal" in first
        assert res["tokens_saved_estimate"] >= 30000
    else:
        assert "market_discrepancies" not in res
        assert "providers_tried" in res


def test_prediction_market_polymarket_gamma_parser():
    from unittest.mock import MagicMock
    from datetime import datetime, timedelta, timezone

    future_end = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    fake_feed = MagicMock()
    fake_feed.fetch_spot_price.return_value = (90000.0, "mock_binance")
    fake_feed.fetch_realized_volatility.return_value = 0.55
    fake_feed.fetch_polymarket_events.return_value = [
        {
            "title": "Bitcoin price targets",
            "slug": "bitcoin-price-targets",
            "volume24hr": 150000.0,
            "markets": [
                {
                    "question": "Will Bitcoin reach $100,000 before month end?",
                    "slug": "btc-100k",
                    "outcomes": '["Yes", "No"]',
                    "outcomePrices": '["0.20", "0.80"]',
                    "endDate": future_end,
                    "volume24hr": 90000.0,
                },
                {
                    "question": "Will Bitcoin dip to $60,000?",
                    "slug": "btc-dip-60k",
                    "outcomes": '["Yes", "No"]',
                    "outcomePrices": '["0.15", "0.85"]',
                    "endDate": future_end,
                    "volume24hr": 60000.0,
                },
            ],
        }
    ]

    radar = PredictionMarketArbitrageRadar(feed=fake_feed)
    res = radar.scan_prediction_arbitrage("BTC", limit=5)
    assert res["data_source"] == "live_polymarket_gamma"
    assert res["opportunities_analyzed"] == 2
    by_slug = {item["market_slug"]: item for item in res["market_discrepancies"]}
    assert by_slug["btc-100k"]["direction"] == "ABOVE_STRIKE"
    assert by_slug["btc-100k"]["target_strike_usd"] == 100000.0
    assert by_slug["btc-dip-60k"]["direction"] == "BELOW_STRIKE"
    assert by_slug["btc-dip-60k"]["spot_implied_prob"] < 0.20


def test_offline_upstream_outage_returns_upstream_unavailable_no_fake_fallback(tmp_path, monkeypatch):
    """Verifies all quant engines and DailyTechTrendsRadar fail closed with upstream_unavailable when feeds fail."""
    offline_feed = MagicMock()
    offline_feed.fetch_spot_order_book.side_effect = RuntimeError("network offline")
    offline_feed.fetch_multi_venue_spot.side_effect = RuntimeError("network offline")
    offline_feed.fetch_perp_funding_rate.side_effect = RuntimeError("network offline")
    offline_feed.fetch_recent_trades.side_effect = RuntimeError("network offline")
    offline_feed.fetch_liquidations.side_effect = RuntimeError("network offline")
    offline_feed.fetch_spot_price.side_effect = RuntimeError("network offline")
    offline_feed.fetch_realized_volatility.side_effect = RuntimeError("network offline")
    offline_feed.fetch_polymarket_events.side_effect = RuntimeError("network offline")

    micro = MarketMicrostructureEngine(feed=offline_feed).get_microstructure_metrics("BTC/USDT")
    assert micro["status"] == "upstream_unavailable"
    assert "metrics" not in micro

    arb = CrossExchangeArbitrageScanner(feed=offline_feed).scan_arbitrage_and_funding("BTC/USDT")
    assert arb["status"] == "upstream_unavailable"
    assert "arbitrage_metrics" not in arb

    slip = OrderBookSlippageSimulator(feed=offline_feed).simulate_slippage("BTC/USDT", side="BUY", trade_size_usd=5000.0)
    assert slip["status"] == "upstream_unavailable"
    assert "simulation" not in slip

    whale = SmartMoneyWhaleRadar(feed=offline_feed).get_whale_flow_telemetry("BTC/USDT")
    assert whale["status"] == "upstream_unavailable"
    assert "smart_money_signals" not in whale

    poly = PredictionMarketArbitrageRadar(feed=offline_feed).scan_prediction_arbitrage("BTC", limit=5)
    assert poly["status"] == "upstream_unavailable"
    assert "market_discrepancies" not in poly

    # Also verify DailyTechTrendsRadar returns upstream_unavailable cleanly when live feeds fail and no cache exists
    monkeypatch.setattr(DailyTechTrendsRadar, "CACHE_PATH", str(tmp_path / "missing_tech_cache.json"))
    monkeypatch.setattr(DailyTechTrendsRadar, "_fetch_live_github_repos", staticmethod(lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("gh down"))))
    monkeypatch.setattr(DailyTechTrendsRadar, "_fetch_live_hackernews", classmethod(lambda cls, *a, **kw: (_ for _ in ()).throw(RuntimeError("hn down"))))
    monkeypatch.setattr(DailyTechTrendsRadar, "_fetch_live_arxiv", staticmethod(lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("arxiv down"))))
    radar_res = DailyTechTrendsRadar().refresh_cache_and_get(force_refresh=True)
    assert radar_res["status"] == "upstream_unavailable"
    assert radar_res["trending_github_ai_repos"] == []
    assert radar_res["hackernews_breakouts"] == []





