# Daily Live Polymarket & Crypto Funding Alpha Snapshot

> **Auto-updated:** `2026-11-22 12:00 UTC` via [`souq-mcp`](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground) (5 free calls/day, no signup).
> Run live in Claude/Cursor with `npx -y souq-mcp` or test in the [browser sandbox](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground).

## 1. Polymarket vs Deribit DVOL Black-Scholes Discrepancies

### BTC (Spot: `$61,065.05` | Vol: `0.5543` via `BTC_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Bitcoin hit $100k by December 31, 2027? | `one_touch_barrier` | 45.5% | 29.3% | `-1619.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $40,000 by December 31, 2026? | `one_touch_barrier` | 11.9% | 2.5% | `-950.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $55,000 by December 31, 2026? | `one_touch_barrier` | 53.5% | 61.2% | `+768.0` | `BUY_YES_UNDERVALUED` |
| Will Bitcoin hit $100k by September 30, 2027? | `one_touch_barrier` | 32.5% | 25.3% | `-719.0` | `BUY_NO_OVERVALUED` |
| Will Bitcoin dip to $58,000 on November 22? | `european_expiry` | 8.5% | 1.8% | `-670.0` | `BUY_NO_OVERVALUED` |

### ETH (Spot: `$1,708.81` | Vol: `0.6897` via `ETH_DVOL`)

| Market | Type | Poly Odds | Model Prob | Edge (bps) | Signal |
|---|---|---|---|---|---|
| Will Ethereum hit $3k by December 31, 2027? | `one_touch_barrier` | 42.5% | 28.5% | `-1401.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,400 in November? | `one_touch_barrier` | 16.4% | 6.8% | `-959.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,000 by December 31, 2026? | `one_touch_barrier` | 10.9% | 2.4% | `-859.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum dip to $1,600 on November 22? | `european_expiry` | 8.5% | 1.6% | `-692.0` | `BUY_NO_OVERVALUED` |
| Will Ethereum hit $3k by September 30, 2027? | `one_touch_barrier` | 32.0% | 25.4% | `-659.0` | `BUY_NO_OVERVALUED` |

## 2. Spot vs Perpetual Basis & Delta-Neutral Funding APR

| Pair | Sources | Basis (bps) | 8h Funding | Annualized APR | Regime |
|---|---|---|---|---|---|
| `BTC/USDT` | `binance_vision+hyperliquid` | `+12.51` | `0.0100%` | `+10.95%` | `EQUILIBRIUM_LOW_SPREAD` |
| `ETH/USDT` | `binance_vision+hyperliquid` | `+10.32` | `0.0042%` | `+4.55%` | `EQUILIBRIUM_LOW_SPREAD` |
| `SOL/USDT` | `binance_vision+hyperliquid` | `+10.44` | `0.0035%` | `+3.85%` | `EQUILIBRIUM_LOW_SPREAD` |

---

- **Test 5 free calls/day:** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground](https://written-emera-arapython-bf7436a4.apps.mistral.run/#playground)
- **Prepaid $5 API Key (~250 calls, Card or Base USDC):** [https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup](https://written-emera-arapython-bf7436a4.apps.mistral.run/#topup)
- **MCP Quickstart:** `npx -y souq-mcp`
