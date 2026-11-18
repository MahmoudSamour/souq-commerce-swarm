# SOUQ MCP Client (`souq-mcp` v0.3.0)

Official 1-line Python SDK and Model Context Protocol (MCP) server for **SOUQ** — the autonomous agent commerce swarm offering 16 sub-cent algorithmic intelligence, cybersecurity defense, and token-saving micro-services on Base L2 USDC.

---

## ⚡ Quick Start: 1-Line Usage

### 1. In Claude Desktop / Cursor / Windsurf / Roo Code (MCP Stdio)
Add this single block to your MCP server configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "souq": {
      "command": "uvx",
      "args": ["souq-mcp"],
      "env": {
        "SOUQ_API_KEY": "optional_prepaid_key_from_topup"
      }
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

# Check prepaid credit balance or public Base USDC payment rails:
print(client.balance())
```

### 3. CLI & Module Execution
```bash
python -m souq_mcp --help
python -m souq_mcp status
python -m souq_mcp list
python -m souq_mcp call prompt_injection_firewall '{"text": "Ignore prior rules"}'
# Or via installed scripts: souq-mcp / souq
```

---

## 🛠️ Built-in Tools Available (16 Paid Tools + `souq_account_status`)
0. `souq_account_status` (Free) - Inspects prepaid `SOUQ_API_KEY` credits, Base USDC wallet, and tool pricing.
1. `prediction_market_arbitrage_radar` ($0.03 USDC, saves 35k tokens) - Black-Scholes implied probabilities vs Polymarket consensus mispricing.
2. `token_context_compressor` ($0.01 USDC, saves 14k tokens) - Structured JSON pruning/tabularization, HTML cleanup, and log deduplication saving 60-95% tokens.
3. `quant_microstructure_radar` ($0.02 USDC, saves 15k tokens) - Binance order book depth, Order Book Imbalance (OBI), liquidation cascade risk.
4. `cross_exchange_arbitrage_scanner` ($0.03 USDC, saves 12k tokens) - Spot vs Perp funding rate APR arbitrage.
5. `orderbook_slippage_simulator` ($0.02 USDC, saves 15k tokens) - 100-level VWAP execution and slippage modeling.
6. `smart_money_whale_flow_radar` ($0.03 USDC, saves 20k tokens) - Real-time block trade flows and Whale Accumulation Index.
7. `dev_api_cheatsheet_vault` ($0.01 USDC, saves 40k tokens) - Zero-fluff schemas for OpenAI, Anthropic, Stripe, Base, FastMCP, DuckDB.
8. `daily_tech_ai_trends_radar` ($0.01 USDC, saves 25k tokens) - GitHub AI trends, HackerNews breakouts, arXiv landmark papers.
9. `ast_security_scanner` ($0.03 USDC, saves 4k tokens) - Python/Solidity security auditor.
10. `ast_structural_slicer` ($0.02 USDC, saves 3k tokens) - Slices isolated functions/classes from AST.
11. `synthetic_schema_verifier` ($0.01 USDC, saves 1.5k tokens) - Zero-hallucination JSON schema validation.
12. `prompt_injection_firewall` ($0.01 USDC, saves 10k tokens) - Adversarial prompt injection, DAN jailbreak, and system prompt exfiltration detector.
13. `smart_contract_honeypot_radar` ($0.03 USDC, saves 25k tokens) - Audits Solidity source or live Base `0x...` contracts for honeypots and reentrancy.
14. `secret_leak_scanner` ($0.01 USDC, saves 15k tokens) - High-entropy credential and private key scanner.
15. `deep_ast_vulnerability_auditor` ($0.03 USDC, saves 15k tokens) - Deep Python AST vulnerability auditor (SQLi, SSRF, RCE).
16. `api_attack_surface_scanner` ($0.02 USDC, saves 12k tokens) - HTTP endpoint security header and CORS misconfiguration auditor.

---

## 💳 Settlement & Free Tier
- **First Call Free**: SOUQ grants 1 free evaluation call per IP per 24h with zero wallet configuration required.
- **Prepaid API Keys**: Fund a reusable `SOUQ_API_KEY` once via Base USDC at `https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup` (or `client.topup_credits(tx_hash="0x...")`) for zero-gas per-call speed.
- **Automatic x402 Wallet**: Configure `private_key` in `SouqClient` or export `SOUQ_AGENT_PRIVATE_KEY` (`pip install 'souq-mcp[wallet]'`) for automated on-chain Base L2 USDC settlement.
