# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-21 18:20 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$60,140.33` | Vol: `0.5857` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will the price of Bitcoin be greater than $72,000 on November 26? | `european_expiry` | 22.4% | 1.0% | `-2135.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be above $66,000 on November 28? | `european_expiry` | 29.5% | 11.9% | `-1762.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be above $54,000 on November 28? | `european_expiry` | 74.5% | 90.4% | `+1588.0` | `BUY_YES_UNDERVALUED` |
| Will the price of Bitcoin be above $52,000 on November 28? | `european_expiry` | 80.5% | 96.2% | `+1567.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 44.0% | 29.3% | `-1469.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,682.24` | Vol: `0.714` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will the price of Ethereum be less than $1,300 on November 25? | `european_expiry` | 22.1% | 1.0% | `-2105.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 27.5% | 14.4% | `-1309.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 40.5% | 28.1% | `-1242.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 58.7% | 70.0% | `+1135.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum reach $1,700 November 16-22? | `one_touch_barrier` | 90.5% | 80.0% | `-1045.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+12.28` | `-0.0034%` | `-3.71%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+12.83` | `-0.0054%` | `-5.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+11.45` | `-0.0147%` | `-16.14%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
