#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Daily Goods & Autonomous Intelligence Upgrade Job
# Executes daily discovery, compliance, and tech radar refresh
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
echo "⚡ SOUQ DAILY GOODS UPGRADE STARTED AT: $TIMESTAMP"
echo "===================================================================="

python3 -c "
import sys
import json
from agents.production.dev_intelligence_vault import DailyTechTrendsRadar
from agents.core.conductor import RaisConductor

print('🔄 1. Refreshing Daily Tech & AI Goods Cache...')
radar = DailyTechTrendsRadar()
trends = radar.refresh_cache_and_get(force_refresh=True)
print(f'   ✅ Fresh Daily Digest generated for date: {trends[\"digest_date\"]}')

print('🏛️ 2. Executing Autonomous Ra\'is Conductor Cycle...')
conductor = RaisConductor()
report = conductor.run_daily_cycle()
print(f'   ✅ Cycle Status: {report[\"status\"]}')
print(f'   ✅ Active Goods in Catalog: {len(report[\"active_catalog\"])}')
for item in report['active_catalog']:
    print(f'      - [{item[\"concept_id\"]}] {item[\"title\"]} (\${item[\"suggested_price\"]} USD)')
"

echo "===================================================================="
echo "🎉 SOUQ DAILY GOODS UPGRADE COMPLETED AT: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "===================================================================="
