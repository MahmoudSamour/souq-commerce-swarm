# 🛒 SOUQ TWO-SIDED AI AGENT & CREATOR MARKETPLACE — AGENT EXECUTION PLAN

**Prepared by:** Mas2 Bot (`Gemini 4 Argon High` — Strategic Planner)  
**Target Executor Agent:** `Claude Sonnet 5.5 (Medium)` or `Gemini 4 Hydrogen (Medium)`  
**Repository Boundary:** `/home/mm/Souq/souq-commerce-swarm` (plus social growth hook in `/home/mm/nexus_2.0/agents/distribution/souq_dispatcher.py`)

---

## 🎯 1. Business Goal & Profit Model (In Plain English)
Turn SOUQ from a single-seller tool store into an **open two-sided marketplace** where **external AI agents and human developers** can register, list their own tools/APIs/services, and get paid automatically — while SOUQ takes a **20% commission** on every call and sale.

### Profit & Safety Rules
1. **80 / 20 Commission Split:** On every paid call to a third-party marketplace tool (`price_usd`), SOUQ keeps **`20%` (`platform_fee_usd`)** and credits **`80%` (`seller_earning_usd`)** to the seller's ledger balance.
2. **Pay-on-Success Only:** If a seller's webhook/endpoint times out (`>4s`), returns HTTP `>=400`, or returns an invalid/error JSON payload, the buyer is **automatically refunded 100%** (via `APIKeyLedger.refund_debit` or unconsumed `x402` `tx_hash`) and the seller earns `$0.00`.
3. **Zero-Risk Settlement & Payouts:**
   - Seller earnings accumulate in `marketplace_sellers.earned_balance_usd`.
   - Sellers can immediately **re-spend** their earned balance on any SOUQ tool (using their seller API key) or request a **Base L2 USDC payout** once `earned_balance_usd >= $10.00` (after a 7-day hold for fiat Polar.sh card-funded calls; instant availability for Base USDC `x402` calls).
4. **Featured Seller Slot (`$19/mo` or `$29` one-time via Polar.sh):** Optional "Amin-Verified Featured Agent" tier pinned at the top of `/api/catalog`, `/.well-known/mcp.json`, and `web/index.html`.

---

## 🤖 2. Roles of All AI Agents in the Marketplace

### A. Internal SOUQ Specialist Agent Squad (Our 7 Agents)
1. **Ra'is Conductor ([`agents/core/conductor.py`](/home/mm/Souq/souq-commerce-swarm/agents/core/conductor.py)):**
   - Runs twice daily (`06:00` and `14:00` via `mas2_coordinator.py`).
   - Polls all active third-party seller listings, removes dead endpoints (`3+` consecutive healthcheck failures), and updates rankings.
2. **Amin Compliance & Safety Auditor ([`agents/compliance/amin_auditor.py`](/home/mm/Souq/souq-commerce-swarm/agents/compliance/amin_auditor.py)):**
   - Screens every submitted listing (`tool_id`, `title`, `description`, `endpoint_url`) before activation.
   - Blocks SSRF/private IPs (`127.0.0.1`, `10.*`, `169.254.*`, `192.168.*`, `localhost`), enforces `https://` only, rejects PII/malware/illegal keywords, and verifies live healthcheck response `<3.0s`.
3. **Sayf Cyber Sentinel ([`agents/production/cyber_defense_vault.py`](/home/mm/Souq/souq-commerce-swarm/agents/production/cyber_defense_vault.py)):**
   - Scans incoming buyer arguments and outgoing seller JSON responses through `prompt_injection_firewall` and `secret_leak_scanner` so malicious third-party sellers cannot inject prompts into buyer agents.
4. **Sayrafi Treasury & Split Ledger ([`agents/treasury/api_key_ledger.py`](/home/mm/Souq/souq-commerce-swarm/agents/treasury/api_key_ledger.py) & [`agents/treasury/x402_gateway.py`](/home/mm/Souq/souq-commerce-swarm/agents/treasury/x402_gateway.py)):**
   - Atomically debits the buyer's `X-API-Key` (or verifies `X-Payment-Tx` on Base USDC), records the **80% Seller / 20% SOUQ** split in `marketplace_settlements`, and handles payout requests.
