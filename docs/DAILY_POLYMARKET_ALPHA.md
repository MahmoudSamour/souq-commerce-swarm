# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-22 18:44 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$60,711.15` | Vol: `0.5636` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 45.5% | 29.2% | `-1630.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $58,000 November 16-22? | `one_touch_barrier` | 11.5% | 1.8% | `-965.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $58,000 on November 22? | `european_expiry` | 10.5% | 1.0% | `-950.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 55.5% | 64.0% | `+855.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin dip to $60,000 November 16-22? | `one_touch_barrier` | 62.0% | 54.7% | `-729.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,714.90` | Vol: `0.7015` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 42.5% | 29.0% | `-1354.0` | `BUY_NO_OVERVALUED` |
| Will the price of Ethereum be above $1,300 on November 29? | `european_expiry` | 86.5% | 99.0% | `+1250.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,000 by December 31, 2026? | `one_touch_barrier` | 9.8% | 2.5% | `-737.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 November 16-22? | `one_touch_barrier` | 8.0% | 1.0% | `-700.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 on November 22? | `european_expiry` | 7.5% | 1.0% | `-650.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+9.50` | `-0.0175%` | `-19.13%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+10.37` | `-0.0023%` | `-2.54%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+9.65` | `0.0040%` | `+4.34%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
