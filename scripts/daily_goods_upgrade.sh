#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Autonomous Update Team Lead & Specialist Agent Squad Pipeline
# Directed by: Ra'is Conductor (رئيس التحديث والعمليات)
# Squad Specialists:
# 1. Sayf (سيف - الحارس السيبراني): Dynamic Cyber Threat Intelligence Sentinel
# 2. Kashif (المستكشف): Daily AI & Tech Trends Radar
# 3. Riyadi (الرياضي): Prediction Market Arbitrage & Microstructure Engine
# 4. Buhuth (البحوث): Autonomous Market Research & AEO Directives
# 5. Amin (الأمين): Zero-Risk Compliance & Legal Clearance
# 6. Munadi (المنادي): Global Discovery & IndexNow Search Broadcast
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
echo "⚡ SOUQ AUTONOMOUS UPDATE TEAM LEAD PIPELINE STARTED AT: $TIMESTAMP"
echo "===================================================================="

python3 -c "
import sys
import json
from agents.core.conductor import AutonomousUpdateTeamLead

print('👑 [Team Lead: Ra\'is] Coordinating Autonomous Specialist Agent Squad...')
lead = AutonomousUpdateTeamLead()
squad = lead.team_squad

print(f'   Registered Specialists: {len(squad)} autonomous agents')
for code, agent_info in squad.items():
    print(f'   * {agent_info[\"name\"]}: {agent_info[\"role\"]}')

print('\n🛡️ [Squad Agent: Sayf] Updating Dynamic Cybersecurity Threat Signatures...')
report = lead.run_daily_cycle(broadcast_search=True)
cyber = report.get('cybersecurity_intelligence', {})
print(f'   ✅ Cyber Sentinel Status: {cyber.get(\"status\")}')
print(f'   ✅ Active Threat Rules Loaded: {cyber.get(\"total_threat_rules\")} signatures (v{cyber.get(\"version\")})')
print(f'      - Prompt Injection Rules: {cyber.get(\"prompt_injection_rules\")}')
print(f'      - Smart Contract Honeypot Traps: {cyber.get(\"honeypot_rules\")}')
print(f'      - High-Entropy Secret Leak Rules: {cyber.get(\"secret_leak_rules\")}')

print('\n🔄 [Squad Agent: Kashif] Daily AI & Developer Tech Trends Refreshed:')
tech = report.get('tech_ai_trends', {})
print(f'   ✅ Tech Digest Date: {tech.get(\"digest_date\")} | Trending Repos: {tech.get(\"total_trending_topics\")}')

print('\n📈 [Squad Agent: Riyadi] Prediction Market Probability Arbitrage Warmed:')
arb = report.get('prediction_arbitrage', {})
print(f'   ✅ Analyzed {arb.get(\"markets_analyzed\")} prediction markets | Benchmark BTC: \${arb.get(\"benchmark_spot\")}')

print('\n🏛️ [Squad Agent: Amin & Buhuth] Compliance Clearance & Market Research Review:')
directive = report.get('market_research', {}).get('market_directive', {})
print(f'   ✅ Cleared & Active Catalog: {len(report.get(\"active_catalog\", []))} goods')
print(f'   📊 Strategic Market Verdict: {directive.get(\"strategic_verdict\", \"N/A\")}')
print(f'   🎯 Prioritized Production Tools: {directive.get(\"prioritized_tools\", [])}')
print(f'   🔍 AEO Search Targets: {len(directive.get(\"aeo_target_keywords\", []))} queries')

print('\n📡 [Squad Agent: Munadi] Discovery Endpoints & Global Search Broadcast:')
herald = report.get('herald_distribution', {})
print(f'   ✅ Discovery Endpoints Health: {herald.get(\"endpoints_health\")}')
index_res = herald.get('indexnow', {})
print(f'   ✅ IndexNow Search Broadcast: HTTP {index_res.get(\"status\")} ({index_res.get(\"urls_submitted\")} machine URLs submitted)')
"

echo ""
echo "📄 [Track 2 Pure-Text Feed] Updating docs/DAILY_POLYMARKET_ALPHA.md..."
if ! python3 "$DIR/scripts/generate_daily_alpha_md.py"; then
    echo "⚠️ Alpha feed generation failed — auto-corrector retrying in 3s..."
    sleep 3
    python3 "$DIR/scripts/generate_daily_alpha_md.py" || echo "⚠️ Alpha feed retry failed; continuing with existing docs."
fi

if [ -s "$DIR/docs/DAILY_POLYMARKET_ALPHA.md" ]; then
    echo "✅ Pure-text alpha feed verified: $(wc -c < "$DIR/docs/DAILY_POLYMARKET_ALPHA.md") bytes"
fi

echo ""
echo "🔄 [GitHub Sync] Pushing pure-text feeds & swarm state to origin/main..."
if ! bash "$DIR/scripts/sync_github.sh"; then
    echo "⚠️ sync_github.sh failed — auto-corrector attempting fast IPv4 git pull --rebase & push..."
    (GIT_TERMINAL_PROMPT=0 timeout -k 5 30 git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=15 pull -4 --rebase origin main && \
     GIT_TERMINAL_PROMPT=0 timeout -k 5 30 git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=15 push -4 origin main) || \
     echo "⚠️ GitHub sync deferred to next cycle."
fi

echo "===================================================================="
echo "🎉 SOUQ AUTONOMOUS UPDATE TEAM LEAD PIPELINE COMPLETED AT: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "===================================================================="
