# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-28 04:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$59,968.81` | Vol: `0.5218` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin dip to $58,000 November 23-29? | `one_touch_barrier` | 20.5% | 39.9% | `+1944.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin reach $62,000 November 23-29? | `one_touch_barrier` | 22.5% | 38.6% | `+1610.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin dip to $57,500 in November? | `one_touch_barrier` | 27.5% | 38.6% | `+1110.0` | `BUY_YES_UNDERVALUED` |
| Will the price of Bitcoin be above $58,000 on November 29? | `european_expiry` | 94.2% | 83.5% | `-1076.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin reach $62,500 in November? | `one_touch_barrier` | 27.0% | 37.7% | `+1066.0` | `BUY_YES_UNDERVALUED` |

### ETH (Spot: `$1,664.67` | Vol: `0.6483` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 42.5% | 25.6% | `-1687.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 November 23-29? | `one_touch_barrier` | 26.5% | 42.5% | `+1596.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,600 in November? | `one_touch_barrier` | 38.5% | 51.8% | `+1330.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 25.0% | 11.9% | `-1312.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 53.4% | 65.4% | `+1194.0` | `BUY_YES_UNDERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `coinbase_exchange+hyperliquid` | `+6.87` | `0.0030%` | `+3.25%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `coinbase_exchange+hyperliquid` | `+4.57` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `coinbase_exchange+hyperliquid` | `+3.77` | `-0.0036%` | `-3.89%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
