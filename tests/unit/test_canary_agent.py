import pytest
from scripts.canary_buyer_agent import CanaryBuyerAgent, EXPECTED_RECIPIENT, EXPECTED_NETWORK


def test_canary_agent_config():
    agent = CanaryBuyerAgent(base_url="https://test.souq.run", buyer_id="test_buyer")
    assert agent.base_url == "https://test.souq.run"
    assert agent.api_url == "https://test.souq.run/api/tools/call"
    assert agent.buyer_id == "test_buyer"
    assert EXPECTED_RECIPIENT == "0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF"
    assert EXPECTED_NETWORK == "Base"
