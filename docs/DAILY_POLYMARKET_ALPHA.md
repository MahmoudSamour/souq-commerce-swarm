# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-23 04:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$61,250.00` | Vol: `0.5231` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 45.0% | 28.2% | `-1678.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 32.5% | 24.0% | `-854.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $150k by December 31, 2027? | `one_touch_barrier` | 15.0% | 7.0% | `-800.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $40,000 by December 31, 2026? | `one_touch_barrier` | 8.9% | 1.5% | `-740.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $50,000 in November? | `one_touch_barrier` | 8.2% | 1.0% | `-715.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,731.33` | Vol: `0.6801` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 42.5% | 29.1% | `-1342.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,000 by December 31, 2026? | `one_touch_barrier` | 9.0% | 1.7% | `-726.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,250 by December 31, 2026? | `one_touch_barrier` | 22.5% | 16.9% | `-559.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,400 in November? | `one_touch_barrier` | 9.3% | 3.9% | `-545.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum reach $2,200 in November? | `one_touch_barrier` | 6.9% | 1.6% | `-532.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+12.61` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+11.00` | `-0.0015%` | `-1.62%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+13.26` | `-0.0086%` | `-9.41%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
