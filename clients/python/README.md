# SOUQ MCP Client (`souq-mcp`)

Official 1-line Python SDK and Model Context Protocol (MCP) server for **SOUQ** — the autonomous agent commerce swarm offering sub-cent algorithmic intelligence and token-saving micro-services on Base L2 USDC.

---

## ⚡ Quick Start: 1-Line Usage

### 1. In Claude Desktop / Cursor / Windsurf / Roo Code (MCP Stdio)
Add this single line to your MCP server configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "souq": {
      "command": "uvx",
      "args": ["souq-mcp"]
    }
  }
}
```

### 2. In Python Code
```bash
pip install souq-mcp
```

```python
from souq_mcp import SouqClient

client = SouqClient()

# Free daily evaluation call included automatically!
arbitrage = client.prediction_arbitrage("BTC")
print(arbitrage)

# Compress massive contexts to slash 80-95% prompt tokens:
compressed = client.compress("massive raw documentation text...")
print(compressed)
```

---

## 🛠️ Built-in Tools Available
1. `prediction_market_arbitrage_radar` ($0.03 USDC, saves 35k tokens) - Black-Scholes implied probabilities vs Polymarket consensus mispricing.
2. `token_context_compressor` ($0.01 USDC, saves 10k-30k tokens) - Semantic compression reducing context bloat by 80-95%.
3. `quant_microstructure_radar` ($0.02 USDC, saves 15k tokens) - Binance order book depth, Order Book Imbalance (OBI), liquidation cascade risk.
4. `cross_exchange_arbitrage_scanner` ($0.03 USDC, saves 12k tokens) - Spot vs Perp funding rate APR arbitrage.
5. `orderbook_slippage_simulator` ($0.02 USDC, saves 15k tokens) - 100-level VWAP execution and slippage modeling.
6. `smart_money_whale_flow_radar` ($0.03 USDC, saves 20k tokens) - Real-time block trade flows and Whale Accumulation Index.
7. `dev_api_cheatsheet_vault` ($0.01 USDC, saves 40k tokens) - Zero-fluff schemas for OpenAI, Anthropic, Stripe, Base, FastMCP.
8. `daily_tech_ai_trends_radar` ($0.01 USDC, saves 25k tokens) - GitHub AI trends, HackerNews breakouts, arXiv landmark papers.
9. `ast_security_scanner` ($0.03 USDC, saves 4k tokens) - Python/Solidity security auditor.
10. `ast_structural_slicer` ($0.02 USDC, saves 3k tokens) - Slices isolated functions/classes from AST.
11. `synthetic_schema_verifier` ($0.01 USDC, saves 1.5k tokens) - Zero-hallucination JSON schema validation.

---

## 💳 Settlement & Free Tier
- **First Call Free**: SOUQ grants 1 free evaluation call per IP per day with zero wallet configuration required.
- **Micro-payments**: SOUQ uses standard HTTP 402 with Base L2 USDC micro-settlement. Configure `private_key` in `SouqClient` or export `SOUQ_AGENT_PRIVATE_KEY` for automated on-chain execution.
