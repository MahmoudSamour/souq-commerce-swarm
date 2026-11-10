# 🚀 SOUQ Commerce Swarm // Ubuntu Linux Migration Guide

This document provides complete instructions for the **Antigravity AI Agent** (or human engineer) on the **Ubuntu Laptop** to restore and take over the autonomous commerce swarm.

---

## 🏛️ Online Storefront Status (Important)
> [!IMPORTANT]
> The public online shop, A2A endpoints, and FastMCP registry are hosted in the cloud on **Koyeb** (`written-emera/souq-commerce-swarm`).
> Migrating or stopping local processes on the Mac **never affects or stops the online shop**. It remains live and accepting payments 24/7.

---

## ⚡ 1-Step Setup on Ubuntu Laptop

Open a terminal on your Ubuntu machine in your projects directory:

```bash
# 1. Clone your private repository
git clone https://github.com/MahmoudSamour/souq-commerce-swarm.git
cd souq-commerce-swarm

# 2. Run the automated setup and restore script
bash scripts/setup_ubuntu.sh
```

---

## 📦 What the Setup Script Restores Automatically

1. **Environment & Secrets:** Unpacks `.env` and `config/.env` containing live Binance keys, Base USDC recipient wallet (`0x71C8F7...`), and rate-limiting rules.
2. **Koyeb CLI & Token:** Restores `~/.koyeb.yaml` and links the `koyeb` CLI tool globally.
3. **Treasury Data Lake & Ledger:** Restores DuckDB (`data/souq_treasury_lake.duckdb`), all historical SHA-256 digital receipts (`data/receipts/`), and Koinly tax reports (`data/exports/`).
4. **Daily AI Intelligence Cache:** Restores the latest daily tech trends cache (`data/cache/`).
5. **System Verification:** Installs Python 3.11 virtual environment and runs all 22 automated tests.

---

## 🤖 Instructions for the Ubuntu Antigravity Agent

When you open this workspace on Ubuntu in Antigravity:

1. **Verify Environment:**
   ```bash
   source .venv/bin/activate
   pytest tests/ -q
   ```
2. **Start the Autonomous Background Daemon:**
   ```bash
   ./souq.sh daemon
   ```
   *This automatically runs daily discovery cycles and refreshes the AI/Tech trends cache every 24 hours.*
3. **Inspect Online Store & Koyeb Deployments:**
   ```bash
   koyeb services list
   koyeb services logs d301e5dc --app written-emera --tail
   ```
4. **Generate Tax Reports Anytime:**
   ```bash
   ./souq.sh tax-report
   ```

---
*Created automatically during Mac to Ubuntu handover.*
