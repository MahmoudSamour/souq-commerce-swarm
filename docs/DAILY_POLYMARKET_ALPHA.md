# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-27 04:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$61,342.19` | Vol: `0.4953` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 44.0% | 26.9% | `-1715.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $60,000 November 23-29? | `one_touch_barrier` | 52.0% | 63.5% | `+1147.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 33.5% | 22.3% | `-1118.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $150k by December 31, 2027? | `one_touch_barrier` | 16.0% | 5.9% | `-1011.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin hit $150k by September 30, 2027? | `one_touch_barrier` | 12.5% | 3.5% | `-901.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,727.26` | Vol: `0.6441` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 42.5% | 27.9% | `-1461.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum reach $1,800 November 23-29? | `one_touch_barrier` | 37.5% | 46.9% | `+936.0` | `BUY_YES_UNDERVALUED` |
| Will Ethereum dip to $1,250 by December 31, 2026? | `one_touch_barrier` | 20.5% | 12.3% | `-820.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $3k by September 30, 2027? | `one_touch_barrier` | 31.5% | 24.4% | `-709.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum reach $1,800 in November? | `one_touch_barrier` | 45.5% | 52.5% | `+703.0` | `BUY_YES_UNDERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `coinbase_exchange+hyperliquid` | `+11.05` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `coinbase_exchange+hyperliquid` | `+10.65` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `coinbase_exchange+hyperliquid` | `+14.31` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
