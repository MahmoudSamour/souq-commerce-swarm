#!/usr/bin/env python3
"""
SOUQ // Migration Bundle Creator
Packages all vital databases, live .env credentials, crypto receipts,
tax exports, and Koyeb CLI configurations into a single compressed archive
for migration to Ubuntu Linux laptop.
"""

import os
import shutil
import tarfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_BUNDLE = BASE_DIR / "souq_migration_bundle.tar.gz"

# Copy local Koyeb CLI token to bundle staging
KOYEB_LOCAL_CONFIG = Path.home() / ".koyeb.yaml"
KOYEB_BACKUP = BASE_DIR / ".koyeb_token_backup"

if KOYEB_LOCAL_CONFIG.exists():
    shutil.copy(KOYEB_LOCAL_CONFIG, KOYEB_BACKUP)
    print("🔑 Backed up ~/.koyeb.yaml to .koyeb_token_backup")

BUNDLE_TARGETS = [
    "config/.env",
    ".env",
    ".koyeb_token_backup",
    "data/souq_treasury_lake.duckdb",
    "data/receipts",
    "data/exports",
    "data/cache"
]


def create_bundle():
    print(f"📦 Packaging SOUQ migration assets from {BASE_DIR}...")
    included_count = 0
    missing_count = 0

    with tarfile.open(OUTPUT_BUNDLE, "w:gz") as tar:
        for rel_path in BUNDLE_TARGETS:
            full_path = BASE_DIR / rel_path
            if full_path.exists():
                size = full_path.stat().st_size if full_path.is_file() else "dir"
                print(f"  ✓ Bundling: {rel_path} ({size})")
                tar.add(full_path, arcname=rel_path)
                included_count += 1
            else:
                print(f"  ⚠️ Skipping (not found): {rel_path}")
                missing_count += 1

    size_mb = OUTPUT_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"\n🎉 SOUQ Migration bundle created successfully!")
    print(f"📁 Output Archive: {OUTPUT_BUNDLE.resolve()}")
    print(f"📊 Bundle Size: {size_mb:.2f} MB")
    print(f"📋 Targets Included: {included_count} | Skipped: {missing_count}")


if __name__ == "__main__":
    create_bundle()
