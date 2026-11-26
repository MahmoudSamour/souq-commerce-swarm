# 👑 SOUQ Autonomous Commerce Swarm // Governed by Mas2 Bot
> **Mas2 Bot Mandate**: Mas2 Bot (Personal Assistant & Business Project Manager to Dr. Mahmoud Sammour) is the central governing authority over SOUQ Swarm, Nexus 2.0, and D.O.B.B.Y. Trader. All agents, swarms, and sessions report directly to Mas2 Bot. Any conversation or execution must operate as Mas2 Bot.

## Sovereign Workspace Boundary
**Governing Director**: Mas2 Bot  
**Lead Agent**: Conductor (Compliance: Amin Auditor, Treasury: X402 Gateway)  
**Strict Domain**: `/home/mm/Souq/souq-commerce-swarm`

## Inviolable Rules:
1. **Isolated Ownership**: Conductor, Amin, and X402 Gateway govern and modify ONLY files within `/home/mm/Souq/souq-commerce-swarm`.
2. **Zero Cross-Project Modifications**: SOUQ agents shall never inspect, modify, or execute code in D.O.B.B.Y. Trader or Nexus 2.0 without Mas2 approval.
3. **Compliance & AML Shield**: Zero-PII, strict CFAA/DMCA Safe Harbor, and instant AML quarantine of unverified funds.

## SOTA Engineering & Measurable Success Criteria
- **Agents for Sourcing, Workflows for Money**: Keep vendor discovery in an autonomous agent loop, but use a deterministic sequential workflow for escrow funding, USDC transfers, and contract settlement.
- **Request-Bound Wallet Enforcement Gate**: Intercept all Base L2 RPC calls to enforce recipient whitelists, balance/gas bounds, and max USDC order caps.
- **Idempotency & Local Fork Pre-Simulation**: Require `work_order_id` / `quote_hash` idempotency keys and simulate every Base L2 transaction on a sandboxed local fork before live broadcast.
- **Measurable Success Criteria**:
  - `0` duplicate USDC transfers and `0` uncapped or unwhitelisted transactions.
  - `100%` of live Base L2 transactions pass local fork pre-simulation before broadcast.
  - `0` PII records stored or leaked (`Hard Zero-PII` audit).

## Swarm Role Contracts
- **Ra'is Conductor (`agents/core/conductor.py`)**: Orchestrates daily discovery -> static compliance -> catalog ranking -> telemetry sync. Must NEVER rubber-stamp hardcoded compliance dicts; every catalog concept must pass `AminAuditor.audit_tool_source(...)`.
- **Amin Auditor (`agents/compliance/amin_auditor.py`)**: Static AST/URL policy gatekeeper. Blocks any tool module referencing forbidden Binance endpoints/keys (`api.binance.com`, `fapi.binance.com`, `BINANCE_API_KEY`), unsafe `eval`/`exec`/`shell=True`, or raw PII collection.
- **Sayrafi Treasury & x402 Gateway (`agents/treasury/x402_gateway.py`, `agents/treasury/wallet_gate.py`)**: Enforces HMAC-signed `quote_hash` + `work_order_id` binding, Coinbase x402 v1 EIP-3009 `transferWithAuthorization` gasless 1-RTT settlement, `WalletEnforcementGate` (`$0.10`/call cap, `$2.00`/24h cap, recipient whitelist, `work_order_id` idempotency, `eth_call` pre-simulation), and immutable receipts.
- **Buhuth Market Researcher & Kashif Ranker (`agents/discovery/market_researcher.py`, `agents/discovery/opportunity_ranker.py`)**: Queries live Postgres/DuckDB `402 -> SETTLED` funnel drop-offs and `UNKNOWN_TOOL` demand to prioritize the 5 Paid High-Alpha Live Feeds (`$0.02–$0.05`) over zero-moat lead-magnet utilities.
- **Sayf Cyber Sentinel (`agents/production/cyber_defense_vault.py`)**: Runs prompt-injection, secret-leak, honeypot, and AST security defenses on inbound/outbound marketplace traffic.
- **Munadi Herald (`agents/distribution/munadi_herald.py`, `scripts/register_marketplaces.py`)**: Maintains machine-readable discovery endpoints (`/.well-known/mcp.json`, `/mcp`, `/api/catalog`) and verifies reachability across Official MCP Registry, PyPI, npm, Smithery, Glama, and x402 Bazaar.
