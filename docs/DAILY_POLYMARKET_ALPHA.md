# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-19 19:07 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$62,701.19` | Vol: `0.4543` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin dip to $62,000 on November 19? | `european_expiry` | 48.5% | 23.1% | `-2536.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 44.5% | 26.8% | `-1771.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $61,000 on November 19? | `european_expiry` | 19.0% | 3.6% | `-1542.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $150k by December 31, 2027? | `one_touch_barrier` | 20.5% | 5.1% | `-1541.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 37.0% | 22.1% | `-1492.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,772.05` | Vol: `0.6043` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,750 on November 19? | `european_expiry` | 51.5% | 27.1% | `-2443.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,700 on November 19? | `european_expiry` | 13.5% | 2.1% | `-1144.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,700 in November? | `one_touch_barrier` | 65.0% | 72.8% | `+777.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum reach $1,800 in November? | `one_touch_barrier` | 78.0% | 85.2% | `+719.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,250 by December 31, 2026? | `one_touch_barrier` | 17.5% | 10.6% | `-690.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+8.03` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+5.88` | `0.0041%` | `+4.53%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+4.22` | `-0.0022%` | `-2.41%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
