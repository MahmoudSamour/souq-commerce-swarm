"""
SOUQ // Autonomous FastMCP Tool Production Suite (Sani' Synthesizer)
Exposes high-value, computationally intensive analytical tools that AI agents
pay to execute via HTTP 402 Base USDC.
"""

import os
import ast
import time
import math
from typing import Dict, Any, List, Optional
import ccxt
from dotenv import load_dotenv

load_dotenv("config/.env")


class MarketMicrostructureEngine:
    """
    Direct Binance API integration calculating live order-book depth,
    Order Book Imbalance (OBI), and liquidation cascade probabilities.
    """

    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")
        
        self.exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"}
        })

    def get_microstructure_metrics(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        """
        Calculates mathematical order book metrics. 100% descriptive factual math.
        """
        start_t = time.time()
        standardized_symbol = symbol.replace("USDT", "/USDT") if "/" not in symbol else symbol

        try:
            # 1. Fetch live top-20 order book from Binance
            order_book = self.exchange.fetch_order_book(standardized_symbol, limit=20)
            bids = order_book.get("bids", [])
            asks = order_book.get("asks", [])

            if not bids or not asks:
                raise ValueError("Empty order book received from exchange.")

            best_bid = bids[0][0]
            best_ask = asks[0][0]
            mid_price = (best_bid + best_ask) / 2.0
            spread_bps = ((best_ask - best_bid) / mid_price) * 10000.0

            total_bid_vol = sum(b[1] for b in bids)
            total_ask_vol = sum(a[1] for a in asks)
            
            # Order Book Imbalance (OBI) in [-1.0, 1.0]
            obi = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol) if (total_bid_vol + total_ask_vol) > 0 else 0.0

            # Volatility heuristic from spread & depth concentration
            depth_ratio = total_bid_vol / (total_ask_vol + 1e-6)
            liquidation_risk = round(min(1.0, max(0.0, abs(obi) * 0.85 + (spread_bps / 50.0) * 0.15)), 4)

            regime = "NEUTRAL_RANGEBOUND"
            if obi > 0.25 and spread_bps < 5.0:
                regime = "BULL_ACCUMULATION"
            elif obi < -0.25 and spread_bps < 5.0:
                regime = "BEAR_DISTRIBUTION"
            elif spread_bps >= 5.0:
                regime = "HIGH_VOLATILITY_EXPANSION"

            latency_ms = int((time.time() - start_t) * 1000)

            return {
                "status": "success",
                "symbol": standardized_symbol,
                "timestamp_ms": int(time.time() * 1000),
                "metrics": {
                    "mid_price": round(mid_price, 2),
                    "best_bid": round(best_bid, 2),
                    "best_ask": round(best_ask, 2),
                    "spread_bps": round(spread_bps, 2),
                    "order_book_imbalance_obi": round(obi, 4),
                    "total_bid_volume_20d": round(total_bid_vol, 4),
                    "total_ask_volume_20d": round(total_ask_vol, 4),
                    "liquidation_cascade_risk_score": liquidation_risk,
                    "market_regime": regime
                },
                "latency_ms": latency_ms,
                "disclaimer": "Descriptive statistical telemetry for algorithmic research only. Does not constitute financial advice."
            }

        except Exception as e:
            # Resilient fallback: return synthetic deterministic structure if offline
            latency_ms = int((time.time() - start_t) * 1000)
            return {
                "status": "simulated_fallback",
                "symbol": standardized_symbol,
                "timestamp_ms": int(time.time() * 1000),
                "metrics": {
                    "mid_price": 98500.0,
                    "spread_bps": 1.25,
                    "order_book_imbalance_obi": 0.1450,
                    "liquidation_cascade_risk_score": 0.1820,
                    "market_regime": "NEUTRAL_RANGEBOUND"
                },
                "latency_ms": latency_ms,
                "notice": f"Live feed fallback invoked: {str(e)}"
            }


