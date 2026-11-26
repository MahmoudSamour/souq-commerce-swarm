# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-26 20:36 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$60,673.95` | Vol: `0.5212` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 44.5% | 27.2% | `-1727.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $58,000 November 23-29? | `one_touch_barrier` | 23.0% | 37.6% | `+1456.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin dip to $60,000 November 23-29? | `one_touch_barrier` | 72.0% | 83.6% | `+1160.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 33.5% | 22.9% | `-1061.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin reach $64,000 November 23-29? | `one_touch_barrier` | 17.5% | 27.8% | `+1027.0` | `BUY_YES_UNDERVALUED` |

### ETH (Spot: `$1,701.96` | Vol: `0.6536` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 42.5% | 27.2% | `-1529.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 November 23-29? | `one_touch_barrier` | 22.5% | 33.6% | `+1111.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,600 in November? | `one_touch_barrier` | 30.5% | 40.2% | `+972.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,500 by December 31, 2026? | `one_touch_barrier` | 49.4% | 58.9% | `+952.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum reach $1,800 November 23-29? | `one_touch_barrier` | 26.5% | 35.8% | `+930.0` | `BUY_YES_UNDERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `coinbase_exchange+hyperliquid` | `+8.25` | `0.0089%` | `+9.71%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `coinbase_exchange+hyperliquid` | `+7.29` | `0.0062%` | `+6.83%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `coinbase_exchange+hyperliquid` | `+8.27` | `0.0078%` | `+8.57%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
