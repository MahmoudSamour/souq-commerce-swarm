# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-20 19:18 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$57,996.00` | Vol: `0.5321` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin dip to $57,000 on November 20? | `european_expiry` | 51.2% | 16.4% | `-3483.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be greater than $72,000 on November 24? | `european_expiry` | 31.2% | 1.0% | `-3025.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $56,000 on November 20? | `european_expiry` | 24.2% | 2.4% | `-2188.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 43.0% | 24.5% | `-1847.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 34.5% | 20.3% | `-1415.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,589.60` | Vol: `0.6552` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,550 on November 20? | `european_expiry` | 48.4% | 12.4% | `-3594.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be above $1,100 on November 27? | `european_expiry` | 75.0% | 99.0% | `+2400.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 41.0% | 23.3% | `-1767.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 26.0% | 10.8% | `-1522.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,500 on November 20? | `european_expiry` | 15.8% | 1.0% | `-1475.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+7.93` | `-0.0119%` | `-13.04%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+6.76` | `-0.0233%` | `-25.46%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+10.93` | `-0.0036%` | `-3.95%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
