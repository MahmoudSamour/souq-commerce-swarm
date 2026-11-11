#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Public Client Release & Publishing Automation (PyPI & npm)
# Releases standalone, zero-secret MCP client libraries to global registries.
# NOTE: The core trading engine and conductor repo remains strictly PRIVATE.
# ==============================================================================
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=== SOUQ Public Client Release Manager ==="

# 1. Build Python Wheel & Sdist
echo "📦 1. Building Python Wheel (souq-mcp)..."
cd "$DIR/clients/python"
"$DIR/.venv/bin/python" -m build
echo "   ✅ Generated:"
ls -lh dist/

# 2. Pack npm Tarball
echo "📦 2. Packaging npm distribution (souq-mcp)..."
cd "$DIR/clients/npm"
npm pack
echo "   ✅ Generated:"
ls -lh souq-mcp-*.tgz

echo ""
echo "=== Publishing Instructions ==="
echo "To publish to PyPI:"
echo "  cd $DIR/clients/python"
echo "  twine upload dist/*"
echo ""
echo "To publish to npm:"
echo "  cd $DIR/clients/npm"
echo "  npm publish --access public"
echo "=========================================="
