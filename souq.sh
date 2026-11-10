#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Autonomous Multi-Agent Commerce Swarm CLI
# Master Orchestrator (Ra'is Conductor)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate Python 3.11 Virtual Environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️ .venv not detected. Please run python3.11 -m venv .venv && pip install -r requirements.txt"
fi

COMMAND="${1:-help}"

case "$COMMAND" in
    cycle)
        echo "🚀 Running SOUQ Autonomous Conductor Cycle (Ra'is)..."
        python3 -c "
from agents.core.conductor import RaisConductor
import json
conductor = RaisConductor()
report = conductor.run_daily_cycle()
print(json.dumps(report, indent=2))
"
        ;;
    server)
        PORT="${2:-8402}"
        echo "⚡ Launching SOUQ Paid FastMCP Server with x402 Base USDC Gateway on port $PORT..."
        python3 scripts/run_mcp_server.py --port "$PORT"
        ;;
    web)
        PORT="${2:-8080}"
        echo "🌐 Launching SOUQ Web Storefront on http://localhost:$PORT..."
        python3 -m http.server "$PORT" --directory web
        ;;
    tax-report)
        echo "📊 Generating IRS & Koinly-Compliant Crypto Tax Audit Report..."
        python3 scripts/export_tax_receipts.py
        ;;
    telemetry)
        echo "📈 Fetching Live A2A Negotiation & Revenue Telemetry..."
        python3 -c "
from agents.analytics.negotiation_tracker import NegotiationTracker
import json
tracker = NegotiationTracker()
summary = tracker.get_market_intelligence_summary()
print(json.dumps(summary, indent=2))
"
        ;;
    test)
        echo "🧪 Running SOUQ Verification & Settlement Test Suite..."
        pytest tests/
        ;;
    sync)
        echo "🔄 Synchronizing with private GitHub repository..."
        bash scripts/sync_github.sh
        ;;
    help|*)
        echo "===================================================================="
        echo "🏛️  PROJECT SOUQ (السوق) // AUTONOMOUS AGENT COMMERCE SWARM"
        echo "===================================================================="
        echo "Usage: ./souq.sh [command]"
        echo ""
        echo "Commands:"
        echo "  cycle          Execute autonomous discovery, compliance & listing cycle"
        echo "  server [port]  Launch paid FastMCP server with HTTP 402 Base USDC gateway"
        echo "  web [port]     Launch interactive web storefront (default port 8080)"
        echo "  tax-report     Generate Koinly/CoinTracker CSV & JSON receipts"
        echo "  telemetry      Display real-time A2A negotiation & revenue telemetry"
        echo "  test           Execute full unit and integration test suite"
        echo "  sync           Commit and push all changes to private GitHub repo"
        echo "  help           Display this guide"
        echo "===================================================================="
        ;;
esac

