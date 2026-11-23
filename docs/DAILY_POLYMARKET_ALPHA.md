# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-23 12:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$61,386.85` | Vol: `0.515` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin dip to $61,000 on November 23? | `european_expiry` | 77.0% | 39.3% | `-3767.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $60,000 on November 23? | `european_expiry` | 37.5% | 15.9% | `-2160.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 43.5% | 28.0% | `-1548.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $59,000 on November 23? | `european_expiry` | 17.0% | 4.1% | `-1289.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 32.5% | 23.7% | `-880.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,724.54` | Vol: `0.6557` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,700 on November 23? | `european_expiry` | 60.5% | 31.4% | `-2909.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 26.0% | 13.6% | `-1245.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,650 on November 23? | `european_expiry` | 16.5% | 6.5% | `-1003.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by September 30, 2027? | `one_touch_barrier` | 18.0% | 10.3% | `-765.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,250 by December 31, 2026? | `one_touch_barrier` | 22.0% | 15.5% | `-652.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+9.14` | `0.0086%` | `+9.36%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+6.18` | `-0.0061%` | `-6.67%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+6.69` | `-0.0146%` | `-16.01%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
