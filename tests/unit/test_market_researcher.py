import pytest
from agents.discovery.market_researcher import MarketResearchAgent, AgentDemandSignal, MarketResearchDirective
from agents.core.conductor import RaisConductor


def test_market_research_agent_trends_and_signals():
    researcher = MarketResearchAgent()
    trends = researcher.scan_agent_economy_trends()
    assert len(trends) >= 5
    categories = [t["category"] for t in trends]
    assert "PREDICTION_MARKETS" in categories
    assert "CONTEXT_OPTIMIZATION" in categories
    assert "MARKET_MICROSTRUCTURE" in categories


def test_market_research_competitive_moat():
    researcher = MarketResearchAgent()
    moat = researcher.analyze_competitive_moat()
    assert "comparison_metrics" in moat
    assert len(moat["comparison_metrics"]) >= 3
    assert "freemium_conversion_multiplier" in moat


def test_market_research_review_and_directive():
    researcher = MarketResearchAgent()
    sample_catalog = [
        {"concept_id": "PREDICTION_MARKET_ARBITRAGE", "title": "Polymarket Arbitrage", "suggested_price": 0.03},
        {"concept_id": "TOKEN_CONTEXT_COMPRESSOR", "title": "Context Compressor", "suggested_price": 0.01},
        {"concept_id": "AST_SECURITY_LINTER", "title": "Security Linter", "suggested_price": 0.03}
    ]
    review_res = researcher.review_catalog_and_decide(sample_catalog)
    assert review_res["status"] == "REVIEW_COMPLETE"
    assert review_res["total_items_reviewed"] == 3
    directive = review_res["market_directive"]
    assert "prioritized_tools" in directive
    assert len(directive["aeo_target_keywords"]) > 0
    assert "strategic_verdict" in directive


def test_conductor_integrates_market_researcher():
    conductor = RaisConductor()
    report = conductor.run_daily_cycle()
    assert report["status"] == "OPERATIONAL_AND_REVENUE_READY"
    assert "market_research" in report
    mr = report["market_research"]
    assert mr["status"] == "REVIEW_COMPLETE"
    assert "market_directive" in mr
