# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-21 04:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$56,836.51` | Vol: `0.5704` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 43.0% | 24.7% | `-1826.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $54,000 November 16-22? | `one_touch_barrier` | 37.5% | 23.6% | `-1390.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $52,000 November 16-22? | `one_touch_barrier` | 15.8% | 3.8% | `-1196.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 32.5% | 20.8% | `-1171.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 81.5% | 91.8% | `+1033.0` | `BUY_YES_UNDERVALUED` |

### ETH (Spot: `$1,572.77` | Vol: `0.6687` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 41.0% | 23.1% | `-1788.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 26.5% | 10.8% | `-1565.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 75.8% | 90.3% | `+1451.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum hit $3k by September 30, 2027? | `one_touch_barrier` | 31.0% | 19.7% | `-1126.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,200 in November? | `one_touch_barrier` | 12.4% | 1.7% | `-1079.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+10.92` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+17.72` | `0.0003%` | `+0.34%` | `BASIS_SPREAD_DIVERGENCE` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+20.55` | `0.0100%` | `+10.95%` | `BASIS_SPREAD_DIVERGENCE` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
