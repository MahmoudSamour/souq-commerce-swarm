# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-22 04:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$59,367.42` | Vol: `0.5861` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 44.0% | 28.4% | `-1564.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 61.5% | 74.8% | `+1325.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin dip to $40,000 by December 31, 2026? | `one_touch_barrier` | 14.6% | 5.0% | `-968.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 33.5% | 24.6% | `-894.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $56,000 November 16-22? | `one_touch_barrier` | 14.5% | 6.4% | `-814.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,661.77` | Vol: `0.7053` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 40.5% | 27.2% | `-1334.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 26.5% | 13.7% | `-1279.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $6k by December 31, 2027? | `one_touch_barrier` | 14.5% | 4.2% | `-1029.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 63.3% | 73.2% | `+983.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,000 by December 31, 2026? | `one_touch_barrier` | 13.2% | 3.8% | `-943.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+14.92` | `-0.0021%` | `-2.35%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+14.69` | `0.0020%` | `+2.19%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+15.11` | `-0.0089%` | `-9.75%` | `BASIS_SPREAD_DIVERGENCE` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
