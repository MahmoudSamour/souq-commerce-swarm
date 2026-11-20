# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-20 12:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$61,838.01` | Vol: `0.4951` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin dip to $61,000 on November 20? | `european_expiry` | 60.0% | 26.8% | `-3317.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be greater than $72,000 on November 26? | `european_expiry` | 30.4% | 1.0% | `-2940.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be less than $56,000 on November 23? | `european_expiry` | 25.4% | 1.7% | `-2370.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be less than $54,000 on November 26? | `european_expiry` | 24.6% | 1.9% | `-2277.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $60,000 on November 20? | `european_expiry` | 27.5% | 8.5% | `-1904.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,749.69` | Vol: `0.6205` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will the price of Ethereum be greater than $2,200 on November 26? | `european_expiry` | 27.9% | 1.0% | `-2685.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be greater than $2,200 on November 24? | `european_expiry` | 23.2% | 1.0% | `-2220.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be greater than $2,300 on November 23? | `european_expiry` | 21.6% | 1.0% | `-2065.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,700 on November 20? | `european_expiry` | 35.5% | 14.9% | `-2064.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,650 on November 20? | `european_expiry` | 13.0% | 1.7% | `-1135.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+7.23` | `0.0078%` | `+8.58%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+8.88` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+8.18` | `0.0070%` | `+7.66%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
