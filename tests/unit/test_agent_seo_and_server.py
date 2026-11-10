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

