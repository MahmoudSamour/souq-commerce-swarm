import io
import json
import os
import sys
import urllib.error
from unittest.mock import patch, MagicMock

# Add clients/python to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../clients/python")))

import souq_mcp
from souq_mcp.client import SouqClient
from souq_mcp.mcp_server import StdioMCPServer, TOOLS_METADATA


def test_client_initialization():
    client = SouqClient(endpoint="https://test.souq.run", api_key="souq_live_demo")
    assert client.endpoint == "https://test.souq.run"
    assert client.api_url == "https://test.souq.run/api/tools/call"
    assert client.api_key == "souq_live_demo"
    assert hasattr(souq_mcp, "client")
    assert callable(souq_mcp.call_tool)


def test_mcp_metadata_completeness():
    assert len(TOOLS_METADATA) == 17
    tool_names = [t["name"] for t in TOOLS_METADATA]
    assert "souq_account_status" in tool_names
    assert "prediction_market_arbitrage_radar" in tool_names
    assert "token_context_compressor" in tool_names
    assert "quant_microstructure_radar" in tool_names
    assert "prompt_injection_firewall" in tool_names
    assert "smart_contract_honeypot_radar" in tool_names
    assert "secret_leak_scanner" in tool_names


def test_mcp_server_initialize_rpc():
    server = StdioMCPServer()
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    resp = server.handle_message(init_msg)
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "souq-mcp"
    assert resp["result"]["serverInfo"]["version"] == "0.3.0"
    assert "protocolVersion" in resp["result"]


def test_mcp_server_tools_list_rpc():
    server = StdioMCPServer()
    list_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    resp = server.handle_message(list_msg)
    assert resp["id"] == 2
    assert len(resp["result"]["tools"]) == 17


def test_client_dict_and_kwargs_signatures_and_402_retry():
    captured_requests = []

    class _FakeResp:
        def __init__(self, body_dict, headers=None, status=200):
            self._body = json.dumps(body_dict).encode("utf-8")
            self.headers = headers or {}
            self.status = status

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=30.0):
        captured_requests.append(req)
        # First test uses dict call -> returns 200 directly
        if len(captured_requests) == 1:
            return _FakeResp({"verdict": "SAFE"}, {"X-Souq-Billing": "FREE_TRIAL_EVALUATION"})
        # Second test uses kwargs + API key -> simulates 402 then settled retry
        if len(captured_requests) == 2:
            challenge = json.dumps({
                "status_code": 402,
                "payment_details": {
                    "amount": "0.0200",
                    "chain": "Base",
                    "recipient_address": "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF",
                }
            }).encode("utf-8")
            raise urllib.error.HTTPError(
                req.full_url,
                402,
                "Payment Required",
                {"X-Souq-Price-USDC": "0.02", "X-Souq-Recipient": "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF"},
                io.BytesIO(challenge),
            )
        return _FakeResp({"verdict": "CLEAN"}, {"X-Souq-Billing": "PAID_SETTLEMENT"})

    client = SouqClient(endpoint="https://test.souq.run", private_key="0x" + "1" * 64, api_key="souq_live_abc")
    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        with patch.object(client, "_settle_usdc_payment", return_value="0x" + "a" * 64):
            r1 = client.call_tool("prompt_injection_firewall", {"text": "hello"})
            assert r1["status_code"] == 200
            body1 = json.loads(captured_requests[0].data.decode("utf-8"))
            assert body1 == {"tool": "prompt_injection_firewall", "text": "hello"}
            assert captured_requests[0].headers.get("X-api-key") == "souq_live_abc"

            r2 = client.call_tool("ast_security_scanner", source_code="x = 1")
            assert r2["billing"] == "PAID_USDC_BASE"
            assert r2["tx_hash"] == "0x" + "a" * 64
            retry_req = captured_requests[2]
            retry_body = json.loads(retry_req.data.decode("utf-8"))
            assert retry_req.headers.get("X-payment-tx") == "0x" + "a" * 64
            assert retry_body["payment_tx_hash"] == "0x" + "a" * 64
