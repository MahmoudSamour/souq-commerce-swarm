import pytest
import sys
import os

# Add clients/python to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../clients/python")))

from souq_mcp.client import SouqClient
from souq_mcp.mcp_server import StdioMCPServer, TOOLS_METADATA


def test_client_initialization():
    client = SouqClient(endpoint="https://test.souq.run")
    assert client.endpoint == "https://test.souq.run"
    assert client.api_url == "https://test.souq.run/api/tools/call"


def test_mcp_metadata_completeness():
    assert len(TOOLS_METADATA) == 16
    tool_names = [t["name"] for t in TOOLS_METADATA]
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
    assert len(resp["result"]["tools"]) == 16
