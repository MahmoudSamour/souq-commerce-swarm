"""
SOUQ // Official 1-Line MCP Client & Autonomous Agent SDK
"""

from .client import SouqClient, PaymentRequiredError

__version__ = "0.3.0"

# Default module-level client instance for ergonomic 1-line usage:
#   from souq_mcp import client
#   client.call_tool("prompt_injection_firewall", {"text": "..."})
client = SouqClient()
call_tool = client.call_tool

__all__ = ["SouqClient", "PaymentRequiredError", "client", "call_tool", "__version__"]
