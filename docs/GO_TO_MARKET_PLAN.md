# SOUQ Go-To-Market, Target Audience & Reach Plan

**Live Store:** `https://written-emera-arapython-bf7436a4.apps.mistral.run`  
**Packages:** `pip install souq-mcp` (`0.3.0`) | `npx souq-mcp` (`0.3.0`)  
**Payment Rails:** Credit/Debit Cards (Polar.sh `$5` & `$15` API packs) + Base L2 USDC (`x402`)

---

## 1. Who Buys From SOUQ (Target Audience)

### A. Human AI Developers & Startup Teams (Card Payments — Polar.sh)
- **Who they are:** Python/Node developers building AI agents with Claude Desktop, Cursor, Windsurf, LangGraph, CrewAI, or AutoGen.
- **What pain SOUQ solves:**
  1. **Prompt-injection & tool security** (firewalls/scanners so their agents don't get hijacked).
  2. **High LLM token bills** (context compression cuts prompt tokens before sending to OpenAI/Anthropic/Gemini).
  3. **Zero crypto friction:** They can pay **$5** (~250 calls) or **$15** (~900 calls) by **credit card** and get an instant `X-API-Key` without touching a crypto wallet.

### B. Autonomous AI Agents & Machine-to-Machine Swarms (Crypto — Base L2 USDC `x402`)
- **Who they are:** Automated coding/research/trading agents running on AgentKit, Coinbase x402, or MCP auto-discovery.
- **What pain SOUQ solves:** Sub-cent pay-per-call (`$0.002`–`$0.05`) with zero signup, zero monthly subscription, and cryptographic receipts.

---

## 2. Where to Reach Buyers Fast (Action Plan)

### Channel 1: MCP Directories (Highest-Intent Buyers)
Submit `souq-mcp` (`https://written-emera-arapython-bf7436a4.apps.mistral.run/.well-known/mcp.json`) to the top active MCP directories:
1. **Glama.ai:** `https://glama.ai/mcp/servers` (submit repo + `.well-known/mcp.json`)
2. **PulseMCP:** `https://www.pulsemcp.com/` (submit `souq-mcp` PyPI + npm links)
3. **MCP.so:** `https://mcp.so/` (submit server listing)
4. **GitHub `awesome-mcp-servers` PRs:** Open PRs on `punkpeye/awesome-mcp-servers` and `appcypher/awesome-mcp-servers` with 1-line install (`npx souq-mcp` / `pip install souq-mcp`).

### Channel 2: Developer Launch Posts (Immediate Human Traffic)
Publish short, practical "copy-paste 1-line install" demos (no hype, real before/after savings):
1. **Dev.to & Hashnode:** *"Cut LLM prompt tokens & block prompt injection in 1 MCP command (`npx souq-mcp`)"*
2. **Reddit:** `r/LocalLLaMA`, `r/MCP`, `r/LangChain`, `r/AI_Agents` (share the free tool call / $5 card pack).
3. **LinkedIn (Personal + Company Page):** Short demo post showing a real token-compression % + security scan result.
4. **GitHub Repo SEO:** Add clear badges, `npx souq-mcp` quickstart, and "$5 Card Checkout" button at the top of `README.md`.

### Channel 3: Agent Search & A2A Discovery (Already Live)
Verified online (`HTTP 200`):
- `/.well-known/agent-card.json`
- `/.well-known/mcp.json`
- `/llms.txt` & `/llms-full.txt`
- `/openapi.json`, `/sitemap.xml`, `/robots.txt`
- IndexNow pings (`agents/distribution/munadi_herald.py`) to Bing/Yandex/Seznam/Naver.

---

## 3. Next High-Value Revenue Upgrades (Optional)
1. **Build the 2 paused digital downloads** (`Guardrail Eval Suite $79` & `FastMCP Boilerplate $39`) so higher-ticket buyers can purchase them on Polar.
2. **Track conversions:** Monitor Polar orders + `x402` USDC receipts weekly via `PaymentGatewayAgent` (`08:30` & `18:30`).
