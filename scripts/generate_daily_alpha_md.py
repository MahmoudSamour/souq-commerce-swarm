#!/usr/bin/env python3
"""
Generates docs/DAILY_POLYMARKET_ALPHA.md with live Polymarket vs Deribit DVOL
mispricing signals and cross-exchange spot/perp funding APRs.
Intended to run daily via GitHub Actions ($0 automated SEO/alpha funnel).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.production.mcp_tool_builder import (
    CrossExchangeArbitrageScanner,
    PredictionMarketArbitrageRadar,
)

OUT_PATH = REPO_ROOT / "docs" / "DAILY_POLYMARKET_ALPHA.md"
EDGE_URL = "https://written-emera-arapython-bf7436a4.apps.mistral.run"


def generate_markdown() -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pred = PredictionMarketArbitrageRadar()
    arb = CrossExchangeArbitrageScanner()

    lines = [
        "# Daily Live Polymarket & Crypto Funding Alpha Snapshot",
        "",
        f"> **Auto-updated:** `{now_str}` via [`souq-mcp`]({EDGE_URL}/#playground) (5 free calls/day, no signup).",
        "> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](" + EDGE_URL + "/#playground).",
        "",
        "## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies",
        "",
    ]

    for asset in ("BTC", "ETH"):
        res = pred.scan_prediction_arbitrage(asset=asset, limit=5)
        if res.get("status") != "success":
            lines.append(f"### {asset} — Feed temporarily unavailable (`{res.get('error', 'unknown')}`)")
            lines.append("")
            continue

        lines.append(
            f"### {asset} (Spot: `${res.get('benchmark_spot_price', 0):,.2f}` | "
            f"Vol: `{res.get('annualized_vol_used')}` via `{res.get('vol_source')}`)"
        )
        lines.append("")
        opps = res.get("market_discrepancies") or []
        if not opps:
            lines.append("_No active binary strike markets matched filters today._")
            lines.append("")
            continue

        lines.append("| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |")
        lines.append("|---|---|---|---|---|---|")
        for o in opps:
            title = str(o.get("market_title", "")).replace("|", "/")[:80]
            ctype = str(o.get("contract_type", ""))
            poly_p = f"{float(o.get('polymarket_consensus_prob', 0)) * 100:.1f}%"
            mod_p = f"{float(o.get('spot_implied_prob', 0)) * 100:.1f}%"
            edge = o.get("arbitrage_edge_bps", 0)
            sig = o.get("signal", "")
            lines.append(f"| {title} | `{ctype}` | {poly_p} | {mod_p} | `{edge:+.1f}` | `{sig}` |")
        lines.append("")

    lines.extend([
        "## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR",
        "",
        "| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |",
        "|---|---|---|---|---|---|",
    ])

    for sym in ("BTC/USDT", "ETH/USDT", "SOL/USDT"):
        res = arb.scan_arbitrage_and_funding(sym)
        if res.get("status") != "success":
            lines.append(f"| `{sym}` | unavailable | - | - | - | `UPSTREAM_UNAVAILABLE` |")
            continue
        m = res.get("arbitrage_metrics") or {}
        src = str(res.get("data_source", "")).replace("live:", "")
        lines.append(
            f"| `{sym}` | `{src}` | `{m.get('basis_spread_bps', 0):+.2f}` | "
            f"`{m.get('funding_rate_8h_pct', 0):.4f}%` | "
            f"`{m.get('annualized_funding_apr_pct', 0):+.2f}%` | `{m.get('regime_verdict', '')}` |"
        )

    lines.extend([
        "",
        "---",
        "",
        f"- **Test 5 free calls/day:** [{EDGE_URL}/#playground]({EDGE_URL}/#playground)",
        f"- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [{EDGE_URL}/#topup]({EDGE_URL}/#topup)",
        "- **MCP Quickstart:** `npx -y souq-mcp`",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    md = generate_markdown()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(md)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
