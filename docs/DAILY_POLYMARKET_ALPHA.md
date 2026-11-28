# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-28 19:12 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$59,255.54` | Vol: `0.5373` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin reach $60,000 on November 28? | `one_touch_barrier` | 29.0% | 48.4% | `+1942.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 32.5% | 21.8% | `-1072.0` | `BUY_NO_OVERVALUED` |
| Will the price of Bitcoin be less than $50,000 on December 2? | `european_expiry` | 11.5% | 1.0% | `-1045.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $58,000 November 23-29? | `one_touch_barrier` | 42.5% | 52.9% | `+1038.0` | `BUY_YES_UNDERVALUED` |
| Will the price of Bitcoin be above $68,000 on December 5? | `european_expiry` | 12.5% | 3.0% | `-954.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,644.53` | Vol: `0.6601` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 58.8% | 70.3% | `+1154.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,600 November 23-29? | `one_touch_barrier` | 42.5% | 51.4% | `+889.0` | `BUY_YES_UNDERVALUED` |
| Will the price of Ethereum be above $1,600 on November 29? | `european_expiry` | 88.0% | 79.4% | `-867.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum reach $1,700 November 23-29? | `one_touch_barrier` | 33.5% | 40.9% | `+745.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,600 in November? | `one_touch_barrier` | 55.5% | 62.4% | `+688.0` | `BUY_YES_UNDERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `coinbase_exchange+hyperliquid` | `+2.95` | `-0.0059%` | `-6.46%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `coinbase_exchange+hyperliquid` | `+4.07` | `0.0082%` | `+9.01%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `coinbase_exchange+hyperliquid` | `+3.55` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
