#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Daily Autonomous Intelligence, Market Research & AEO Upgrade Pipeline
# Orchestrates:
# 1. Tech & AI Trends Intelligence Synthesis
# 2. Prediction Market Probability Arbitrage Warming
# 3. Autonomous Ra'is Conductor & Buhuth Market Research Review
# 4. Agent Engine Optimization (AEO) Broadcast & IndexNow Search Engine Ping
# ==============================================================================
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

mkdir -p "$DIR/logs"

export PATH="/home/mm/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

if [ -f "$DIR/.venv/bin/activate" ]; then
    source "$DIR/.venv/bin/activate"
else
    echo "❌ Error: Virtual environment at $DIR/.venv not found." >&2
    exit 1
fi

TIMESTAMP="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "===================================================================="
echo "⚡ SOUQ AUTONOMOUS PIPELINE CYCLE STARTED AT: $TIMESTAMP"
echo "===================================================================="

python3 -c "
import sys
import json
from agents.production.dev_intelligence_vault import DailyTechTrendsRadar
from agents.production.mcp_tool_builder import PredictionMarketArbitrageRadar
from agents.core.conductor import RaisConductor
from agents.distribution.munadi_herald import MunadiHerald

print('🔄 [1/4] Refreshing Daily Tech & AI Goods Cache...')
trends_radar = DailyTechTrendsRadar()
trends = trends_radar.refresh_cache_and_get(force_refresh=True)
print(f'   ✅ Fresh Daily Digest generated for date: {trends[\"digest_date\"]}')

print('📈 [2/4] Warming Prediction Market Arbitrage Radar...')
pred_radar = PredictionMarketArbitrageRadar()
arb = pred_radar.scan_prediction_arbitrage('BTC')
print(f'   ✅ Analyzed {arb[\"opportunities_analyzed\"]} prediction markets | Benchmark BTC Spot: \${arb[\"benchmark_spot_price\"]}')

print('🏛️ [3/4] Executing Ra\'is Conductor & Buhuth Market Research Review...')
conductor = RaisConductor()
report = conductor.run_daily_cycle()
market_research = report.get('market_research', {})
directive = market_research.get('market_directive', {})

print(f'   ✅ Conductor Status: {report[\"status\"]}')
print(f'   ✅ Active Cleared Catalog: {len(report[\"active_catalog\"])} goods')
print(f'   📊 Market Research Verdict: {directive.get(\"strategic_verdict\", \"N/A\")}')
print(f'   🎯 Prioritized Tools: {directive.get(\"prioritized_tools\", [])}')
print(f'   🔍 Target AEO Keywords: {len(directive.get(\"aeo_target_keywords\", []))} search queries loaded')

print('📡 [4/4] Executing Agent Engine Optimization (AEO) & IndexNow Broadcast...')
herald = MunadiHerald()
audit = herald.verify_public_discovery_endpoints()
print(f'   ✅ Discovery Endpoint Health: {audit.get(\"overall_status\")}')
index_res = herald.broadcast_to_indexnow()
print(f'   ✅ IndexNow Search Network Ping: HTTP {index_res.get(\"status\")} ({index_res.get(\"urls_submitted\")} machine URLs broadcasted)')
"

echo "===================================================================="
echo "🎉 SOUQ AUTONOMOUS PIPELINE CYCLE COMPLETED AT: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "===================================================================="
