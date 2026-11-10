"""
SOUQ // Tax & Audit Exporter CLI Script
Generates Koinly CSV, CoinTracker, and JSON audit files for all crypto earnings.
"""

import os
import sys

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from rich.console import Console
from rich.table import Table

console = Console()


def main():
    console.print("\n[bold cyan]📊 SOUQ // Cryptographic Tax & Audit Exporter[/bold cyan]")
    engine = CryptoReceiptEngine()
    result = engine.export_tax_ledger()

    table = Table(title="Generated Audit Artifacts", show_header=True, header_style="bold magenta")
    table.add_column("Artifact Type", style="dim")
    table.add_column("File Path", style="green")
    table.add_column("Format Standard")

    table.add_row("Koinly CSV Report", result["csv_report"], "Koinly / CoinTracker / IRS-8949")
    table.add_row("Cryptographic JSON Lake", result["json_report"], "SHA-256 Verifiable Signatures")

    console.print(table)
    console.print(f"[bold green]✅ Total Receipts Exported: {result['total_records']}[/bold green]\n")


if __name__ == "__main__":
    main()