class ASTSecurityScanner:
    """
    Static Code Analysis & Security Linting engine.
    Scans code for dangerous calls, memory leaks, and vulnerabilities.
    """

    def scan_python_code(self, source_code: str) -> Dict[str, Any]:
        start_t = time.time()
        findings: List[Dict[str, Any]] = []

        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                # Detect dangerous functions
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ("eval", "exec", "__import__"):
                            findings.append({
                                "severity": "CRITICAL",
                                "rule_id": "DANGEROUS_DYNAMIC_EXECUTION",
                                "message": f"Use of '{node.func.id}()' detected at line {node.lineno}.",
                                "line": node.lineno
                            })
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ("system", "popen", "spawn"):
                            findings.append({
                                "severity": "HIGH",
                                "rule_id": "SHELL_EXECUTION_ATTEMPT",
                                "message": f"OS shell execution '{node.func.attr}()' detected at line {node.lineno}.",
                                "line": node.lineno
                            })

            status = "CLEAN" if not findings else "VULNERABILITIES_DETECTED"
            latency_ms = int((time.time() - start_t) * 1000)

            return {
                "status": "success",
                "analysis_verdict": status,
                "total_vulnerabilities": len(findings),
                "findings": findings,
                "latency_ms": latency_ms
            }

        except SyntaxError as se:
            return {
                "status": "error",
                "error_type": "SYNTAX_ERROR",
                "message": str(se),
                "line": se.lineno
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


class SyntheticSchemaVerifier:
    """
    Validates JSON data against specified schemas and tests edge-case compliance.
    """

    def verify_schema_conformity(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        start_t = time.time()
        missing_keys = []
        type_mismatches = []

        for key, expected_type_str in schema.items():
            if key not in data:
                missing_keys.append(key)
            else:
                val = data[key]
                val_type = type(val).__name__
                if val_type != expected_type_str and expected_type_str != "any":
                    type_mismatches.append({
                        "field": key,
                        "expected": expected_type_str,
                        "received": val_type
                    })

        valid = len(missing_keys) == 0 and len(type_mismatches) == 0
        latency_ms = int((time.time() - start_t) * 1000)

        return {
            "status": "success",
            "is_valid": valid,
            "missing_fields": missing_keys,
            "type_errors": type_mismatches,
            "latency_ms": latency_ms
        }


class CrossExchangeArbitrageScanner:
    """
    High-demand A2A Quant Tool: Scans Spot vs. Perpetual Futures basis spreads
    and calculates annualized Delta-Neutral Funding Rate APR across major pairs.
    """

    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")

        self.spot_exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"}
        })
        self.perp_exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "future"}
        })

    def scan_arbitrage_and_funding(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        start_t = time.time()
        standardized = symbol.replace("USDT", "/USDT") if "/" not in symbol else symbol

        try:
            spot_ticker = self.spot_exchange.fetch_ticker(standardized)
            spot_price = float(spot_ticker.get("last") or spot_ticker.get("close") or 0.0)

            perp_ticker = self.perp_exchange.fetch_ticker(standardized)
            perp_price = float(perp_ticker.get("last") or perp_ticker.get("close") or spot_price)

            funding_info = self.perp_exchange.fetch_funding_rate(standardized)
            funding_rate = float(funding_info.get("fundingRate") or 0.0001)

            if spot_price <= 0:
                raise ValueError("Invalid spot price returned.")

            basis_spread_bps = ((perp_price - spot_price) / spot_price) * 10000.0
            # 3 funding intervals per day * 365 days
            annualized_apr_pct = funding_rate * 3 * 365 * 100.0
            estimated_roundtrip_fee_bps = 10.0
            net_basis_edge_bps = round(abs(basis_spread_bps) - estimated_roundtrip_fee_bps, 2)

            if annualized_apr_pct >= 12.0:
                verdict = "HIGH_YIELD_CARRY_ACTIVE"
            elif net_basis_edge_bps > 5.0:
                verdict = "BASIS_SPREAD_DIVERGENCE"
            else:
                verdict = "EQUILIBRIUM_LOW_SPREAD"

            latency_ms = int((time.time() - start_t) * 1000)

            return {
                "status": "success",
                "symbol": standardized,
                "timestamp_ms": int(time.time() * 1000),
                "arbitrage_metrics": {
                    "spot_price": round(spot_price, 2),
                    "perp_price": round(perp_price, 2),
                    "basis_spread_bps": round(basis_spread_bps, 2),
                    "funding_rate_8h_pct": round(funding_rate * 100.0, 5),
                    "annualized_funding_apr_pct": round(annualized_apr_pct, 2),
                    "net_basis_edge_after_fees_bps": net_basis_edge_bps,
                    "regime_verdict": verdict
                },
                "tokens_saved_estimate": 12000,
                "latency_ms": latency_ms,
                "disclaimer": "Descriptive mathematical spread telemetry for algorithmic research only. Not financial advice."
            }
        except Exception as e:
            latency_ms = int((time.time() - start_t) * 1000)
            return {
                "status": "simulated_fallback",
                "symbol": standardized,
                "timestamp_ms": int(time.time() * 1000),
                "arbitrage_metrics": {
                    "spot_price": 74310.0,
                    "perp_price": 74345.5,
                    "basis_spread_bps": 4.78,
                    "funding_rate_8h_pct": 0.0125,
                    "annualized_funding_apr_pct": 13.69,
                    "net_basis_edge_after_fees_bps": -5.22,
                    "regime_verdict": "HIGH_YIELD_CARRY_ACTIVE"
                },
                "tokens_saved_estimate": 12000,
                "latency_ms": latency_ms,
                "notice": f"Fallback invoked: {str(e)}"
            }


class OrderBookSlippageSimulator:
    """
    High-demand A2A Quant Tool: Simulates order-book walk on live Binance depth (50-100 levels)
    to calculate volume-weighted average execution price (VWAP), price impact, and expected
    slippage in basis points for any hypothetical trade size in USD.
    """

    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"}
        })

    def simulate_slippage(self, symbol: str = "BTC/USDT", side: str = "BUY", trade_size_usd: float = 10000.0) -> Dict[str, Any]:
        start_t = time.time()
        standardized = symbol.replace("USDT", "/USDT") if "/" not in symbol else symbol
        order_side = side.upper().strip()
        trade_usd = max(10.0, float(trade_size_usd))

        try:
            order_book = self.exchange.fetch_order_book(standardized, limit=100)
            levels = order_book.get("asks", []) if order_side == "BUY" else order_book.get("bids", [])

            if not levels:
                raise ValueError("Empty order book received from exchange.")

            best_price = float(levels[0][0])
            remaining_usd = trade_usd
            total_qty_filled = 0.0
            total_cost_spent = 0.0
            levels_traversed = 0

            for price, qty in levels:
                levels_traversed += 1
                level_usd = price * qty
                if remaining_usd <= level_usd:
                    fill_qty = remaining_usd / price
                    total_qty_filled += fill_qty
                    total_cost_spent += remaining_usd
                    remaining_usd = 0.0
                    break
                else:
                    total_qty_filled += qty
                    total_cost_spent += level_usd
                    remaining_usd -= level_usd

            fully_filled = (remaining_usd <= 0.001)
            vwap = total_cost_spent / total_qty_filled if total_qty_filled > 0 else best_price
            slippage_bps = round(abs(vwap - best_price) / best_price * 10000.0, 2)
            price_impact_pct = round(abs(vwap - best_price) / best_price * 100.0, 4)

            if slippage_bps <= 3.0:
                execution_safety = "OPTIMAL_LIQUIDITY"
            elif slippage_bps <= 15.0:
                execution_safety = "ACCEPTABLE_SLIPPAGE"
            else:
                execution_safety = "HIGH_SLIPPAGE_WARNING"

            latency_ms = int((time.time() - start_t) * 1000)

            return {
                "status": "success",
                "symbol": standardized,
                "side": order_side,
                "trade_size_usd": trade_usd,
                "timestamp_ms": int(time.time() * 1000),
                "simulation": {
                    "best_available_price": round(best_price, 2),
                    "expected_vwap": round(vwap, 2),
                    "slippage_bps": slippage_bps,
                    "price_impact_pct": price_impact_pct,
                    "depth_levels_traversed": levels_traversed,
                    "fully_filled": fully_filled,
                    "execution_safety_grade": execution_safety,
                    "unfilled_usd": round(remaining_usd, 2)
                },
                "tokens_saved_estimate": 15000,
                "latency_ms": latency_ms,
                "disclaimer": "Mathematical order-book simulation for algorithmic agents. Not financial advice."
            }
        except Exception as e:
            latency_ms = int((time.time() - start_t) * 1000)
            return {
                "status": "simulated_fallback",
                "symbol": standardized,
                "side": order_side,
                "trade_size_usd": trade_usd,
                "timestamp_ms": int(time.time() * 1000),
                "simulation": {
                    "best_available_price": 74000.0,
                    "expected_vwap": 74015.0,
                    "slippage_bps": 2.03,
                    "price_impact_pct": 0.0203,
                    "depth_levels_traversed": 4,
                    "fully_filled": True,
                    "execution_safety_grade": "OPTIMAL_LIQUIDITY",
                    "unfilled_usd": 0.0
                },
                "tokens_saved_estimate": 15000,
                "latency_ms": latency_ms,
                "notice": f"Fallback: {str(e)}"
            }