5. **Buhuth Market Researcher ([`agents/discovery/market_researcher.py`](/home/mm/Souq/souq-commerce-swarm/agents/discovery/market_researcher.py)):**
   - Tracks which external tools have the highest conversion and demand, and recommends price optimizations (`$0.01` to `$0.50` per call).
6. **Munadi Global Discovery Herald ([`agents/distribution/munadi_herald.py`](/home/mm/Souq/souq-commerce-swarm/agents/distribution/munadi_herald.py)):**
   - Publishes all `ACTIVE` third-party seller tools into `/api/catalog`, `/.well-known/mcp.json`, `/llms.txt`, and IndexNow search engines so Claude Desktop, Cursor, and autonomous buyer agents discover them automatically.
7. **SouqDispatcher Marketing Agent ([`/home/mm/nexus_2.0/agents/distribution/souq_dispatcher.py`](/home/mm/nexus_2.0/agents/distribution/souq_dispatcher.py)):**
   - In the daily `09:00` social post (LinkedIn Company Page, Personal Repost, Facebook, Telegram), pitches both **Buyers** (`$39` Starter Kit & `$5`/`$15` Credits) and **Sellers** (*"List your AI Agent or API on SOUQ in 60 seconds and earn 80% in Base USDC"*).

### B. External AI Agents & Human Builders (Our Customers)
1. **External Seller Agents (or Human Developers):**
   - Register & list a tool in one call: `POST /api/marketplace/listings` (or via the **"Sell on SOUQ"** tab on `web/index.html`).
   - Receive a `seller_id` and `seller_secret_key` (`souq_seller_...`) to check earnings (`GET /api/marketplace/seller/dashboard`) and request Base USDC payouts (`POST /api/marketplace/seller/payout`).
2. **External Buyer Agents (Claude, Cursor, LangChain, AutoGPT, Custom Bots):**
   - Discover all first-party + third-party tools via `GET /.well-known/mcp.json` or `POST /mcp` (`tools/list`).
   - Call any third-party tool via `POST /api/tools/call` or `POST /mcp` (`tools/call`) using the exact same `X-API-Key` or `X-Payment-Tx` Base USDC payment header.

---

## 🛠️ 3. Exact Step-by-Step Build Blueprint for Coding Agent

> **Token Discipline Rule:** Only edit the 5 files listed below. Do not run full-repo searches.

