# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-25 20:44 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$59,938.00` | Vol: `0.5463` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 43.5% | 27.4% | `-1609.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 54.5% | 66.1% | `+1160.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin reach $61,000 on November 25? | `one_touch_barrier` | 18.2% | 28.9% | `+1075.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 33.5% | 23.3% | `-1023.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $150k by December 31, 2027? | `one_touch_barrier` | 14.5% | 7.2% | `-734.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,682.49` | Vol: `0.6835` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 56.9% | 65.6% | `+876.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,000 by December 31, 2026? | `one_touch_barrier` | 9.3% | 2.0% | `-729.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 in November? | `one_touch_barrier` | 49.5% | 56.5% | `+705.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum reach $1,700 on November 25? | `one_touch_barrier` | 54.5% | 61.4% | `+687.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,250 by December 31, 2026? | `one_touch_barrier` | 25.5% | 19.7% | `-582.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+9.64` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+7.11` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+8.53` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
