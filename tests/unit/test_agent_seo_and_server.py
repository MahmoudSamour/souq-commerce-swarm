import pytest
from starlette.testclient import TestClient
from scripts.koyeb_server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_homepage_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "SOUQ" in response.text
    assert "Token Savings Calculator" in response.text


def test_agent_seo_llms_txt(client):
    response = client.get("/llms.txt")
    assert response.status_code == 200
    assert "SOUQ // Autonomous Agent Commerce" in response.text
    assert "x402-v1.0" in response.text


def test_agent_seo_robots_txt(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "User-agent: GPTBot" in response.text
    assert "User-agent: ClaudeBot" in response.text


def test_agent_seo_sitemap_xml(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "urlset" in response.text


def test_agent_seo_llms_full_txt(client):
    response = client.get("/llms-full.txt")
    assert response.status_code == 200
    assert "SOUQ // Autonomous Multi-Agent Commerce Swarm" in response.text


def test_agent_seo_openapi_json(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"] == "3.1.0"
    assert "/api/tools/call" in data["paths"]


def test_agent_seo_agent_card_json(client):
    response = client.get("/.well-known/agent-card.json")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert len(data["skills"]) >= 10


def test_well_known_mcp_discovery(client):
    response = client.get("/.well-known/mcp.json")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert data["settlement"]["currency"] == "USDC"


def test_health_probe(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_security_headers_and_protection(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # Test payload size protection (simulated 2MB payload)
    large_payload_headers = {"Content-Length": "2097152"}
    oversized_res = client.post("/api/tools/call", headers=large_payload_headers)
    assert oversized_res.status_code == 413
    assert "Payload Too Large" in oversized_res.json()["error"]


def test_free_trial_evaluation_flow(client):
    # First call with no payment receives 1 free trial
    payload = {"tool": "dev_api_cheatsheet_vault", "ecosystem": "openai"}
    res = client.post("/api/tools/call", json=payload)
    assert res.status_code == 200
    assert "cheatsheet" in res.json()
    assert res.headers.get("X-Souq-Billing") == "FREE_TRIAL_EVALUATION"
    assert res.headers.get("X-Souq-Tokens-Saved") == "40000"
    assert res.headers.get("X-Souq-Net-ROI") == "1900%"

    # Second consecutive call with no payment must throw HTTP 402 challenge with economic headers
    res2 = client.post("/api/tools/call", json=payload)
    assert res2.status_code == 402
    assert res2.json()["error"] == "Payment Required"
    assert res2.headers.get("X-Souq-Price-USDC") == "0.01"
    assert res2.headers.get("X-Souq-Tokens-Saved") == "40000"
    assert res2.headers.get("X-Souq-Net-ROI") == "1900%"


def test_prediction_market_arbitrage_server_flow(client):
    # Using a distinct client/IP simulation by passing custom tool call
    payload = {"tool": "prediction_market_arbitrage_radar", "asset": "BTC"}
    res = client.post("/api/tools/call", json=payload)
    # If free trial is already consumed by previous test on testclient IP (127.0.0.1), expect 402 with correct headers
    if res.status_code == 402:
        assert res.headers.get("X-Souq-Tool") == "prediction_market_arbitrage_radar"
        assert res.headers.get("X-Souq-Price-USDC") == "0.03"
        assert res.headers.get("X-Souq-Tokens-Saved") == "35000"
        assert res.headers.get("X-Souq-Net-ROI") == "483%"
    else:
        assert res.status_code == 200
        assert "market_discrepancies" in res.json()
        assert res.headers.get("X-Souq-Tool") == "prediction_market_arbitrage_radar"
        assert res.headers.get("X-Souq-Tokens-Saved") == "35000"

