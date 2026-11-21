# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-21 12:05 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$58,152.01` | Vol: `0.6032` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will the price of Bitcoin be greater than $68,000 on November 27? | `european_expiry` | 22.4% | 2.2% | `-2018.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 42.5% | 27.5% | `-1501.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be less than $54,000 on November 26? | `european_expiry` | 30.8% | 15.8% | `-1498.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 69.5% | 84.1% | `+1458.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin dip to $55,000 on November 21? | `european_expiry` | 13.0% | 1.8% | `-1121.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,650.82` | Vol: `0.7105` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will the price of Ethereum be greater than $2,100 on November 27? | `european_expiry` | 31.1% | 1.0% | `-3010.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be greater than $2,200 on November 26? | `european_expiry` | 19.9% | 1.0% | `-1885.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be less than $1,300 on November 25? | `european_expiry` | 18.7% | 1.0% | `-1770.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be greater than $2,200 on November 24? | `european_expiry` | 15.9% | 1.0% | `-1490.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 27.5% | 13.6% | `-1386.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+13.78` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+13.41` | `-0.0045%` | `-4.90%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+13.15` | `-0.0101%` | `-11.10%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