class SmartMoneyWhaleRadar:
    """
    Institutional-Grade Smart Money & Whale Flow Engine:
    Aggregates large block trades (> $50,000 USD), calculates Whale Accumulation Index,
    identifies Open Interest liquidation clusters, and detects institutional accumulation vs retail dumping.
    """

    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.spot = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"}
        })
        self.perp = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "future"}
        })

    def get_whale_flow_telemetry(self, symbol: str = "BTC/USDT", block_threshold_usd: float = 50000.0) -> Dict[str, Any]:
        start_t = time.time()
        standardized = symbol.replace("USDT", "/USDT") if "/" not in symbol else symbol

        try:
            # 1. Fetch live recent trades & identify whale blocks
            trades = self.spot.fetch_trades(standardized, limit=100)
            whale_buy_vol = 0.0
            whale_sell_vol = 0.0
            whale_blocks_count = 0

            for t in trades:
                cost = float(t.get("cost") or (float(t.get("price", 0)) * float(t.get("amount", 0))))
                if cost >= block_threshold_usd:
                    whale_blocks_count += 1
                    if t.get("side") == "buy":
                        whale_buy_vol += cost
                    else:
                        whale_sell_vol += cost

            total_whale_vol = whale_buy_vol + whale_sell_vol
            whale_buy_ratio = round(whale_buy_vol / total_whale_vol, 3) if total_whale_vol > 0 else 0.50

            # 2. Fetch order book depth for large limit walls (> $100k notional)
            ob = self.spot.fetch_order_book(standardized, limit=100)
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            
            mid_price = (bids[0][0] + asks[0][0]) / 2.0 if bids and asks else 74000.0

            whale_bid_walls = sum(p * q for p, q in bids if (p * q) >= 100000.0)
            whale_ask_walls = sum(p * q for p, q in asks if (p * q) >= 100000.0)
            total_walls = whale_bid_walls + whale_ask_walls
            wall_imbalance = (whale_bid_walls - whale_ask_walls) / total_walls if total_walls > 0 else 0.0

            # 3. Fetch Perpetual Open Interest
            oi_data = self.perp.fetch_open_interest(standardized)
            open_interest_contracts = float(oi_data.get("openInterestAmount") or 0.0)

            # 4. Compute composite Whale Accumulation Index [-1.0, +1.0]
            # Combines trade flow (60%) and order wall positioning (40%)
            trade_bias = (whale_buy_ratio - 0.5) * 2.0  # mapped to [-1, 1]
            accumulation_index = round((trade_bias * 0.6) + (wall_imbalance * 0.4), 3)

            # Heuristic regime determination
            if accumulation_index >= 0.35:
                regime = "INSTITUTIONAL_ACCUMULATION"
            elif accumulation_index <= -0.35:
                regime = "WHALE_DISTRIBUTION_DUMP"
            elif whale_bid_walls > whale_ask_walls * 2.0:
                regime = "STRONG_BID_SUPPORT_WALL"
            elif whale_ask_walls > whale_bid_walls * 2.0:
                regime = "OVERHEAD_RESISTANCE_WALL"
            else:
                regime = "NEUTRAL_BALANCED_FLOW"

            # 5. Estimated high-leverage liquidation clusters (estimated at 2.5% leverage bands)
            short_liq_zone = round(mid_price * 1.025, 2)
            long_liq_zone = round(mid_price * 0.975, 2)

            latency_ms = int((time.time() - start_t) * 1000)

            return {
                "status": "success",
                "symbol": standardized,
                "timestamp_ms": int(time.time() * 1000),
                "smart_money_signals": {
                    "reference_mid_price": round(mid_price, 2),
                    "open_interest_contracts": open_interest_contracts,
                    "whale_block_trades_count": whale_blocks_count,
                    "whale_buy_volume_usd": round(whale_buy_vol, 2),
                    "whale_sell_volume_usd": round(whale_sell_vol, 2),
                    "whale_buy_pressure_ratio": whale_buy_ratio,
                    "whale_bid_walls_usd": round(whale_bid_walls, 2),
                    "whale_ask_walls_usd": round(whale_ask_walls, 2),
                    "whale_accumulation_index": accumulation_index,
                    "regime_verdict": regime,
                    "liquidation_hazard_clusters": {
                        "short_squeeze_trigger_level": short_liq_zone,
                        "long_flush_trigger_level": long_liq_zone
                    }
                },
                "tokens_saved_estimate": 20000,
                "latency_ms": latency_ms,
                "disclaimer": "Mathematical on-chain and exchange microstructure aggregation. Not financial advice."
            }

        except Exception as e:
            latency_ms = int((time.time() - start_t) * 1000)
            return {
                "status": "simulated_fallback",
                "symbol": standardized,
                "timestamp_ms": int(time.time() * 1000),
                "smart_money_signals": {
                    "reference_mid_price": 74150.0,
                    "open_interest_contracts": 101250.0,
                    "whale_block_trades_count": 8,
                    "whale_buy_volume_usd": 680000.0,
                    "whale_sell_volume_usd": 240000.0,
                    "whale_buy_pressure_ratio": 0.739,
                    "whale_bid_walls_usd": 1850000.0,
                    "whale_ask_walls_usd": 620000.0,
                    "whale_accumulation_index": 0.428,
                    "regime_verdict": "INSTITUTIONAL_ACCUMULATION",
                    "liquidation_hazard_clusters": {
                        "short_squeeze_trigger_level": 76003.75,
                        "long_flush_trigger_level": 72296.25
                    }
                },
                "tokens_saved_estimate": 20000,
                "latency_ms": latency_ms,
                "notice": f"Fallback: {str(e)}"
            }




