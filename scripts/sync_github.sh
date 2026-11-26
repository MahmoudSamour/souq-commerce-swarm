#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Autonomous Git Synchronization Daemon
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "🔄 Synchronizing SOUQ codebase with private GitHub repository..."

git add -A
# Prevent OAuth workflow-scope push rejections by restoring/unstaging .github/workflows/
git checkout HEAD -- .github/workflows/ 2>/dev/null || true
git reset HEAD .github/workflows/ 2>/dev/null || true
if git diff-index --quiet HEAD --; then
    echo "✅ Working tree clean, nothing to commit."
else
    TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    git commit -m "chore(swarm): automated telemetry and agent state sync [$TIMESTAMP]"
    echo "📦 Committed local changes."
fi

GIT_TERMINAL_PROMPT=0 timeout -k 5 30 git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=15 pull -4 --rebase -X theirs origin main || { git rebase --abort 2>/dev/null || true; exit 1; }
GIT_TERMINAL_PROMPT=0 timeout -k 5 30 git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=15 push -4 origin main
echo "🚀 Successfully synchronized with origin/main!"

