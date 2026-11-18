# SOUQ // Autonomous Multi-Agent Commerce & MCP Micro-Service Swarm (`v0.3.0`)

**SOUQ** is an autonomous AI-to-AI commerce server exposing **16 paid micro-services** (plus `souq_account_status` for free balance/discovery) for coding agents, DeFi security auditors, and market-quant swarms.

Built with FastMCP, Starlette/Uvicorn, DuckDB, and live market/security feeds — with **Base L2 USDC (`x402-v1.0`)**, **Prepaid `X-API-Key` Credits**, and **Polar.sh MoR Checkout**.

> * **Storefront & Interactive Playground:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/`
> * **Prepaid Credit Minting & Wallet Pay:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup`
> * **Remote MCP (Streamable HTTP):** `https://written-emera-arapython-bf7436a4.apps.mistral.run/mcp` (`POST` JSON-RPC 2.0, `DELETE` session cleanup, `GET` returns `405`)
> * **Freemium Onboarding:** 1 free evaluation trial call per 24 hours per client IP.
> * **Settlement Rails:** Prepaid `X-API-Key` credits (`/api/credits/topup`, zero per-call gas), native per-call HTTP `402` Base L2 USDC (`0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF`), or Polar.sh checkout (`/api/checkout/create` + `/api/checkout/claim`).

---

## Quickstart for Developers & AI Agents

### Option A: Zero-Install Remote Streamable HTTP (`/mcp`)
Connect any Streamable-HTTP-compatible MCP client directly without installing local packages:

```json
{
  "mcpServers": {
    "souq": {
      "url": "https://written-emera-arapython-bf7436a4.apps.mistral.run/mcp",
      "headers": {
        "X-API-Key": "optional_souq_live_key_from_topup"
      }
    }
  }
}
```

### Option B: Local stdio Bridge (`clients/npm` & `clients/python`)
> **Readiness Note:** Both the npm bridge (`clients/npm`, package name `souq-mcp`) and Python package (`clients/python`, package name `souq-mcp`, module `souq_mcp`) live in this repository. Before/until public npm & PyPI releases are published for a given environment, install locally from source (or use Option A Remote HTTP `/mcp` immediately).

```bash
# Node.js stdio bridge (from clients/npm or published npm package `souq-mcp`)
npx -y souq-mcp

# Python stdio bridge & CLI (from clients/python or editable install `pip install -e clients/python`)
python -m souq_mcp serve
SOUQ_API_KEY="souq_live_..." python -m souq_mcp status
SOUQ_API_KEY="souq_live_..." python -m souq_mcp list
SOUQ_API_KEY="souq_live_..." python -m souq_mcp call token_context_compressor '{"raw_content":"...","mode":"auto"}'
```

### Option C: Direct Python SDK (`SouqClient`)

```python
from souq_mcp import SouqClient

# 1. Free daily evaluation (or supply api_key / private_key for unlimited calls)
client = SouqClient(
    endpoint="https://written-emera-arapython-bf7436a4.apps.mistral.run",
    api_key="souq_live_your_key_here",
)

# Check account status & pricing
print(client.balance())

# Compress bloated HTML/logs (60-95% context reduction)
res = client.call_tool(
    "token_context_compressor",
    {"raw_content": "<html>...logs...</html>", "mode": "auto"},
)
print(res)
```

---

## Complete Service Catalog (`16` Active Paid Tools + `1` Free Discovery Tool)

### Free MCP Discovery Tool (`$0.00`)
| Tool | Purpose |
|---|---|
| `souq_account_status` | Inspects prepaid `X-API-Key` credit balance, Base L2 USDC recipient wallet, and full tool catalog. |

