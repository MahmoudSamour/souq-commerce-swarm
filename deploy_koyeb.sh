#!/usr/bin/env bash
# ==============================================================================
# SOUQ // Safe Pre-Flight Deployment Guard for Koyeb
# Usage: ./deploy_koyeb.sh [--dry-run] [--confirm-clean] [-m "commit msg"]
#
# Never uses blind `git add -A`. Refuses deployment if secrets or unstaged
# dirty files exist unless `--confirm-clean` is explicitly passed after review.
# ==============================================================================
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTEST_BIN="${DIR}/.venv/bin/pytest"
if [ ! -x "$PYTEST_BIN" ]; then
    PYTEST_BIN="pytest"
fi

DRY_RUN=0
CONFIRM_CLEAN=0
MSG="feat(deploy): update SOUQ production edge server for Koyeb"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --confirm-clean)
            CONFIRM_CLEAN=1
            shift
            ;;
        -m|--message)
            if [ -z "${2:-}" ]; then
                echo "Error: --message requires a value." >&2
                exit 2
            fi
            MSG="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./deploy_koyeb.sh [--dry-run] [--confirm-clean] [-m \"commit message\"]"
            exit 0
            ;;
        *)
            MSG="$1"
            shift
            ;;
    esac
done

echo "Checking repository for accidental secret files..."
SECRET_MATCHES="$(git status --short --untracked-files=all | awk '{print $NF}' | grep -E '(^|/)(\.env(\..*)?|\.koyeb_token_backup|.*\.(key|pem|token|secret))$' | grep -vE '\.env\.example$' || true)"
if [ -n "$SECRET_MATCHES" ]; then
    echo "ABORT: Potential secret or credential files detected in git status:" >&2
    echo "$SECRET_MATCHES" >&2
    exit 1
fi

DIRTY_STATUS="$(git status --short)"
if [ -n "$DIRTY_STATUS" ] && [ "$CONFIRM_CLEAN" -ne 1 ]; then
    echo "ABORT: Working tree has uncommitted or unstaged changes." >&2
    echo "Review and stage intended commits explicitly, or pass --confirm-clean:" >&2
    echo "$DIRTY_STATUS" >&2
    exit 1
fi

echo "Running pre-flight test suite (${PYTEST_BIN})..."
"$PYTEST_BIN" tests/ -q

if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY RUN COMPLETE: Secret guard, git status check, and pytest passed. Skipping git push."
    exit 0
fi

UNPUSHED="$(git status --short)"
if [ -n "$UNPUSHED" ]; then
    echo "ABORT: Please commit your reviewed changes cleanly before pushing (git add -A is intentionally disabled)." >&2
    echo "$UNPUSHED" >&2
    exit 1
fi

echo "Pushing reviewed HEAD commit ('${MSG}') to origin/main..."
git push origin main

echo ""
echo "===================================================================="
echo "SUCCESS: SOUQ deployment pushed cleanly to origin/main!"
echo "===================================================================="
