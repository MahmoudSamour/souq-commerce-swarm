# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-23 22:57 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$61,182.03` | Vol: `0.5237` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will the price of Bitcoin be above $68,000 on November 30? | `european_expiry` | 23.0% | 6.6% | `-1642.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 43.5% | 28.1% | `-1537.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $60,000 on November 23? | `european_expiry` | 22.5% | 7.8% | `-1470.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be above $66,000 on November 30? | `european_expiry` | 27.0% | 13.8% | `-1318.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 46.5% | 56.8% | `+1027.0` | `BUY_YES_UNDERVALUED` |

### ETH (Spot: `$1,710.53` | Vol: `0.6586` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,700 on November 23? | `european_expiry` | 65.6% | 36.3% | `-2939.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 26.0% | 13.3% | `-1268.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 47.9% | 59.5% | `+1165.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,650 on November 23? | `european_expiry` | 9.8% | 1.9% | `-789.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $4k by September 30, 2027? | `one_touch_barrier` | 18.0% | 10.2% | `-785.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+7.63` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+5.02` | `-0.0103%` | `-11.25%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+0.80` | `-0.0046%` | `-5.08%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