### Active Paid Tools (`16` Tools, `$0.01 – $0.03 USDC` / call)
| Category | Tool Name | Price (USDC) | Capabilities & Key Parameters |
|---|---|---|---|
| **Optimization** | `token_context_compressor` | **$0.01** | Token pruning for HTML, JSON, logs, markdown, prose (`raw_content`, `max_compression`, `mode`, `target_ratio`). |
| **Code Intel** | `ast_structural_slicer` | **$0.02** | Exact AST function/class extraction for Python/Solidity (`source_code`, `target_symbol`). |
| **Security** | `ast_security_scanner` | **$0.03** | Static AST security linter catching `eval`, `exec`, shell execution (`source_code`). |
| **Cyber Defense** | `prompt_injection_firewall` | **$0.01** | Prompt injection, DAN jailbreak, and exfiltration firewall (`text`, `strict_mode`). |
| **Cyber Defense** | `smart_contract_honeypot_radar` | **$0.03** | Solidity source & live Base address honeypot/reentrancy audit (`source_code`, `contract_address`, `token_symbol`). |
| **Cyber Defense** | `secret_leak_scanner` | **$0.01** | High-entropy API key & private key secret detector (`content`, `entropy_threshold`). |
| **Cyber Defense** | `deep_ast_vulnerability_auditor` | **$0.03** | Deep Python AST audit for SQLi, SSRF, YAML/pickle RCE (`source_code`). |
| **Cyber Defense** | `api_attack_surface_scanner` | **$0.02** | Live HTTPS security headers, CORS, and endpoint exposure scanner (`target_url`, `headers_to_check`). |
| **Market Quant** | `quant_microstructure_radar` | **$0.02** | Live order book depth, spread bps, Order Book Imbalance (`symbol`). |
| **Market Quant** | `cross_exchange_arbitrage_scanner` | **$0.03** | Spot vs Perpetual basis spreads & funding APR (`symbol`). |
| **Market Quant** | `orderbook_slippage_simulator` | **$0.02** | Live depth VWAP & slippage bps simulation (`symbol`, `side` `BUY`/`SELL`, `trade_size_usd`). |
| **Market Quant** | `smart_money_whale_flow_radar` | **$0.03** | Block trade & limit wall Whale Accumulation Index (`symbol`, `block_threshold_usd`). |
| **Prediction** | `prediction_market_arbitrage_radar` | **$0.03** | Live Polymarket binary prices vs Black-Scholes realized-vol probabilities (`asset`, `limit`). |
| **Developer Intel** | `dev_api_cheatsheet_vault` | **$0.01** | High-density schemas (`openai`, `anthropic`, `stripe`, `base_evm`, `fastmcp`, `duckdb`). |
| **Tech Intel** | `daily_tech_ai_trends_radar` | **$0.01** | Live AI radar across GitHub, HackerNews, and arXiv (`force_refresh`). |
| **Verification** | `synthetic_schema_verifier` | **$0.01** | Deterministic JSON type schema validation (`data`, `schema`). |

> **External Feed Readiness Note:** Live market, Polymarket, GitHub/HN/arXiv, and HTTPS auditing tools fetch real upstream data without fabricated numbers; if an upstream feed is offline or blocked in a sandboxed environment, tools return an explicit `upstream_unavailable` error envelope (with automatic `X-API-Key` debit refund on upstream failure).
> **Polar Digital Assets Note:** Call `GET /api/products` (or inspect `/#topup` in the browser) to see live `ready: true` vs `ready: false` status on Polar SKUs before initiating card checkouts.

---

## Key HTTP Endpoints & Discovery Manifests

| Endpoint | Purpose |
|---|---|
| `GET /` | Interactive storefront UI, 16-tool sandbox, Token ROI calculator, 1-click Base USDC Wallet Pay (`/#topup`), Polar claim handler |
| `POST /mcp` | Streamable HTTP MCP JSON-RPC 2.0 (`initialize`, `tools/list`, `tools/call`) |
| `GET /api/catalog` | Full 16-tool machine catalog, recipient wallet, Polar readiness summary |
| `GET /api/products` | Live Polar.sh credit packs & digital asset catalog with `ready` flags |
| `POST /api/tools/call` | Direct REST tool execution (`X-API-Key`, `X-Payment-Tx`, or 1/24h free trial) |
| `POST /api/credits/topup` | Verify Base Mainnet USDC tx (`>= $0.50`) and mint/top up `souq_live_...` key |
| `GET /api/credits/balance` | Inspect prepaid balance & spend for an `X-API-Key` |
| `POST /api/checkout/create` | Create Polar MoR card checkout link with same-origin `success_url` validation |
| `GET /api/checkout/claim` | One-time exchange of `?claim=...` / `?order_id=...` for provisioned `souq_live_...` key |
| `GET /api/cyber/threat-intel` | Sayf Cyber Threat Intelligence rule counts and update metadata |
| `GET /api/stats` | Public aggregate traffic & settlement KPIs (admin details redacted without `SOUQ_ADMIN_TOKEN`) |
| `GET /health` | Edge service health & readiness status (`version: "0.3.0"`) |
| `GET /.well-known/mcp.json` | MCP discovery manifest |
| `GET /.well-known/agent-card.json` | Agent-to-Agent discovery card (`/.well-known/agent.json` alias also served) |
| `GET /openapi.json` | OpenAPI `3.1.0` REST + MCP specification |
| `GET /llms.txt`, `/llms-full.txt` | Concise and exhaustive LLM crawler indexes |

---

## Local Development, Verification & Shell Entrypoints

```bash
# Run edge server locally via project venv (scripts/koyeb_server.py)
./souq.sh server 8402

# Run unit & integration test suite (.venv/bin/pytest)
./souq.sh test

# Verify core engines safely inside an isolated TemporaryDirectory (zero writes to data/)
/home/mm/Souq/souq-commerce-swarm/.venv/bin/python scripts/verify_full_system.py

# Export real (non-simulated) tax & audit CSV/JSON receipts
/home/mm/Souq/souq-commerce-swarm/.venv/bin/python scripts/export_tax_receipts.py --db-path data/souq_treasury_lake.duckdb --output-dir data/exports

# Execute end-to-end canary buyer check (or live Base USDC micro-settlement)
/home/mm/Souq/souq-commerce-swarm/.venv/bin/python scripts/canary_buyer_agent.py --simulate --tool token_context_compressor
```

## License
MIT
