#!/usr/bin/env python3
"""
SOUQ // Tax & Audit Exporter CLI Script
Generates Koinly CSV, CoinTracker, and JSON audit files for real (non-simulated) crypto earnings.
"""

import argparse
import os
import sys

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich.console import Console
from rich.table import Table

from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine

console = Console()


def main() -> int:
    default_db = os.getenv("SOUQ_DB_PATH") or os.getenv("SOUQ_DUCKDB_PATH") or "data/souq_treasury_lake.duckdb"
    default_output = os.getenv("SOUQ_EXPORT_DIR") or "data/exports"
    default_receipts = os.getenv("SOUQ_RECEIPTS_DIR") or "data/receipts"

    parser = argparse.ArgumentParser(description="Export real non-simulated SOUQ crypto receipts for tax & audit.")
    parser.add_argument(
        "--db-path",
        default=default_db,
        help="DuckDB file path or PostgreSQL DSN (default: SOUQ_DB_PATH or data/souq_treasury_lake.duckdb)",
    )
    parser.add_argument(
        "--output-dir",
        default=default_output,
        help="Directory for exported Koinly CSV and audit JSON files (default: SOUQ_EXPORT_DIR or data/exports)",
    )
    parser.add_argument(
        "--receipts-dir",
        default=default_receipts,
        help="Directory containing signed receipt JSON artifacts (default: SOUQ_RECEIPTS_DIR or data/receipts)",
    )
    args = parser.parse_args()

    console.print("\n[bold cyan]SOUQ // Cryptographic Tax & Audit Exporter[/bold cyan]")
    console.print(f"[dim]DB Target :[/dim] {args.db_path}")
    console.print(f"[dim]Output Dir:[/dim] {args.output_dir}")

    engine = CryptoReceiptEngine(db_path=args.db_path, receipts_dir=args.receipts_dir)
    result = engine.export_tax_ledger(output_dir=args.output_dir)

    table = Table(title="Generated Audit Artifacts", show_header=True, header_style="bold magenta")
    table.add_column("Artifact Type", style="dim")
    table.add_column("File Path", style="green")
    table.add_column("Format Standard")

    table.add_row("Koinly CSV Report", result["csv_report"], "Koinly / CoinTracker / IRS-8949")
    table.add_row("Cryptographic JSON Lake", result["json_report"], "SHA-256 Verifiable Signatures")

    console.print(table)
    console.print(f"[bold green]Total Real Receipts Exported: {result['total_records']}[/bold green]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
