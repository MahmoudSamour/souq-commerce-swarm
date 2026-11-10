#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Autonomous Git Synchronization Daemon
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "🔄 Synchronizing SOUQ codebase with private GitHub repository..."

git add -A
if git diff-index --quiet HEAD --; then
    echo "✅ Working tree clean, nothing to commit."
else
    TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    git commit -m "chore(swarm): automated telemetry and agent state sync [$TIMESTAMP]"
    echo "📦 Committed local changes."
fi

git push origin main
echo "🚀 Successfully synchronized with origin/main!"

