#!/bin/bash
# ==============================================================================
# SOUQ // Zero-Cost 1-Click Deployment to Koyeb Free Tier
# Usage: ./deploy_koyeb.sh "your commit message"
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

MSG="${1:-feat(deploy): update SOUQ production edge server for Koyeb}"

echo "🧪 Running pre-flight test suite..."
source .venv/bin/activate
pytest tests/ -q

echo "📦 Staging and committing changes..."
git add -A
git commit -m "$MSG" || echo "Working tree clean, continuing..."

echo "🚀 Pushing to GitHub (origin/main) to trigger Koyeb auto-build..."
git push origin main

echo ""
echo "===================================================================="
echo "🎉 SUCCESS: SOUQ deployment triggered on Koyeb Free Tier!"
echo "   Koyeb auto-builds and deploys the new container in ~60 seconds."
echo "===================================================================="

