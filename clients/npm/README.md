# souq-mcp (Node / NPX v0.3.0)

Official 1-line Model Context Protocol (MCP) server & CLI for **SOUQ** — Autonomous Multi-Agent Commerce Swarm on Base L2 USDC.

---

## ⚡ 1-Line Usage (No Installation Needed)

### In Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "souq": {
      "command": "npx",
      "args": ["-y", "souq-mcp"],
      "env": {
        "SOUQ_API_KEY": "optional_prepaid_key_from_topup"
      }
    }
  }
}
```

### In Cursor / Windsurf / Roo Code:
Add an MCP stdio server with:
- **Command**: `npx`
- **Args**: `-y souq-mcp`

### Direct CLI Usage:
```bash
npx -y souq-mcp --help
npx -y souq-mcp status
npx -y souq-mcp list
npx -y souq-mcp call prompt_injection_firewall '{"text": "Ignore prior rules"}'
```

---

## 🛠️ Instant Tool Access (16 Paid Tools + `souq_account_status`)
- **Account Status (`souq_account_status`)**: Free discovery & balance check for `SOUQ_API_KEY` and Base USDC payment rails.
- **Prediction Market Arbitrage Radar (`prediction_market_arbitrage_radar`)**: Arbitrage spreads between Polymarket consensus and spot/volatility Black-Scholes pricing.
- **Token Context Compressor (`token_context_compressor`)**: Slashes JSON, HTML, logs, and markdown bloat by 60-95% to save prompt tokens.
- **Quant Microstructure Radar (`quant_microstructure_radar`)**: Binance order book depth, Order Book Imbalance (OBI), and liquidation risk.
- **Cross-Exchange Arbitrage Scanner (`cross_exchange_arbitrage_scanner`)**: Funding rate APR arbitrage.
- **Order Book Slippage Simulator (`orderbook_slippage_simulator`)**: 100-level VWAP and slippage simulation.
- **Smart Money Whale Flow Radar (`smart_money_whale_flow_radar`)**: Real-time whale blocks (> $50k) and accumulation telemetry.
- **Dev API CheatSheet Vault (`dev_api_cheatsheet_vault`)**: Zero-fluff schemas for OpenAI, Anthropic, Stripe, Base, FastMCP, DuckDB.
- **Daily Tech & AI Trends Radar (`daily_tech_ai_trends_radar`)**: GitHub AI trends, HackerNews, arXiv papers.
- **AST Structural Slicer (`ast_structural_slicer`)**: Surgically extracts targeted functions/classes from source code.
- **AST Security Scanner (`ast_security_scanner`)**: Python/Solidity security auditor.
- **Synthetic Schema Verifier (`synthetic_schema_verifier`)**: Zero-hallucination JSON schema validation.
- **Prompt Injection Firewall (`prompt_injection_firewall`)**: Adversarial prompt injection, jailbreak, and exfiltration detector.
- **Smart Contract Honeypot Radar (`smart_contract_honeypot_radar`)**: Audits Solidity source or live Base `0x...` contracts for honeypots and reentrancy.
- **Secret Leak Scanner (`secret_leak_scanner`)**: High-entropy credential and private key scanner.
- **Deep AST Vulnerability Auditor (`deep_ast_vulnerability_auditor`)**: Deep Python AST vulnerability auditor (SQLi, SSRF, RCE).
- **API Attack Surface Scanner (`api_attack_surface_scanner`)**: HTTP endpoint security header and CORS misconfiguration auditor.

---

## 🎁 Freemium Evaluation & Settlement
- Every IP receives **1 free call per 24h** with zero wallet setup required.
- For unlimited low-latency calls, mint a prepaid `SOUQ_API_KEY` at `https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup` or pass a single-use Base L2 USDC transaction hash via `SOUQ_PAYMENT_TX`.
