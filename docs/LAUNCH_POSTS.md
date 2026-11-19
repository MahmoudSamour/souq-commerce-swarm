# SOUQ Launch Copy Pack (Ready to Paste)

> Use these after completing `OPS-1` (Neon Postgres), `OPS-2` (Polar Payouts), `OPS-3` (Upload `$39` Boilerplate), and `OPS-4` (1 verified test checkout).

---

## 1. Reddit — `r/Polymarket` & `r/algotrading`
**Title:** I built a free-to-try MCP server that compares live Polymarket crypto odds vs Deribit DVOL Black-Scholes barrier probabilities

**Body:**
I got tired of manually checking whether Polymarket BTC/ETH binary contracts ("Will BTC hit $X by date Y?") were mispriced relative to Deribit DVOL implied volatility.

So I wrapped it into an open MCP tool (`prediction_market_arbitrage_radar`) that works in Claude Desktop, Cursor, or Python:
- Fetches live Polymarket Gamma binary markets
- Pulls live spot across Coinbase / Kraken / Binance Data Vision / Hyperliquid (geo-unblocked failover)
- Pulls Deribit DVOL (falls back to 30d realized vol)
- Distinguishes **one-touch barrier** (`hit`/`reach`) vs **European expiry** (`above`/`below`) contracts and outputs `arbitrage_edge_bps`

**Try it (5 free calls/day, no signup):**
- Live web sandbox: https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground
- Claude/Cursor 1-liner: `npx -y souq-mcp`
- Daily live snapshot (auto-updated): `docs/DAILY_POLYMARKET_ALPHA.md` in the repo

If you run it in a bot loop past the 5 free daily calls, prepaid keys are $5 (~250 calls) via card or Base USDC (`x402`). Happy to hear what edge cases or other venues I should add!

---

## 2. Hacker News (`Show HN`)
**Title:** Show HN: Monetizing an MCP server with Polar.sh cards and Base USDC (HTTP 402) on $0 free tiers

**Body:**
Hi HN — I built SOUQ (`souq-mcp`), a Streamable HTTP MCP server exposing 16 quant, Polymarket Black-Scholes arbitrage, and Base security tools, monetized with both:
1. **Prepaid `X-API-Key` credits** via Polar.sh card checkout (Standard Webhooks HMAC + sealed one-time claim tokens)
2. **Native HTTP 402 (`x402`)** via Base L2 USDC ERC-20 `Transfer` log verification (with anti-replay locking and automatic refunds if an upstream feed fails)

The hardest parts weren't the tools — it was:
- Switching from local DuckDB to pooled Neon Postgres so Koyeb free-tier restarts don't wipe balances
- Handling USD vs USDT quote skew across geo-unblocked exchange APIs
- Making sure buyers are never charged when an upstream exchange times out

You can test 5 free calls/day in the browser sandbox (no wallet or card required): https://written-emera-arapython-bf7436a4.apps.mistral.run/

I also packaged the stripped-down billing/webhook/x402/Postgres starter kit as a $39 boilerplate if anyone wants to skip the payment plumbing on their own MCP server. Curious what HN thinks about dual card + x402 monetization for agent tools.

---

## 3. Reddit — `r/MCP` & `r/ClaudeAI`
**Title:** Dual-rail MCP monetization (Polar.sh Card + Base USDC x402) + 5 free daily calls for Quant & Base Security tools

**Body:**
Most MCP servers are either completely free or require tedious OAuth/subscriptions. I built `souq-mcp` (`npx -y souq-mcp` or remote Streamable HTTP at `https://written-emera-arapython-bf7436a4.apps.mistral.run/mcp`) with:
- **5 free calls/day per IP** so you can test in Claude/Cursor immediately
- **Live tools:** Polymarket vs Deribit DVOL arbitrage, cross-exchange spot/perp funding APR, 100-level orderbook slippage, Base contract honeypot/bytecode radar, and prompt-injection/secret scanners
- **Zero-subscription billing:** $5 prepaid card pack (~250 calls) or per-call Base USDC (`HTTP 402`)

Repo & setup: https://github.com/MahmoudSamour/souq-commerce-swarm
Sandbox: https://written-emera-arapython-bf7436a4.apps.mistral.run/

---

## 4. MCP Directory Submission Blurb (Smithery / Glama / PulseMCP / MCP.so)
- **Name:** `souq-mcp`
- **Remote Streamable HTTP URL:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/mcp`
- **Manifest URL:** `https://written-emera-arapython-bf7436a4.apps.mistral.run/.well-known/mcp.json`
- **Stdio Command:** `npx -y souq-mcp`
- **Short Description:** Live Polymarket vs Deribit DVOL arbitrage, geo-unblocked multi-venue crypto orderbook/funding telemetry, Base contract honeypot radar, and security/token tools. 5 free calls/day + Polar card packs & Base USDC x402.
