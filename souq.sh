#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Autonomous Multi-Agent Commerce Swarm CLI
# Master Orchestrator (Ra'is Conductor)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTHON_BIN="${DIR}/.venv/bin/python"
PYTEST_BIN="${DIR}/.venv/bin/pytest"
UVICORN_BIN="${DIR}/.venv/bin/uvicorn"

if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(command -v python3)"
fi
if [ ! -x "$PYTEST_BIN" ]; then
    PYTEST_BIN="pytest"
fi

COMMAND="${1:-help}"

case "$COMMAND" in
    cycle)
        echo "Launching SOUQ Autonomous Conductor Cycle (Ra'is)..."
        "$PYTHON_BIN" -c "
from agents.core.conductor import RaisConductor
import json
conductor = RaisConductor()
report = conductor.run_daily_cycle()
print(json.dumps(report, indent=2))
"
        ;;
    server|web)
        PORT="${2:-8402}"
        echo "Launching SOUQ FastAPI/Starlette Edge Server (scripts/koyeb_server.py) on port $PORT..."
        if [ -x "$UVICORN_BIN" ]; then
            exec "$UVICORN_BIN" scripts.koyeb_server:app --host 0.0.0.0 --port "$PORT"
        else
            PORT="$PORT" exec "$PYTHON_BIN" scripts/koyeb_server.py
        fi
        ;;
    verify)
        shift || true
        echo "Running isolated SOUQ verification probe..."
        "$PYTHON_BIN" scripts/verify_full_system.py "$@"
        ;;
    tax-report)
        shift || true
        echo "Generating IRS & Koinly-Compliant Crypto Tax Audit Report..."
        "$PYTHON_BIN" scripts/export_tax_receipts.py "$@"
        ;;
    telemetry)
        echo "Fetching Live A2A Negotiation & Revenue Telemetry..."
        "$PYTHON_BIN" -c "
from agents.analytics.negotiation_tracker import NegotiationTracker
import json
tracker = NegotiationTracker()
summary = tracker.get_market_intelligence_summary()
print(json.dumps(summary, indent=2))
"
        ;;
    test)
        shift || true
        echo "Running SOUQ Verification & Settlement Test Suite..."
        "$PYTEST_BIN" tests/ "$@"
        ;;
    sync)
        echo "Synchronizing with private GitHub repository..."
        bash scripts/sync_github.sh
        ;;
    refresh-trends)
        echo "Refreshing Daily Tech & AI Trends Cache..."
        "$PYTHON_BIN" -c "
from agents.production.dev_intelligence_vault import DailyTechTrendsRadar
radar = DailyTechTrendsRadar()
res = radar.refresh_cache_and_get(force_refresh=True)
print('Fresh Daily Digest generated for date:', res['digest_date'])
"
        ;;
    upgrade-goods)
        bash scripts/daily_goods_upgrade.sh
        ;;
    herald)
        echo "Running Munadi Distribution Herald (Endpoint Audit & Registry Manifest)..."
        "$PYTHON_BIN" agents/distribution/munadi_herald.py
        ;;
    daemon)
        INTERVAL_HOURS="${2:-24}"
        echo "Starting SOUQ Autonomous Scheduled Background Daemon (Every $INTERVAL_HOURS hours)..."
        while true; do
            echo "[$(date)] Executing autonomous discovery & cache refresh cycle..."
            "$PYTHON_BIN" -c "
from agents.production.dev_intelligence_vault import DailyTechTrendsRadar
from agents.core.conductor import RaisConductor
DailyTechTrendsRadar().refresh_cache_and_get(force_refresh=True)
RaisConductor().run_daily_cycle()
"
            echo "Sleeping for $INTERVAL_HOURS hours. Press Ctrl+C to stop."
            sleep "$((INTERVAL_HOURS * 3600))"
        done
        ;;
    help|*)
        echo "===================================================================="
        echo "PROJECT SOUQ // AUTONOMOUS AGENT COMMERCE SWARM"
        echo "===================================================================="
        echo "Usage: ./souq.sh [command]"
        echo ""
        echo "Commands:"
        echo "  server [port]  Launch scripts/koyeb_server.py via .venv/bin/uvicorn (default: 8402)"
        echo "  web [port]     Alias for server (serves interactive storefront + /mcp + /api/*)"
        echo "  test [args]    Execute test suite via .venv/bin/pytest"
        echo "  verify [args]  Run isolated system verification probe (scripts/verify_full_system.py)"
        echo "  cycle          Execute autonomous discovery, compliance & listing cycle"
        echo "  tax-report     Generate Koinly/CoinTracker CSV & JSON receipts"
        echo "  telemetry      Display real-time A2A negotiation & revenue telemetry"
        echo "  refresh-trends Manually trigger cache refresh of daily AI & tech signals"
        echo "  upgrade-goods  Execute full daily goods upgrade (radar & catalog cycle)"
        echo "  herald         Audit public discovery endpoints and generate registry info"
        echo "  sync           Commit and push changes via scripts/sync_github.sh"
        echo "  daemon [hours] Run autonomous background cycle daemon (default: every 24h)"
        echo "  help           Display this guide"
        echo "===================================================================="
        ;;
esac
