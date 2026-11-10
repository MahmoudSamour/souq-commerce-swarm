import pytest
from agents.analytics.negotiation_tracker import NegotiationTracker


@pytest.fixture
def temp_tracker(tmp_path):
    db_file = str(tmp_path / "test_negotiations.duckdb")
    return NegotiationTracker(db_path=db_file)


def test_negotiation_logging_and_summary(temp_tracker):
    # Log 1: Settled call
    temp_tracker.log_negotiation(
        client_agent_id="agent_alpha",
        client_user_agent="CrewAI-Agent/2.0",
        tool_requested="quant_microstructure_radar",
        initial_quote_usd=0.02,
        settled_price_usd=0.02,
        payment_protocol="x402_http",
        outcome="SETTLED",
        latency_ms=120
    )

    # Log 2: Challenged call
    temp_tracker.log_negotiation(
        client_agent_id="agent_beta",
        client_user_agent="Claude-Code-Agent/1.0",
        tool_requested="ast_security_scanner",
        initial_quote_usd=0.03,
        settled_price_usd=None,
        payment_protocol="x402_http",
        outcome="CHALLENGED_402",
        latency_ms=5
    )

    summary = temp_tracker.get_market_intelligence_summary()
    assert summary["total_interactions"] == 2
    assert summary["successful_settlements"] == 1
    assert summary["conversion_rate_pct"] == 50.0
    assert len(summary["tool_telemetry"]) == 2
