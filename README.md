# Project SOUQ (السوق) // Autonomous Multi-Agent Commerce Swarm

> **Architecture Lineage:** Inspired by `nexus_2.0` and `Dobby_Trader`  
> **Core Objective:** 100% Autonomous Digital Product Discovery, Synthesis, Distribution, and Settlement  
> **Primary Revenue Rail:** Agent-to-Agent (A2A) Micropayments via **FastMCP + HTTP 402 + Base USDC**  
> **Secondary Revenue Rail:** B2B / Developer Digital Assets via **Polar.sh Merchant of Record**  
> **Audit Readiness:** Cryptographic Receipts & IRS/Koinly Compliant Tax Ledger  

---

## 1. What SOUQ Sells

1. **A2A Paid FastMCP Tool Endpoints** ($0.01 – $0.05 USDC per call):
   * `quant_microstructure_radar`: Real-time Binance order book depth, Order Book Imbalance (OBI), and liquidation risk.
   * `ast_security_scanner`: Static AST security linting detecting eval injections, shell executions, and reentrancy.
   * `synthetic_schema_verifier`: Schema conformity validation for autonomous LLM pipelines.
2. **Machine Learning & Quant Data Lakes** ($49.00 – $99.00 one-time):
   * Cleaned DuckDB and Parquet lakes of 5-year high-frequency market microstructure.
3. **Developer Infrastructure Boilerplates** ($29.00 – $79.00 one-time):
   * Production-ready sovereign multi-agent swarm templates with automated GitHub repository access invitations.

---

## 2. Sovereign Agent Swarm Structure

```
souq_swarm/
├── agents/
│   ├── core/                  # Ra'is (Supreme Executive Conductor)
│   ├── discovery/             # Kashif (Market Demand & Opportunity Scout)
│   ├── production/            # Sani' (FastMCP & Data Synthesizer)
│   ├── treasury/              # Sayrafi (Base USDC x402 Gateway & Crypto Receipts)
│   ├── distribution/          # Munadi (MCP Registry & SEO Growth Herald)
│   ├── compliance/            # Amin (Chief Legal, CFAA & DMCA Auditor)
│   └── analytics/             # Negotiation Tracker & Pricing Intelligence
├── config/
│   ├── settings.yaml          # System orchestration parameters
│   ├── pricing_models.yaml    # Elastic pricing rules
│   └── .env                   # Binance API & Base wallet keys
├── data/
│   ├── souq_treasury_lake.duckdb # Master financial & telemetry ledger
│   ├── receipts/              # Individual signed cryptographic JSON receipts
│   └── exports/               # Koinly/CoinTracker CSV tax exports
├── scripts/
│   ├── run_mcp_server.py      # Live FastMCP server with x402 gateway
│   ├── export_tax_receipts.py # IRS/Koinly tax report generator
│   └── sync_github.sh         # Automated private git sync daemon
└── souq.sh                    # Master CLI orchestrator
```

---

## 3. Quick Start & CLI Usage

```bash
# 1. Run Autonomous Discovery & Listing Cycle
./souq.sh cycle

# 2. Launch Paid FastMCP Server (Port 8402)
./souq.sh server 8402

# 3. Export Cryptographic Tax Receipts (Koinly CSV + JSON)
./souq.sh tax-report

# 4. View Real-Time Agent-to-Agent Negotiation Telemetry
./souq.sh telemetry

# 5. Run Full Verification Test Suite
./souq.sh test

# 6. Synchronize with Private GitHub Repository
./souq.sh sync
```
