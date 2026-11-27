# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-27 20:23 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$59,720.51` | Vol: `0.5183` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin dip to $58,000 November 23-29? | `one_touch_barrier` | 29.5% | 49.2% | `+1967.0` | `BUY_YES_UNDERVALUED` |
| Will the price of Bitcoin be above $52,000 on December 4? | `european_expiry` | 81.0% | 97.3% | `+1629.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin reach $62,000 November 23-29? | `one_touch_barrier` | 20.5% | 36.1% | `+1564.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin dip to $57,500 in November? | `one_touch_barrier` | 32.5% | 45.6% | `+1310.0` | `BUY_YES_UNDERVALUED` |
| Will the price of Bitcoin be above $58,000 on November 29? | `european_expiry` | 90.3% | 78.2% | `-1218.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,666.04` | Vol: `0.6486` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,600 November 23-29? | `one_touch_barrier` | 29.5% | 45.0% | `+1552.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum hit $4k by December 31, 2027? | `one_touch_barrier` | 25.0% | 11.9% | `-1307.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $6k by December 31, 2027? | `one_touch_barrier` | 14.5% | 3.1% | `-1139.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 in November? | `one_touch_barrier` | 42.0% | 53.2% | `+1117.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 55.1% | 65.3% | `+1022.0` | `BUY_YES_UNDERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `coinbase_exchange+hyperliquid` | `+7.62` | `0.0029%` | `+3.18%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `coinbase_exchange+hyperliquid` | `+6.96` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `coinbase_exchange+hyperliquid` | `+7.64` | `0.0046%` | `+5.03%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
