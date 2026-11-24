# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-24 21:37 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$59,954.01` | Vol: `0.5323` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 43.5% | 26.9% | `-1663.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 33.5% | 22.6% | `-1087.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $59,000 on November 24? | `european_expiry` | 23.5% | 15.2% | `-832.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $150k by December 31, 2027? | `one_touch_barrier` | 14.5% | 6.7% | `-780.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $40,000 by December 31, 2026? | `one_touch_barrier` | 9.8% | 2.0% | `-772.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,681.64` | Vol: `0.6683` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,650 on November 24? | `european_expiry` | 30.5% | 16.7% | `-1383.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 56.7% | 65.3% | `+860.0` | `BUY_YES_UNDERVALUED` |
| Will the price of Ethereum be greater than $2,100 on December 1? | `european_expiry` | 8.2% | 1.0% | `-720.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 in November? | `one_touch_barrier` | 53.5% | 59.5% | `+602.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,000 by December 31, 2026? | `one_touch_barrier` | 7.9% | 1.9% | `-601.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+7.80` | `-0.0076%` | `-8.27%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+8.91` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+8.57` | `-0.0033%` | `-3.60%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