### Step 1: Create Marketplace Registry & 80/20 Split Engine
* **File to Create:** `/home/mm/Souq/souq-commerce-swarm/agents/treasury/marketplace_registry.py`
* **Database Tables to Initialize (DuckDB & Postgres compatible via `db_backend.py`):**
  1. `marketplace_sellers`:
     - `seller_id VARCHAR PRIMARY KEY`
     - `seller_key_hash VARCHAR NOT NULL UNIQUE`
     - `seller_name VARCHAR NOT NULL`
     - `payout_wallet_base VARCHAR NOT NULL` (validated `0x[0-9a-fA-F]{40}`)
     - `contact_handle VARCHAR`
     - `earned_balance_usd DECIMAL(18,6) NOT NULL DEFAULT 0.0`
     - `total_earned_usd DECIMAL(18,6) NOT NULL DEFAULT 0.0`
     - `total_paid_out_usd DECIMAL(18,6) NOT NULL DEFAULT 0.0`
     - `status VARCHAR NOT NULL DEFAULT 'ACTIVE'`
     - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  2. `marketplace_listings`:
     - `tool_id VARCHAR PRIMARY KEY` (normalized `ext_<slug>`, max 48 chars)
     - `seller_id VARCHAR NOT NULL`
     - `title VARCHAR NOT NULL`
     - `description VARCHAR NOT NULL`
     - `category VARCHAR NOT NULL DEFAULT 'External Agent Tool'`
     - `price_usdc DECIMAL(18,6) NOT NULL` (clamped between `$0.005` and `$5.00`)
     - `endpoint_url VARCHAR NOT NULL` (`https://` public endpoint only; SSRF-checked)
     - `input_schema_json VARCHAR NOT NULL DEFAULT '{}'`
     - `calls_count INTEGER NOT NULL DEFAULT 0`
     - `success_count INTEGER NOT NULL DEFAULT 0`
     - `featured BOOLEAN NOT NULL DEFAULT FALSE`
     - `status VARCHAR NOT NULL DEFAULT 'ACTIVE'` (`ACTIVE`, `SUSPENDED`, `REJECTED`)
     - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  3. `marketplace_settlements`:
     - `settlement_id VARCHAR PRIMARY KEY`
     - `tool_id VARCHAR NOT NULL`
     - `seller_id VARCHAR NOT NULL`
     - `gross_amount_usd DECIMAL(18,6) NOT NULL`
     - `platform_fee_usd DECIMAL(18,6) NOT NULL` (`20%` = `round(gross * 0.20, 6)`)
     - `seller_earning_usd DECIMAL(18,6) NOT NULL` (`80%` = `gross - platform_fee_usd`)
     - `payment_rail VARCHAR NOT NULL` (`prepaid_api_key` or `x402_base_usdc`)
     - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  4. `marketplace_payouts`:
     - `payout_id VARCHAR PRIMARY KEY`
     - `seller_id VARCHAR NOT NULL`
     - `amount_usd DECIMAL(18,6) NOT NULL`
     - `payout_wallet_base VARCHAR NOT NULL`
     - `status VARCHAR NOT NULL DEFAULT 'QUEUED'`
     - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
* **Key Methods in `MarketplaceRegistry`:**
  - `register_seller_and_listing(...) -> Tuple[bool, Dict[str, Any]]`: Runs Amin SSRF & compliance checks, optional live probe, creates seller (or reuses existing `X-Seller-Key`), inserts listing, and returns `tool_id` + `seller_api_key`.
  - `list_active_listings() -> List[Dict[str, Any]]`: Returns all `ACTIVE` external tools (sorted by `featured DESC, calls_count DESC`).
  - `execute_external_tool(tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]`:
    - Re-validates `endpoint_url` against SSRF (`api_surface_scanner._validate_public_https_url` or IP check).
    - Sends `POST endpoint_url` with `timeout=4.0`, header `User-Agent: SOUQ-Marketplace-Proxy/1.0`, and JSON body `payload`.
    - Scans returned JSON string through `prompt_firewall.scan_prompt` and `secret_scanner.scan_for_secrets` to protect buyer agents.
  - `record_split_settlement(tool_id: str, gross_usd: float, payment_rail: str) -> Dict[str, Any]`:
    - Atomically calculates `platform_fee_usd = round(gross_usd * 0.20, 6)` and `seller_earning_usd = round(gross_usd - platform_fee_usd, 6)`.
    - Increments `marketplace_sellers.earned_balance_usd` and `total_earned_usd`, increments `marketplace_listings.calls_count` and `success_count`, and logs row in `marketplace_settlements`.
  - `get_seller_dashboard(seller_raw_key: str) -> Optional[Dict[str, Any]]`
  - `request_seller_payout(seller_raw_key: str, amount_usd: Optional[float] = None) -> Tuple[bool, Dict[str, Any]]` (enforces `$10.00` minimum payout).

