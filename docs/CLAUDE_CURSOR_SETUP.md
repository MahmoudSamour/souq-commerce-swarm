# Connect SOUQ to Claude Desktop, Cursor, Windsurf & AI Agents (`v0.3.0`)

SOUQ exposes **16 paid micro-services** (`$0.01 – $0.03 USDC` / call) plus **`souq_account_status`** (free discovery & balance inspection) alongside REST APIs (`/api/catalog`, `/api/products`, `/api/credits/*`, `/api/checkout/*`, `/api/tools/call`).

Live Edge Endpoint:
`https://written-emera-arapython-bf7436a4.apps.mistral.run`

---

## 1. Zero-Install Remote Streamable HTTP (`/mcp`) — Recommended

Modern MCP clients that support Streamable HTTP can connect directly to `/mcp` without installing local Node.js or Python packages:

- **URL:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/mcp`
- **Transport:** `POST /mcp` (JSON-RPC 2.0 requests), `DELETE /mcp` (session close). Note: `GET /mcp` intentionally returns HTTP `405` because SOUQ uses stateless Streamable HTTP request/response without SSE streaming.

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

---

## 2. Claude Desktop / Cursor via Local stdio Bridge

> **Package Readiness Note:** The Node.js bridge (`clients/npm`, package name `souq-mcp`) and Python package (`clients/python`, package name `souq-mcp`, module `souq_mcp`) live in this repository. Before/until public npm or PyPI registries publish `souq-mcp`, install locally from the repo (or use Remote HTTP `/mcp` in Section 1).

### Option A: Node.js stdio Proxy (`npx -y souq-mcp`)

Add to your `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`, Linux: `~/.config/Claude/claude_desktop_config.json`) or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "souq": {
      "command": "npx",
      "args": ["-y", "souq-mcp"],
      "env": {
        "SOUQ_ENDPOINT": "https://written-emera-arapython-bf7436a4.apps.mistral.run",
        "SOUQ_API_KEY": "optional_souq_live_key_from_topup"
      }
    }
  }
}
```

If running directly from a local checkout without npm registry publish:
```bash
node /path/to/souq-commerce-swarm/clients/npm/bin/souq-mcp.js
```

### Option B: Python stdio Server & CLI (`python -m souq_mcp`)

Install locally with `pip install -e ./clients/python` (or from `souq-mcp` once published to PyPI), then configure:

```json
{
  "mcpServers": {
    "souq": {
      "command": "python",
      "args": ["-m", "souq_mcp", "serve"],
      "env": {
        "SOUQ_ENDPOINT": "https://written-emera-arapython-bf7436a4.apps.mistral.run",
        "SOUQ_API_KEY": "optional_souq_live_key_from_topup"
      }
    }
  }
}
```

Verified `python -m souq_mcp` CLI subcommands (`clients/python/souq_mcp/cli.py`):
- `python -m souq_mcp serve` — run the stdio MCP server (default when no subcommand is given)
- `python -m souq_mcp status [--api-key souq_live_...]` — inspect prepaid balance & Base USDC payment details (uses `SOUQ_ENDPOINT` / `SOUQ_API_KEY` env vars)
- `python -m souq_mcp list` — fetch `/api/catalog` tool list & ROI metrics
- `python -m souq_mcp call <tool> ['{"arg":"val"}'] [--api-key souq_live_...]` — execute a tool directly from shell

---

## 3. Funding Unlimited Calls (`/#topup` & Payment Flows)

By default, every client IP receives **1 free trial call every 24 hours**. For continuous production runs:

### A. 1-Click Base USDC Wallet Pay or Manual Tx Mint (`/#topup`)
1. Open `https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup`.
2. Connect an EVM wallet (`window.ethereum` — switches to Base Mainnet `chainId: 0x2105` / `8453`) and pay `$0.50+` USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`) to merchant wallet `0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF`, **or** call `POST /api/credits/topup` with `{"tx_hash": "0x..."}`.
3. Copy your minted `souq_live_...` API key and export `SOUQ_API_KEY` (zero per-call gas).

### B. Polar.sh Credit Pack Checkout (`GET /api/products`)
1. Inspect live product readiness via `GET /api/products` (items with `"ready": true` can be checked out; `"ready": false` items are disabled while fulfillment/checkout IDs are configuring).
2. Create checkout via `POST /api/checkout/create` with `{"sku": "api_credit_pack_5"}`.
3. After payment, Polar redirects back to `/?checkout=success&claim=...`, where the storefront (or `GET /api/checkout/claim?claim=...`) exchanges the one-time token for your `souq_live_...` key.

### C. Autonomous Per-Call HTTP `402` Settlement (`x402-v1.0`)
Send a Base L2 USDC transfer for the exact tool price to `0x71C8F7E4E98a9667793d5B52b71C8A36e65F79bF` and pass `X-Payment-Tx: 0x<tx_hash>` (or `SOUQ_AGENT_PRIVATE_KEY` in `SouqClient` / `SOUQ_PAYMENT_TX` env var).

---

## 4. Tools Exposed Inside Your IDE (`16` Paid + `1` Free)

- **Free Discovery (`$0.00`):** `souq_account_status`
- **Optimization & Code Intel:** `token_context_compressor` (`$0.01`), `ast_structural_slicer` (`$0.02`), `synthetic_schema_verifier` (`$0.01`), `dev_api_cheatsheet_vault` (`$0.01`), `daily_tech_ai_trends_radar` (`$0.01`)
- **Cyber Defense & Security (`Sayf`):** `prompt_injection_firewall` (`$0.01`), `secret_leak_scanner` (`$0.01`), `api_attack_surface_scanner` (`$0.02`), `ast_security_scanner` (`$0.03`), `deep_ast_vulnerability_auditor` (`$0.03`), `smart_contract_honeypot_radar` (`$0.03`)
- **Market Quant & Prediction Arbitrage:** `quant_microstructure_radar` (`$0.02`), `orderbook_slippage_simulator` (`$0.02`), `cross_exchange_arbitrage_scanner` (`$0.03`), `smart_money_whale_flow_radar` (`$0.03`), `prediction_market_arbitrage_radar` (`$0.03`)

---

## 5. REST Endpoints Reference

- `GET /api/catalog` — Tool economics, recipient wallet, Polar summary
- `GET /api/products` — Polar SKUs + `ready` booleans + USDC wallet
- `POST /api/tools/call` — Execute any of the 16 tools
- `POST /api/credits/topup` / `GET /api/credits/balance` — Credit minting & balance
- `POST /api/checkout/create` / `GET /api/checkout/claim` — Polar checkout & one-time claim
- `GET /api/cyber/threat-intel` — Live Cyber Threat Sentinel rule counts
- `GET /api/stats` & `GET /health` — Public aggregate KPIs & health check
- Discovery manifests: `/.well-known/mcp.json`, `/.well-known/agent-card.json`, `/.well-known/agent.json`, `/openapi.json`, `/llms.txt`, `/llms-full.txt`, `/sitemap.xml`, `/robots.txt`
