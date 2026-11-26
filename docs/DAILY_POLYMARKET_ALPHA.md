# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-26 04:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$60,716.92` | Vol: `0.5178` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 47.5% | 58.0% | `+1048.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $150k by December 31, 2027? | `one_touch_barrier` | 14.5% | 6.5% | `-802.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $40,000 by December 31, 2026? | `one_touch_barrier` | 8.0% | 1.2% | `-680.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $58,000 November 23-29? | `one_touch_barrier` | 34.5% | 41.1% | `+659.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $150k by September 30, 2027? | `one_touch_barrier` | 10.0% | 4.0% | `-603.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,696.64` | Vol: `0.6553` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 50.8% | 60.5% | `+973.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,600 November 23-29? | `one_touch_barrier` | 33.5% | 41.0% | `+753.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,600 in November? | `one_touch_barrier` | 40.0% | 46.5% | `+647.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,000 by December 31, 2026? | `one_touch_barrier` | 7.6% | 1.3% | `-636.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be above $1,600 on November 29? | `european_expiry` | 87.0% | 81.1% | `-586.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `coinbase_exchange+hyperliquid` | `+14.34` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `coinbase_exchange+hyperliquid` | `+13.73` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `coinbase_exchange+hyperliquid` | `+10.57` | `-0.0042%` | `-4.54%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
