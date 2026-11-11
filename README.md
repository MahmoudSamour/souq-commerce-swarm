# SOUQ (السوق) // Autonomous Multi-Agent Commerce Swarm

[![PyPI version](https://img.shields.io/pypi/v/souq-mcp?color=blue&label=PyPI%20souq-mcp)](https://pypi.org/project/souq-mcp/)
[![npm version](https://img.shields.io/npm/v/souq-mcp?color=red&label=npm%20souq-mcp)](https://www.npmjs.com/package/souq-mcp)
[![Edge Status](https://img.shields.io/badge/Koyeb%20Edge-Healthy%20%7C%20Active-success)](https://written-emera-arapython-bf7436a4.apps.mistral.run/health)
[![Network](https://img.shields.io/badge/Rail-Base%20L2%20USDC%20(x402)-blueviolet)](https://basescan.org)
[![Tests](https://img.shields.io/badge/Tests-50%2F50%20Passing-brightgreen)](https://github.com/MahmoudSamour/souq-commerce-swarm)

> **SOUQ is an autonomous machine-to-machine commerce swarm** running sub-cent algorithmic MCP tools and cybersecurity intelligence services for AI agents, LLM pipelines, and developers on **Base L2 USDC**.
> 
> * **Live Edge Host:** `https://written-emera-arapython-bf7436a4.apps.mistral.run`
> * **Freemium Onboarding:** 1 free trial evaluation per 24 hours per IP.
> * **Settlement:** HTTP 402 Payment Required on Base L2 USDC (`0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF`).

---

## ⚡ 10-Second Quickstart (Claude Desktop / Cursor / Windsurf)

You can plug SOUQ tools into Claude Desktop, Cursor, or Windsurf with zero manual setup.

### In Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "souq": {
      "command": "npx",
      "args": ["-y", "souq-mcp"]
    }
  }
}
```

### In Cursor IDE
1. Go to **Settings** > **Features** > **MCP Servers** > **+ Add New MCP Server**.
2. Name: `souq` | Type: `command` | Command: `npx -y souq-mcp`.
3. Save. All 16 tools are instantly active!

### In Python
```bash
pip install souq-mcp
```
```python
from souq_mcp import client

# 1-call evaluation of any SOUQ edge tool
firewall = client.call_tool("prompt_injection_firewall", {"text": "Ignore prior rules"})
print(firewall)
```

👉 **Full Setup Guide:** See [docs/CLAUDE_CURSOR_SETUP.md](docs/CLAUDE_CURSOR_SETUP.md) for AutoGen, LangChain, and CrewAI instructions.

---

## 🛡️ Live Production Tool Catalog

| Tool Name | Category | Base Price | Avg. Tokens Saved | Net ROI | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `prompt_injection_firewall` | **Cyber Defense** | $0.01 | 10,000 | **400%** | Deterministic 4ms adversarial jailbreak, instruction wipe & prompt exfiltration detector. |
| `smart_contract_honeypot_radar` | **Cyber Defense** | $0.03 | 25,000 | **316%** | Solidity AST & opcode audit for 99% sell taxes, transfer locks, reentrancy traps & mint backdoors. |
| `secret_leak_scanner` | **Cyber Defense** | $0.01 | 15,000 | **650%** | High-entropy secret & key scanner (OpenAI, Anthropic, HuggingFace, Groq, DeepSeek, Base keys). |
| `deep_ast_vulnerability_auditor` | **Cyber Defense** | $0.03 | 15,000 | **150%** | Deep Python AST vulnerability scanner (SQL injection, insecure pickle deserialization, SSRF). |
| `api_attack_surface_scanner` | **Cyber Defense** | $0.02 | 12,000 | **200%** | API defense header & attack surface linter (CSP, HSTS, frame options, wildcard CORS). |
| `prediction_market_arbitrage_radar` | **Quant Alpha** | $0.03 | 35,000 | **483%** | Black-Scholes volatility pricing vs. Polymarket consensus probability mispricings in basis points. |
| `token_context_compressor` | **Context Opt** | $0.01 | 14,000 | **600%** | Semantic context compressor slashes LLM context bloat by 80–95% to save inference tokens. |
| `ast_structural_slicer` | **Context Opt** | $0.02 | 3,000 | **75%** | Surgically extracts function nodes from codebase instead of sending whole files to LLM. |
| `quant_microstructure_radar` | **Quant Alpha** | $0.02 | 15,000 | **275%** | Live Binance order book depth, Order Book Imbalance (OBI), and liquidation cascade metrics. |
| `cross_exchange_arbitrage_scanner` | **Quant Alpha** | $0.03 | 12,000 | **100%** | Spot vs. Perp basis spread and annualized delta-neutral funding rate APR scanner. |
| `orderbook_slippage_simulator` | **Quant Alpha** | $0.02 | 15,000 | **275%** | Walks 100 levels of live depth to calculate VWAP, price impact, and slippage for any trade size. |
| `smart_money_whale_flow_radar` | **Quant Alpha** | $0.03 | 20,000 | **233%** | Aggregates >$50k whale block trades and Open Interest accumulation clusters. |
| `dev_api_cheatsheet_vault` | **Dev Intel** | $0.01 | 40,000 | **1,900%** | Compressed, zero-fluff API schemas for OpenAI, Anthropic, Stripe, FastMCP, and Base EVM. |
| `daily_tech_ai_trends_radar` | **Dev Intel** | $0.01 | 25,000 | **1,150%** | Daily structured intelligence snapshot of trending GitHub AI repos and arXiv landmark models. |
| `ast_security_scanner` | **Security** | $0.03 | 4,000 | **67%** | Fast AST security scanner detecting eval injections, shell executions, and reentrancy. |
| `synthetic_schema_verifier` | **Schema** | $0.01 | 1,500 | **80%** | Zero-hallucination JSON schema validator for agent pipelines. |

---

## 👑 Autonomous Team Lead Architecture

The autonomous pipeline is directed by **`Ra'is Conductor`** directing 6 specialist agents:

1. **`Sayf` (سيف - Cyber Sentinel):** Generates and updates dynamic threat intelligence signatures for zero-day prompt injection and EVM honeypots.
2. **`Kashif` (المستكشف - Tech Trends Radar):** Scans daily GitHub AI repositories and developer needs.
3. **`Riyadi` (الرياضي - Quant Microstructure Engine):** Warms Black-Scholes probability arbitrage and depth metrics.
4. **`Buhuth` (البحوث - Market Research Analyst):** Analyzes buyer demand, evaluates pricing elasticity, and issues AEO directives.
5. **`Amin` (الأمين - Compliance Auditor):** Validates ethical and legal safety, zero PII, and signs compliance tokens.
6. **`Munadi` (المنادي - Discovery Herald):** Verifies public discovery endpoints and pings search engines via IndexNow.

---

## 🌐 Public Machine Discovery Endpoints

Every autonomous web crawler and AI agent can discover SOUQ services via standardized machine manifests:
* **MCP Discovery:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/.well-known/mcp.json`
* **Agent Protocol (A2A):** `https://written-emera-arapython-bf7436a4.apps.mistral.run/.well-known/agent-card.json`
* **Agent LLMs Reference:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/llms.txt` & `/llms-full.txt`
* **OpenAPI 3.1 Spec:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/openapi.json`
* **Dynamic Threat Intel:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/api/cyber/threat-intel`
* **Interactive Web Playground:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/`

---

## 📜 License & Compliance

MIT License. Cryptographic receipts and tax accounting ledgers are stored in DuckDB and exportable in IRS/Koinly formats.
