import sys
import json
import logging
from typing import Dict, Any, Optional
from .client import SouqClient

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

TOOLS_METADATA = [
    {
        "name": "token_context_compressor",
        "description": "Slashes LLM context bloat by 80-95% to save prompt tokens ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_content": {"type": "string", "description": "The raw text, markdown, or code to compress"}
            },
            "required": ["raw_content"]
        }
    },
    {
        "name": "ast_structural_slicer",
        "description": "Surgically slices targeted AST functions from source code ($0.02 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_code": {"type": "string", "description": "The Python or Solidity source code"},
                "target_symbol": {"type": "string", "description": "The function or class name to slice"}
            },
            "required": ["source_code", "target_symbol"]
        }
    },
    {
        "name": "quant_microstructure_radar",
        "description": "Real-time Binance order book depth, Order Book Imbalance (OBI), and liquidation risk ($0.02 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "default": "BTC/USDT", "description": "Trading pair symbol"}
            }
        }
    },
    {
        "name": "cross_exchange_arbitrage_scanner",
        "description": "Scans Spot vs Perpetual Futures basis spreads and annualized delta-neutral funding APR ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "default": "BTC/USDT", "description": "Trading pair symbol"}
            }
        }
    },
    {
        "name": "orderbook_slippage_simulator",
        "description": "Walks live Binance order book depth (100 levels) to simulate VWAP, slippage bps, and price impact ($0.02 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "default": "BTC/USDT"},
                "side": {"type": "string", "enum": ["BUY", "SELL"], "default": "BUY"},
                "trade_size_usd": {"type": "number", "default": 10000.0}
            }
        }
    },
    {
        "name": "smart_money_whale_flow_radar",
        "description": "Aggregates live whale block trades (> $50k) and computes Whale Accumulation Index ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "default": "BTC/USDT"},
                "block_threshold_usd": {"type": "number", "default": 50000.0}
            }
        }
    },
    {
        "name": "dev_api_cheatsheet_vault",
        "description": "Compressed API schemas and snippets for major developer platforms (openai, anthropic, stripe, base_evm, fastmcp, duckdb) ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ecosystem": {"type": "string", "enum": ["openai", "anthropic", "stripe", "base_evm", "fastmcp", "duckdb"], "default": "openai"}
            }
        }
    },
    {
        "name": "daily_tech_ai_trends_radar",
        "description": "Daily intelligence snapshot of trending GitHub AI repos, HackerNews, and arXiv ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "force_refresh": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "prediction_market_arbitrage_radar",
        "description": "Cross-market probability discrepancy engine between Polymarket consensus and spot/volatility Black-Scholes pricing ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "default": "BTC", "description": "Target crypto asset (BTC, ETH, SOL)"}
            }
        }
    },
    {
        "name": "ast_security_scanner",
        "description": "Static AST code security linter for Python and Solidity ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_code": {"type": "string", "description": "Source code to audit for vulnerabilities"}
            },
            "required": ["source_code"]
        }
    },
    {
        "name": "synthetic_schema_verifier",
        "description": "Validates JSON objects against standard schema constraints ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object", "description": "The JSON object to validate"},
                "schema": {"type": "object", "description": "Target field-to-type validation mapping"}
            },
            "required": ["data", "schema"]
        }
    }
]


class StdioMCPServer:
    """
    Standard Model Context Protocol (MCP) JSON-RPC 2.0 stdio server.
    Plugs natively into Claude Desktop, Cursor, Windsurf, Roo Code, and AI Agents.
    """

    def __init__(self):
        self.client = SouqClient()

    def run(self):
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                response = self.handle_message(msg)
                if response:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": None
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

    def handle_message(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "souq-mcp",
                        "version": "0.1.0"
                    }
                }
            }

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS_METADATA}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                res = self.client.call_tool(tool_name, **arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(res, indent=2)}
                        ]
                    }
                }
            except Exception as ex:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "isError": True,
                    "result": {
                        "content": [
                            {"type": "text", "text": f"Error executing tool {tool_name}: {str(ex)}"}
                        ]
                    }
                }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            }
