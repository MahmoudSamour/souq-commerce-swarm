#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Autonomous Commerce Swarm: Ubuntu Linux Setup & Migration Restore
# Target Machine: Ubuntu Laptop / Desktop (x86_64 / Debian Linux)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "===================================================================="
echo "🚀 SOUQ AUTONOMOUS COMMERCE SWARM: UBUNTU ENVIRONMENT SETUP"
echo "📂 Working Directory: $DIR"
echo "===================================================================="

# 1. System Packages via apt
if command -v apt-get &> /dev/null; then
    if sudo -n true 2>/dev/null; then
        echo "📦 Checking and installing system dependencies via apt..."
        sudo apt-get update -y
        sudo apt-get install -y python3 python3-pip python3-venv curl build-essential git
    else
        echo "ℹ️  Passwordless sudo not available; using existing system packages."
    fi
fi

# 2. Virtual Environment
if [ ! -d ".venv" ]; then
    echo "🐍 Creating clean Python 3.11 virtual environment..."
    python3.11 -m venv .venv || python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip setuptools wheel

# 3. Restore Migration Bundle (Databases, .env credentials, Receipts)
if [ -f "souq_migration_bundle.tar.gz" ]; then
    echo "📦 Unpacking souq_migration_bundle.tar.gz..."
    tar -zxvf souq_migration_bundle.tar.gz
    echo "✅ Databases, .env, and receipts restored successfully."
fi

# 4. Restore Koyeb CLI & Authentication Token
if [ -f ".koyeb_token_backup" ]; then
    echo "🔑 Restoring Koyeb CLI authentication..."
    cp .koyeb_token_backup "$HOME/.koyeb.yaml"
    chmod 600 "$HOME/.koyeb.yaml"
    echo "✅ Restored credentials to ~/.koyeb.yaml"
fi

# Install Koyeb CLI if not present
if ! command -v koyeb &> /dev/null; then
    echo "⚡ Installing Koyeb CLI for Ubuntu Linux..."
    curl -fsSL https://raw.githubusercontent.com/koyeb/koyeb-cli/master/install.sh | sh || true
    if [ -f "$HOME/.koyeb/bin/koyeb" ]; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$HOME/.koyeb/bin/koyeb" "$HOME/.local/bin/koyeb" || true
        if sudo -n true 2>/dev/null; then
            sudo ln -sf "$HOME/.koyeb/bin/koyeb" /usr/local/bin/koyeb || true
        fi
    fi
fi

# 5. Install Python Project Dependencies
echo "📥 Installing SOUQ Python dependencies..."
pip install -r requirements.txt

# 6. Verify System Health & Run Verification Probes
echo "🧪 Running full system verification probe on Ubuntu..."
pytest tests/ -q
python3 scripts/verify_full_system.py

echo ""
echo "===================================================================="
echo "🎉 SOUQ COMMERCE SWARM MIGRATION TO UBUNTU COMPLETE!"
echo "🏛️  ONLINE SHOP STATUS: Cloud server on Koyeb is running 24/7."
echo "🤖 Background Daemon Command: ./souq.sh daemon"
echo "===================================================================="