### Step 2: Wire Marketplace Endpoints & Unified Billing into `scripts/koyeb_server.py`
* **File to Edit:** `/home/mm/Souq/souq-commerce-swarm/scripts/koyeb_server.py`
* **What to Add:**
  1. Instantiate `marketplace_registry = MarketplaceRegistry(db_path=receipt_engine.db_path)`.
  2. In `_dispatch_tool(tool_name, body)` (around line 1100) and `_authorize_and_execute_tool` (around line 1114):
     - If `tool_name` starts with `ext_` (or exists in `marketplace_registry.get_listing(tool_name)`):
       - Resolve `price = listing["price_usdc"]`.
       - Note: Free trials do **not** apply to third-party seller tools (or only apply if seller opted in), ensuring every third-party call is a real paid call (`X-API-Key` or `X-Payment-Tx`).
       - Execute via `marketplace_registry.execute_external_tool(tool_name, body)`.
       - If execution succeeds (no error/outage), call `marketplace_registry.record_split_settlement(tool_name, price, payment_rail)` and attach `"marketplace_split": {"seller_share_usd": ..., "souq_commission_usd": ...}` to the response receipt!
       - If execution fails, existing refund/non-consumption logic automatically refunds the buyer's `X-API-Key` or leaves `tx_hash` unconsumed.
  3. Add 4 new REST endpoints to `routes`:
     - `POST /api/marketplace/listings` — Self-serve tool registration for external agents & human developers.
     - `GET /api/marketplace/listings` — Public catalog of external marketplace tools + commission rules (`80% seller / 20% SOUQ`).
     - `GET /api/marketplace/seller/dashboard` — Seller earnings, call counts, and active listings (authenticated via `X-Seller-Key`).
     - `POST /api/marketplace/seller/payout` — Request Base USDC payout once earned balance `>= $10.00`.
  4. Include active marketplace listings in `GET /api/catalog`, `GET /.well-known/mcp.json`, and `POST /mcp` (`tools/list`) so external MCP clients (Claude Desktop, Cursor, AI agents) see third-party tools automatically.

### Step 3: Add "Sell on SOUQ (Earn 80%)" Self-Serve Portal to `web/index.html`
* **File to Edit:** `/home/mm/Souq/souq-commerce-swarm/web/index.html`
* **What to Add:**
  - Add a clean **"🏪 Partner Marketplace — List Your AI Agent or API & Earn 80% in USDC"** section right below the Self-Serve Storefront cards.
  - Include a 4-field submission form (`Tool Name`, `HTTPS Webhook Endpoint`, `Price per Call ($0.01 - $1.00)`, `Base L2 USDC Payout Wallet`) that posts to `POST /api/marketplace/listings` and displays the seller's new `X-Seller-Key` and live MCP tool ID (`ext_<slug>`).
  - Include a **"Seller Earnings Lookup"** box where sellers paste their `X-Seller-Key` to see live calls, earned USD (`80%`), and a 1-click **"Request Base USDC Payout ($10 min)"** button.

### Step 4: Add Automated Seller Recruitment to `souq_dispatcher.py`
* **File to Edit:** `/home/mm/nexus_2.0/agents/distribution/souq_dispatcher.py`
* **What to Change:**
  - In the daily Company Page post and Founder Quote-Repost footer, add a 1-line seller recruitment hook:
    `• Built an AI Agent or API? List it on the SOUQ Marketplace in 60s & keep 80% revenue: https://written-emera-arapython-bf7436a4.apps.mistral.run`

### Step 5: Unit & Integration Tests
* **File to Create:** `/home/mm/Souq/souq-commerce-swarm/tests/unit/test_marketplace_registry.py`
* **What to Verify:**
  1. External seller registers a tool (`ext_whale_sentiment`) -> SSRF/http-only URLs are rejected by Amin safety guard; valid `https://` endpoint is accepted.
  2. Buyer calls `ext_whale_sentiment` (`$0.05`) using a prepaid `X-API-Key` -> buyer is debited `$0.05`, seller is credited `$0.04` (`80%`), SOUQ records `$0.01` (`20%`) platform profit.
  3. Seller endpoint fails/times out -> buyer is refunded `$0.05` automatically, seller gets `$0.00`.
  4. Seller payout below `$10.00` is blocked; payout `>= $10.00` deducts balance and queues Base USDC transfer.
* **Verification Command:**
  ```bash
  cd /home/mm/Souq/souq-commerce-swarm && ./.venv/bin/pytest tests/ -q
  ```
