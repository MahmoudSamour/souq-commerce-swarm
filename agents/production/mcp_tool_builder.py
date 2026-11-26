"""
SOUQ // Autonomous FastMCP Tool Production Suite (Sani' Synthesizer)
Exposes high-value, computationally intensive analytical tools that AI agents
pay to execute via HTTP 402 Base USDC or prepaid SOUQ API keys.
"""

from datetime import datetime, timezone
import json
import math
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from agents.production.cyber_defense_vault import DeepASTVulnerabilityAuditor
from agents.treasury.db_backend import load_souq_env

load_souq_env()

_SYMBOL_VALID_RE = re.compile(r"^[A-Z0-9/_-]{2,20}$")


def _validate_symbol(symbol: Any) -> Tuple[bool, str]:
    """Validates and normalizes a trading pair or asset symbol."""
    if not isinstance(symbol, str):
        return False, ""
    cleaned = symbol.strip().upper()
    if not _SYMBOL_VALID_RE.match(cleaned):
        return False, cleaned
    return True, cleaned


def _upstream_unavailable(
    providers_tried: List[str],
    detail: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Standard unbilled upstream-unavailable response (no fabricated fallback data)."""
    payload: Dict[str, Any] = {
        "status": "upstream_unavailable",
        "error": "All live market data providers failed or unreachable",
        "providers_tried": providers_tried,
        "timestamp_ms": int(time.time() * 1000),
    }
    if detail:
        payload["detail"] = detail
    if extra:
        payload.update(extra)
    return payload


class _PublicMarketFeed:
    """
    Lightweight pooled REST market-data & Polymarket Gamma client with short TTL caching
    and geo-resilient multi-venue failover:
    Coinbase Exchange -> Kraken -> Hyperliquid -> Deribit -> OKX / CoinGecko
    (with geo-safe unauthenticated data-api.binance.vision Spot-only archive as last resort).
    """

    COINBASE_BASE = "https://api.exchange.coinbase.com"
    KRAKEN_BASE = "https://api.kraken.com"
    HYPERLIQUID_INFO = "https://api.hyperliquid.xyz/info"
    DERIBIT_BASE = "https://www.deribit.com/api/v2/public"
    OKX_BASE = "https://www.okx.com"
    COINGECKO_BASE = "https://api.coingecko.com/api/v3"
    BINANCE_VISION_BASE = "https://data-api.binance.vision"
    POLYMARKET_GAMMA = "https://gamma-api.polymarket.com/events"

    KNOWN_QUOTES = ("FDUSD", "USDT", "USDC", "BUSD", "TUSD", "USD", "EUR", "BTC", "ETH")
    _KRAKEN_ASSET_MAP = {"BTC": "XBT", "DOGE": "XDG"}
    _COINGECKO_ID_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "XRP": "ripple",
        "DOGE": "dogecoin",
        "BNB": "binancecoin",
        "ADA": "cardano",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
    }

    def __init__(self, timeout_s: float = 3.5):
        self.timeout_s = timeout_s
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "SOUQ-Quant-Engine/0.3 (+https://github.com/MahmoudSamour/souq-commerce-swarm)",
            "Accept": "application/json",
        })
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @classmethod
    def split_symbol(cls, symbol: str) -> Tuple[str, str]:
        clean = (symbol or "").upper().strip()
        for sep in ("/", "-", "_"):
            if sep in clean:
                base, quote = clean.split(sep, 1)
                return base.strip(), (quote.strip() or "USDT")
        for quote in sorted(cls.KNOWN_QUOTES, key=len, reverse=True):
            if clean.endswith(quote) and len(clean) > len(quote):
                return clean[:-len(quote)], quote
        return clean, "USDT"

    @classmethod
    def standardize_symbol(cls, symbol: str) -> str:
        base, quote = cls.split_symbol(symbol)
        return f"{base}/{quote}"

    @classmethod
    def pair_id(cls, symbol: str) -> str:
        base, quote = cls.split_symbol(symbol)
        return f"{base}{quote}"

    @classmethod
    def _kraken_pair(cls, base: str, quote: str) -> str:
        k_base = cls._KRAKEN_ASSET_MAP.get(base, base)
        return f"{k_base}{quote}"

    @staticmethod
    def _parse_iso_ms(iso_str: Optional[str]) -> int:
        if not iso_str or not isinstance(iso_str, str):
            return 0
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except ValueError:
            return 0

    def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None, ttl_s: float = 4.0) -> Any:
        key = f"GET:{url}?{json.dumps(params or {}, sort_keys=True)}"
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(key)
            if cached and (now - cached[0]) < ttl_s:
                return cached[1]

        resp = self._session.get(url, params=params, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()

        with self._lock:
            self._cache[key] = (now, data)
            if len(self._cache) > 256:
                oldest = min(self._cache.items(), key=lambda item: item[1][0])[0]
                self._cache.pop(oldest, None)
        return data

    def _post_json(self, url: str, payload: Dict[str, Any], ttl_s: float = 4.0) -> Any:
        key = f"POST:{url}?{json.dumps(payload, sort_keys=True)}"
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(key)
            if cached and (now - cached[0]) < ttl_s:
                return cached[1]

        resp = self._session.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()

        with self._lock:
            self._cache[key] = (now, data)
            if len(self._cache) > 256:
                oldest = min(self._cache.items(), key=lambda item: item[1][0])[0]
                self._cache.pop(oldest, None)
        return data

    def fetch_usdt_usd_rate(self) -> Optional[float]:
        """Fetches live USDT/USD exchange rate from Coinbase or Kraken."""
        try:
            cb = self._get_json(f"{self.COINBASE_BASE}/products/USDT-USD/ticker", ttl_s=10.0)
            rate = float(cb["price"])
            if 0.90 <= rate <= 1.10:
                return rate
        except Exception:
            pass
        try:
            kr = self._get_json(f"{self.KRAKEN_BASE}/0/public/Ticker", params={"pair": "USDTUSD"}, ttl_s=10.0)
            if not kr.get("error") and kr.get("result"):
                first_row = next(iter(kr["result"].values()))
                rate = float(first_row["c"][0])
                if 0.90 <= rate <= 1.10:
                    return rate
        except Exception:
            pass
        return None

    def fetch_spot_order_book(self, symbol: str, limit: int = 20) -> Tuple[List[List[float]], List[List[float]], str]:
        base, quote = self.split_symbol(symbol)
        pair = f"{base}{quote}"
        allowed_limits = [5, 10, 20, 50, 100, 500]
        vision_limit = min((v for v in allowed_limits if v >= limit), default=100)
        providers_tried: List[str] = []
        last_err: Optional[Exception] = None

        # 1. Coinbase Exchange L2
        providers_tried.append("coinbase_exchange")
        try:
            cb = self._get_json(
                f"{self.COINBASE_BASE}/products/{base}-USD/book",
                params={"level": 2},
                ttl_s=3.0,
            )
            bids = [[float(entry[0]), float(entry[1])] for entry in cb.get("bids", [])[:limit]]
            asks = [[float(entry[0]), float(entry[1])] for entry in cb.get("asks", [])[:limit]]
            if bids and asks:
                return bids, asks, "coinbase_exchange"
        except Exception as exc:
            last_err = exc

        # 2. Kraken Depth
        providers_tried.append("kraken")
        try:
            k_pair = self._kraken_pair(base, "USD" if quote in ("USD", "USDT") else quote)
            kr = self._get_json(
                f"{self.KRAKEN_BASE}/0/public/Depth",
                params={"pair": k_pair, "count": min(limit, 100)},
                ttl_s=3.0,
            )
            if not kr.get("error") and kr.get("result"):
                book = next(iter(kr["result"].values()))
                bids = [[float(p), float(q)] for p, q, *_ in book.get("bids", [])[:limit]]
                asks = [[float(p), float(q)] for p, q, *_ in book.get("asks", [])[:limit]]
                if bids and asks:
                    return bids, asks, "kraken"
        except Exception as exc:
            last_err = exc

        # 3. Hyperliquid L2 Book
        providers_tried.append("hyperliquid")
        try:
            hl = self._post_json(
                self.HYPERLIQUID_INFO,
                {"type": "l2Book", "coin": base},
                ttl_s=3.0,
            )
            levels = hl.get("levels") or []
            if len(levels) >= 2:
                bids = [[float(lv["px"]), float(lv["sz"])] for lv in levels[0][:limit]]
                asks = [[float(lv["px"]), float(lv["sz"])] for lv in levels[1][:limit]]
                if bids and asks:
                    return bids, asks, "hyperliquid"
        except Exception as exc:
            last_err = exc

        # 4. Geo-safe unauthenticated Spot-only public archive (data-api.binance.vision)
        providers_tried.append("binance_vision")
        try:
            bv_pair = pair if quote != "USD" else f"{base}USDT"
            data = self._get_json(
                f"{self.BINANCE_VISION_BASE}/api/v3/depth",
                params={"symbol": bv_pair, "limit": vision_limit},
                ttl_s=3.0,
            )
            bids = [[float(p), float(q)] for p, q in data.get("bids", [])[:limit]]
            asks = [[float(p), float(q)] for p, q in data.get("asks", [])[:limit]]
            if bids and asks:
                return bids, asks, "binance_vision"
        except Exception as exc:
            last_err = exc

        raise RuntimeError(f"All spot depth venues failed for {symbol} ({providers_tried}): {last_err}")

    def fetch_spot_price_meta(self, symbol: str) -> Tuple[float, str, str, int, List[str]]:
        """
        Fetches live spot price with metadata:
        (price, venue, quote_currency, exchange_timestamp_ms, providers_tried).
        """
        base, quote = self.split_symbol(symbol)
        pair = f"{base}{quote}"
        providers_tried: List[str] = []
        last_err: Optional[Exception] = None

        # 1. Coinbase Exchange (USD native)
        providers_tried.append("coinbase_exchange")
        try:
            cb = self._get_json(f"{self.COINBASE_BASE}/products/{base}-USD/ticker", ttl_s=4.0)
            price = float(cb["price"])
            ts_ms = self._parse_iso_ms(cb.get("time")) or int(time.time() * 1000)
            if price > 0:
                return price, "coinbase_exchange", "USD", ts_ms, providers_tried
        except Exception as exc:
            last_err = exc

        # 2. Kraken
        providers_tried.append("kraken")
        for k_quote in ([quote, "USD"] if quote != "USD" else ["USD"]):
            try:
                k_pair = self._kraken_pair(base, k_quote)
                kr = self._get_json(
                    f"{self.KRAKEN_BASE}/0/public/Ticker",
                    params={"pair": k_pair},
                    ttl_s=4.0,
                )
                if not kr.get("error") and kr.get("result"):
                    row = next(iter(kr["result"].values()))
                    price = float(row["c"][0])
                    if price > 0:
                        return price, "kraken", k_quote, int(time.time() * 1000), providers_tried
            except Exception as exc:
                last_err = exc

        # 3. Deribit Index (for BTC/ETH/SOL)
        if base in ("BTC", "ETH", "SOL"):
            providers_tried.append("deribit_index")
            try:
                db = self._get_json(
                    f"{self.DERIBIT_BASE}/get_index_price",
                    params={"index_name": f"{base.lower()}_usd"},
                    ttl_s=4.0,
                )
                price = float((db.get("result") or {}).get("index_price") or 0.0)
                if price > 0:
                    return price, "deribit_index", "USD", int(time.time() * 1000), providers_tried
            except Exception as exc:
                last_err = exc

        # 4. CoinGecko
        cg_id = self._COINGECKO_ID_MAP.get(base)
        if cg_id:
            providers_tried.append("coingecko")
            try:
                cg = self._get_json(
                    f"{self.COINGECKO_BASE}/simple/price",
                    params={"ids": cg_id, "vs_currencies": "usd"},
                    ttl_s=15.0,
                )
                price = float((cg.get(cg_id) or {}).get("usd") or 0.0)
                if price > 0:
                    return price, "coingecko", "USD", int(time.time() * 1000), providers_tried
            except Exception as exc:
                last_err = exc

        # 5. Geo-safe unauthenticated Spot-only public archive (data-api.binance.vision)
        providers_tried.append("binance_vision")
        try:
            bv_pair = pair if quote != "USD" else f"{base}USDT"
            bv_quote = quote if quote != "USD" else "USDT"
            data = self._get_json(
                f"{self.BINANCE_VISION_BASE}/api/v3/ticker/price",
                params={"symbol": bv_pair},
                ttl_s=4.0,
            )
            price = float(data["price"])
            if price > 0:
                return price, "binance_vision", bv_quote, int(time.time() * 1000), providers_tried
        except Exception as exc:
            last_err = exc

        raise RuntimeError(f"Unable to fetch spot price for {symbol} ({providers_tried}): {last_err}")

    def fetch_spot_price(self, symbol: str) -> Tuple[float, str]:
        price, venue, _, _, _ = self.fetch_spot_price_meta(symbol)
        return price, venue

    def fetch_perp_premium_meta(self, symbol: str) -> Tuple[float, float, str, str, int, List[str]]:
        """
        Fetches perpetual mark price & 8h funding rate across non-Binance venues:
        Hyperliquid -> Deribit -> OKX Swap.
        Returns (mark_price, funding_rate_8h, venue, quote_ccy, ts_ms, providers_tried).
        """
        base, _ = self.split_symbol(symbol)
        providers_tried: List[str] = []
        last_err: Optional[Exception] = None

        # 1. Hyperliquid (geo-unblocked; funding field is 1-hour rate -> * 8 for 8h convention)
        providers_tried.append("hyperliquid")
        try:
            hl = self._post_json(self.HYPERLIQUID_INFO, {"type": "metaAndAssetCtxs"}, ttl_s=4.0)
            if isinstance(hl, list) and len(hl) >= 2:
                universe = hl[0].get("universe") or []
                ctxs = hl[1] or []
                for idx, asset_meta in enumerate(universe):
                    if str(asset_meta.get("name", "")).upper() == base and idx < len(ctxs):
                        ctx = ctxs[idx]
                        mark = float(ctx.get("markPx") or ctx.get("midPx") or 0.0)
                        funding_1h = float(ctx.get("funding") or 0.0)
                        if mark > 0:
                            return mark, funding_1h * 8.0, "hyperliquid", "USD", int(time.time() * 1000), providers_tried
        except Exception as exc:
            last_err = exc

        # 2. Deribit Perpetual
        if base in ("BTC", "ETH", "SOL"):
            providers_tried.append("deribit_perp")
            try:
                db = self._get_json(
                    f"{self.DERIBIT_BASE}/ticker",
                    params={"instrument_name": f"{base}-PERPETUAL"},
                    ttl_s=4.0,
                )
                res = db.get("result") or {}
                mark = float(res.get("mark_price") or res.get("last_price") or 0.0)
                funding_8h = float(res.get("funding_8h") or res.get("current_funding") or 0.0)
                ts_ms = int(res.get("timestamp") or time.time() * 1000)
                if mark > 0:
                    return mark, funding_8h, "deribit_perp", "USD", ts_ms, providers_tried
            except Exception as exc:
                last_err = exc

        # 3. OKX Swap
        providers_tried.append("okx_swap")
        try:
            inst_id = f"{base}-USDT-SWAP"
            ticker = self._get_json(
                f"{self.OKX_BASE}/api/v5/market/ticker",
                params={"instId": inst_id},
                ttl_s=4.0,
            )
            funding_resp = self._get_json(
                f"{self.OKX_BASE}/api/v5/public/funding-rate",
                params={"instId": inst_id},
                ttl_s=15.0,
            )
            t_rows = ticker.get("data") or []
            f_rows = funding_resp.get("data") or []
            if t_rows:
                mark = float(t_rows[0]["last"])
                funding = float(f_rows[0]["fundingRate"]) if f_rows else 0.0
                ts_ms = int(t_rows[0].get("ts") or time.time() * 1000)
                if mark > 0:
                    return mark, funding, "okx_swap", "USDT", ts_ms, providers_tried
        except Exception as exc:
            last_err = exc

        raise RuntimeError(f"All perp venues failed for {symbol} ({providers_tried}): {last_err}")

    def fetch_perp_premium(self, symbol: str) -> Tuple[float, float, str]:
        """Returns (perp_mark_price, funding_rate_8h, source)."""
        mark, funding, src, _, _, _ = self.fetch_perp_premium_meta(symbol)
        return mark, funding, src

    def fetch_open_interest(self, symbol: str) -> Optional[float]:
        base, _ = self.split_symbol(symbol)

        # 1. Hyperliquid
        try:
            hl = self._post_json(self.HYPERLIQUID_INFO, {"type": "metaAndAssetCtxs"}, ttl_s=10.0)
            if isinstance(hl, list) and len(hl) >= 2:
                universe = hl[0].get("universe") or []
                ctxs = hl[1] or []
                for idx, asset_meta in enumerate(universe):
                    if str(asset_meta.get("name", "")).upper() == base and idx < len(ctxs):
                        oi = float(ctxs[idx].get("openInterest") or 0.0)
                        if oi > 0:
                            return oi
        except Exception:
            pass

        # 2. Deribit Perpetual
        if base in ("BTC", "ETH", "SOL"):
            try:
                db = self._get_json(
                    f"{self.DERIBIT_BASE}/ticker",
                    params={"instrument_name": f"{base}-PERPETUAL"},
                    ttl_s=10.0,
                )
                oi = float((db.get("result") or {}).get("open_interest") or 0.0)
                if oi > 0:
                    return oi
            except Exception:
                pass

        # 3. OKX Swap
        try:
            resp = self._get_json(
                f"{self.OKX_BASE}/api/v5/public/open-interest",
                params={"instType": "SWAP", "instId": f"{base}-USDT-SWAP"},
                ttl_s=15.0,
            )
            rows = resp.get("data") or []
            if rows:
                oi = float(rows[0].get("oi") or 0.0)
                if oi > 0:
                    return oi
        except Exception:
            pass

        return None

    def fetch_spot_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        base, quote = self.split_symbol(symbol)
        pair = f"{base}{quote}"
        last_err: Optional[Exception] = None

        # 1. Coinbase Exchange
        try:
            rows = self._get_json(
                f"{self.COINBASE_BASE}/products/{base}-USD/trades",
                params={"limit": min(limit, 100)},
                ttl_s=3.0,
            )
            return [
                {
                    "price": float(r["price"]),
                    "amount": float(r["size"]),
                    "cost": float(r["price"]) * float(r["size"]),
                    "side": "sell" if r.get("side") == "buy" else "buy",
                }
                for r in rows
            ]
        except Exception as exc:
            last_err = exc

        # 2. Kraken Trades
        try:
            k_pair = self._kraken_pair(base, "USD" if quote in ("USD", "USDT") else quote)
            kr = self._get_json(
                f"{self.KRAKEN_BASE}/0/public/Trades",
                params={"pair": k_pair},
                ttl_s=3.0,
            )
            if not kr.get("error") and kr.get("result"):
                rows = next(iter(kr["result"].values()))
                if isinstance(rows, list):
                    return [
                        {
                            "price": float(r[0]),
                            "amount": float(r[1]),
                            "cost": float(r[0]) * float(r[1]),
                            "side": "buy" if r[3] == "b" else "sell",
                        }
                        for r in rows[-limit:]
                    ]
        except Exception as exc:
            last_err = exc

        # 3. Geo-safe unauthenticated Spot-only public archive (data-api.binance.vision)
        try:
            bv_pair = pair if quote != "USD" else f"{base}USDT"
            rows = self._get_json(
                f"{self.BINANCE_VISION_BASE}/api/v3/trades",
                params={"symbol": bv_pair, "limit": min(limit, 500)},
                ttl_s=3.0,
            )
            return [
                {
                    "price": float(r["price"]),
                    "amount": float(r["qty"]),
                    "cost": float(r.get("quoteQty") or (float(r["price"]) * float(r["qty"]))),
                    "side": "sell" if r.get("isBuyerMaker") else "buy",
                }
                for r in rows
            ]
        except Exception as exc:
            last_err = exc

        raise RuntimeError(f"Unable to fetch recent trades for {symbol}: {last_err}")

    def fetch_deribit_dvol(self, asset: str) -> Optional[float]:
        """Fetches live annualized DVOL implied volatility (e.g. 0.45 for 45%) for BTC or ETH."""
        clean = (asset or "").strip().upper()
        if clean not in ("BTC", "ETH"):
            return None
        try:
            end_ms = int(time.time() * 1000)
            start_ms = end_ms - (12 * 3600 * 1000)
            resp = self._get_json(
                f"{self.DERIBIT_BASE}/get_volatility_index_data",
                params={
                    "currency": clean,
                    "resolution": "3600",
                    "start_timestamp": start_ms,
                    "end_timestamp": end_ms,
                },
                ttl_s=120.0,
            )
            candles = (resp.get("result") or {}).get("data") or []
            if candles:
                latest_close = float(candles[-1][4])
                if latest_close > 0:
                    return round(latest_close / 100.0, 4)
        except Exception:
            pass
        return None

    def fetch_realized_volatility(self, symbol: str, lookback_days: int = 30) -> float:
        base, quote = self.split_symbol(symbol)
        pair = f"{base}{quote}"
        closes: List[float] = []

        # 1. Coinbase Exchange daily candles ([time, low, high, open, close, volume] newest first)
        try:
            candles = self._get_json(
                f"{self.COINBASE_BASE}/products/{base}-USD/candles",
                params={"granularity": 86400},
                ttl_s=300.0,
            )
            if isinstance(candles, list) and len(candles) >= 7:
                ordered = sorted(candles[:lookback_days + 1], key=lambda c: c[0])
                closes = [float(c[4]) for c in ordered if len(c) > 4]
        except Exception:
            closes = []

        # 2. Kraken daily OHLC
        if len(closes) < 7:
            try:
                k_pair = self._kraken_pair(base, "USD" if quote in ("USD", "USDT") else quote)
                kr = self._get_json(
                    f"{self.KRAKEN_BASE}/0/public/OHLC",
                    params={"pair": k_pair, "interval": 1440},
                    ttl_s=300.0,
                )
                if not kr.get("error") and kr.get("result"):
                    rows = next(iter(kr["result"].values()))
                    if isinstance(rows, list):
                        closes = [float(r[4]) for r in rows[-(lookback_days + 1):] if len(r) > 4]
            except Exception:
                closes = []

        # 3. Geo-safe unauthenticated Spot-only public archive (data-api.binance.vision)
        if len(closes) < 7:
            try:
                bv_pair = pair if quote != "USD" else f"{base}USDT"
                klines = self._get_json(
                    f"{self.BINANCE_VISION_BASE}/api/v3/klines",
                    params={"symbol": bv_pair, "interval": "1d", "limit": lookback_days + 1},
                    ttl_s=300.0,
                )
                closes = [float(k[4]) for k in klines if len(k) > 4]
            except Exception:
                closes = []

        if len(closes) < 7:
            raise RuntimeError(f"Unable to fetch historical klines for volatility calculation: {symbol}")

        log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
        if len(log_returns) < 2:
            raise RuntimeError(f"Insufficient valid log-returns for volatility calculation: {symbol}")
        mean_r = sum(log_returns) / len(log_returns)
        var = sum((r - mean_r) ** 2 for r in log_returns) / (len(log_returns) - 1)
        ann_vol = math.sqrt(var) * math.sqrt(365.0)
        return round(max(0.10, min(2.50, ann_vol)), 4)

    def fetch_polymarket_events(self, limit: int = 100, tag_slug: str = "crypto") -> List[Dict[str, Any]]:
        """Fetches active crypto prediction events from Polymarket Gamma API with pagination."""
        page_size = min(100, max(1, int(limit)))
        all_events: List[Dict[str, Any]] = []
        for offset in (0, page_size):
            batch = self._get_json(
                self.POLYMARKET_GAMMA,
                params={
                    "active": "true",
                    "closed": "false",
                    "tag_slug": tag_slug,
                    "limit": page_size,
                    "offset": offset,
                    "order": "volume24hr",
                    "ascending": "false",
                },
                ttl_s=60.0,
            )
            if not isinstance(batch, list) or not batch:
                break
            all_events.extend(batch)
            if len(batch) < page_size or len(all_events) >= limit * 2:
                break
        return all_events


_SHARED_FEED = _PublicMarketFeed()


class MarketMicrostructureEngine:
    """
    Direct multi-venue REST integration calculating live order-book depth,
    Order Book Imbalance (OBI), and liquidation cascade probabilities.
    """

    def __init__(self, feed: Optional[_PublicMarketFeed] = None):
        self.feed = feed or _SHARED_FEED

    def get_microstructure_metrics(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        """
        Calculates mathematical order book metrics. 100% descriptive factual math.
        """
        start_t = time.time()
        ok, clean_symbol = _validate_symbol(symbol)
        if not ok:
            return {
                "status": "error",
                "error": "invalid_symbol",
                "message": "symbol must match ^[A-Z0-9/_-]{2,20}$",
            }
        standardized_symbol = _PublicMarketFeed.standardize_symbol(clean_symbol)

        try:
            bids, asks, venue = self.feed.fetch_spot_order_book(standardized_symbol, limit=20)
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            mid_price = (best_bid + best_ask) / 2.0
            spread_bps = ((best_ask - best_bid) / mid_price) * 10000.0

            total_bid_vol = sum(b[1] for b in bids)
            total_ask_vol = sum(a[1] for a in asks)

            # Order Book Imbalance (OBI) in [-1.0, 1.0]
            obi = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol) if (total_bid_vol + total_ask_vol) > 0 else 0.0
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
                "data_source": f"live:{venue}",
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
            latency_ms = int((time.time() - start_t) * 1000)
            return _upstream_unavailable(
                providers_tried=["coinbase_exchange", "kraken", "hyperliquid", "binance_vision"],
                detail=str(e),
                extra={"symbol": standardized_symbol, "latency_ms": latency_ms},
            )


class ASTSecurityScanner:
    """
    Static Code Analysis & Security Linting engine.
    Delegates to DeepASTVulnerabilityAuditor with full input/AST safety.
    """

    def __init__(self) -> None:
        self._auditor = DeepASTVulnerabilityAuditor()

    def scan_python_code(self, source_code: str) -> Dict[str, Any]:
        return self._auditor.scan_code(source_code)


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
    (with FX USDT/USD normalization and timestamp skew validation) and calculates
    annualized Delta-Neutral Funding Rate APR across major pairs.
    """

    MAX_TIMESTAMP_SKEW_MS = 30_000

    def __init__(self, feed: Optional[_PublicMarketFeed] = None):
        self.feed = feed or _SHARED_FEED

    def scan_arbitrage_and_funding(self, symbol: str = "BTC/USDT") -> Dict[str, Any]:
        start_t = time.time()
        ok, clean_symbol = _validate_symbol(symbol)
        if not ok:
            return {
                "status": "error",
                "error": "invalid_symbol",
                "message": "symbol must match ^[A-Z0-9/_-]{2,20}$",
            }
        standardized = _PublicMarketFeed.standardize_symbol(clean_symbol)
        _, target_quote = _PublicMarketFeed.split_symbol(standardized)
        providers_tried: List[str] = []

        try:
            t0_ms = int(time.time() * 1000)
            if isinstance(self.feed, _PublicMarketFeed):
                spot_price, spot_src, spot_quote, spot_ts_ms, spot_tried = self.feed.fetch_spot_price_meta(standardized)
                providers_tried.extend(spot_tried)
            else:
                spot_price, spot_src = self.feed.fetch_spot_price(standardized)
                spot_quote = "USD" if "coinbase" in str(spot_src).lower() else target_quote
                spot_ts_ms = int(time.time() * 1000)

            if isinstance(self.feed, _PublicMarketFeed):
                perp_price, funding_rate, perp_src, perp_quote, perp_ts_ms, perp_tried = self.feed.fetch_perp_premium_meta(standardized)
                providers_tried.extend(p for p in perp_tried if p not in providers_tried)
            else:
                perp_price, funding_rate, perp_src = self.feed.fetch_perp_premium(standardized)
                perp_quote = "USD" if "hyperliquid" in str(perp_src).lower() else "USDT"
                perp_ts_ms = int(time.time() * 1000)

            t1_ms = int(time.time() * 1000)
            exchange_skew_ms = abs(spot_ts_ms - perp_ts_ms)
            fetch_skew_ms = abs(t1_ms - t0_ms)
            timestamp_skew_ms = max(exchange_skew_ms, fetch_skew_ms)

            if timestamp_skew_ms > self.MAX_TIMESTAMP_SKEW_MS:
                return _upstream_unavailable(
                    providers_tried=providers_tried,
                    detail=f"Quote timestamp skew ({timestamp_skew_ms}ms) exceeded {self.MAX_TIMESTAMP_SKEW_MS}ms safety limit.",
                    extra={
                        "error": "stale_or_skewed_quote_timestamps",
                        "symbol": standardized,
                        "timestamp_skew_ms": timestamp_skew_ms,
                    },
                )

            # FX normalization when comparing USD/USDC vs USDT quotes
            fx_adjusted = False
            usdt_usd_rate: Optional[float] = None
            norm_quote = "USD" if target_quote == "USD" else "USDT"
            norm_spot = spot_price
            norm_perp = perp_price

            if spot_quote != perp_quote and {spot_quote, perp_quote} & {"USDT"} and {spot_quote, perp_quote} & {"USD", "USDC"}:
                usdt_usd_rate = self.feed.fetch_usdt_usd_rate() if hasattr(self.feed, "fetch_usdt_usd_rate") else None
                if not isinstance(usdt_usd_rate, (int, float)) or isinstance(usdt_usd_rate, bool) or usdt_usd_rate <= 0:
                    return _upstream_unavailable(
                        providers_tried=providers_tried + ["coinbase_usdt_usd", "kraken_usdt_usd"],
                        detail="Cannot compare USD and USDT venues accurately without live USDT/USD FX rate.",
                        extra={"symbol": standardized},
                    )
                if norm_quote == "USDT":
                    if spot_quote in ("USD", "USDC"):
                        norm_spot = spot_price / usdt_usd_rate
                    if perp_quote in ("USD", "USDC"):
                        norm_perp = perp_price / usdt_usd_rate
                else:
                    if spot_quote == "USDT":
                        norm_spot = spot_price * usdt_usd_rate
                    if perp_quote == "USDT":
                        norm_perp = perp_price * usdt_usd_rate
                fx_adjusted = True

            basis_spread_bps = ((norm_perp - norm_spot) / norm_spot) * 10000.0
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
                "data_source": f"live:{spot_src}+{perp_src}",
                "symbol": standardized,
                "timestamp_ms": int(time.time() * 1000),
                "arbitrage_metrics": {
                    "spot_price": round(norm_spot, 2),
                    "perp_price": round(norm_perp, 2),
                    "quote_currency": norm_quote,
                    "fx_adjusted": fx_adjusted,
                    "usdt_usd_rate": round(usdt_usd_rate, 6) if usdt_usd_rate else None,
                    "timestamp_skew_ms": timestamp_skew_ms,
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
            return _upstream_unavailable(
                providers_tried=providers_tried or ["binance_vision", "coinbase_exchange", "kraken", "hyperliquid", "deribit_perp", "okx_swap"],
                detail=str(e),
                extra={"symbol": standardized, "latency_ms": latency_ms},
            )


class OrderBookSlippageSimulator:
    """
    High-demand A2A Quant Tool: Simulates order-book walk on live depth (up to 100 levels)
    to calculate volume-weighted average execution price (VWAP), price impact, and expected
    slippage in basis points for any hypothetical trade size in USD.
    """

    def __init__(self, feed: Optional[_PublicMarketFeed] = None):
        self.feed = feed or _SHARED_FEED

    def simulate_slippage(self, symbol: str = "BTC/USDT", side: str = "BUY", trade_size_usd: float = 10000.0) -> Dict[str, Any]:
        start_t = time.time()
        ok, clean_symbol = _validate_symbol(symbol)
        if not ok:
            return {
                "status": "error",
                "error": "invalid_symbol",
                "message": "symbol must match ^[A-Z0-9/_-]{2,20}$",
            }
        if not isinstance(side, str) or side.strip().upper() not in ("BUY", "SELL"):
            return {
                "status": "error",
                "error": "invalid_side",
                "message": "side must be 'BUY' or 'SELL'",
            }
        try:
            raw_size = float(trade_size_usd)
            if not math.isfinite(raw_size) or raw_size <= 0:
                return {"status": "error", "error": "invalid_trade_size", "message": "trade_size_usd must be a positive finite number."}
        except (TypeError, ValueError):
            return {"status": "error", "error": "invalid_trade_size", "message": "trade_size_usd must be numeric."}

        standardized = _PublicMarketFeed.standardize_symbol(clean_symbol)
        order_side = side.upper().strip()
        trade_usd = max(10.0, raw_size)

        try:
            bids, asks, venue = self.feed.fetch_spot_order_book(standardized, limit=100)
            levels = asks if order_side == "BUY" else bids

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
                "data_source": f"live:{venue}",
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
            return _upstream_unavailable(
                providers_tried=["coinbase_exchange", "kraken", "hyperliquid", "binance_vision"],
                detail=str(e),
                extra={"symbol": standardized, "side": order_side, "latency_ms": latency_ms},
            )


class SmartMoneyWhaleRadar:
    """
    Institutional-Grade Smart Money & Whale Flow Engine:
    Aggregates large block trades, calculates Whale Accumulation Index,
    identifies real orderbook liquidity clusters + Hyperliquid/Deribit/OKX OI & funding,
    and detects institutional accumulation vs retail distribution.
    """

    def __init__(self, feed: Optional[_PublicMarketFeed] = None):
        self.feed = feed or _SHARED_FEED

    @staticmethod
    def _extract_liquidity_clusters(
        levels: List[List[float]],
        mid_price: float,
        bucket_bps: float = 10.0,
        top_n: int = 3,
    ) -> List[Dict[str, float]]:
        """Groups live orderbook depth into 10 bps price buckets and returns top notional clusters."""
        if not levels or mid_price <= 0:
            return []
        step = max(mid_price * (bucket_bps / 10000.0), 1e-6)
        buckets: Dict[float, float] = {}
        for price, qty in levels:
            notional = float(price) * float(qty)
            if notional <= 0:
                continue
            bucket_price = round(round(float(price) / step) * step, 2)
            buckets[bucket_price] = buckets.get(bucket_price, 0.0) + notional

        ranked = sorted(buckets.items(), key=lambda item: item[1], reverse=True)[:top_n]
        return [
            {
                "price_level": round(px, 2),
                "liquidity_usd": round(notional, 2),
                "distance_from_mid_bps": round(((px - mid_price) / mid_price) * 10000.0, 2),
            }
            for px, notional in ranked
        ]

    def get_whale_flow_telemetry(self, symbol: str = "BTC/USDT", block_threshold_usd: float = 50000.0) -> Dict[str, Any]:
        start_t = time.time()
        ok, clean_symbol = _validate_symbol(symbol)
        if not ok:
            return {
                "status": "error",
                "error": "invalid_symbol",
                "message": "symbol must match ^[A-Z0-9/_-]{2,20}$",
            }
        standardized = _PublicMarketFeed.standardize_symbol(clean_symbol)

        try:
            trades = self.feed.fetch_spot_trades(standardized, limit=100)
            whale_buy_vol = 0.0
            whale_sell_vol = 0.0
            whale_blocks_count = 0

            for t in trades:
                cost = float(t["cost"])
                if cost >= block_threshold_usd:
                    whale_blocks_count += 1
                    if t.get("side") == "buy":
                        whale_buy_vol += cost
                    else:
                        whale_sell_vol += cost

            total_whale_vol = whale_buy_vol + whale_sell_vol
            whale_buy_ratio = round(whale_buy_vol / total_whale_vol, 3) if total_whale_vol > 0 else 0.50

            bids, asks, venue = self.feed.fetch_spot_order_book(standardized, limit=100)
            mid_price = (bids[0][0] + asks[0][0]) / 2.0

            whale_bid_walls = sum(p * q for p, q in bids if (p * q) >= 100000.0)
            whale_ask_walls = sum(p * q for p, q in asks if (p * q) >= 100000.0)
            total_walls = whale_bid_walls + whale_ask_walls
            wall_imbalance = (whale_bid_walls - whale_ask_walls) / total_walls if total_walls > 0 else 0.0

            open_interest_contracts = self.feed.fetch_open_interest(standardized)
            funding_rate_8h: Optional[float] = None
            perp_venue: Optional[str] = None
            try:
                _, f_rate, p_src = self.feed.fetch_perp_premium(standardized)
                funding_rate_8h = round(f_rate * 100.0, 5)
                perp_venue = p_src
            except Exception:
                pass

            trade_bias = (whale_buy_ratio - 0.5) * 2.0
            accumulation_index = round((trade_bias * 0.6) + (wall_imbalance * 0.4), 3)

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

            ask_clusters = self._extract_liquidity_clusters(asks, mid_price)
            bid_clusters = self._extract_liquidity_clusters(bids, mid_price)
            strongest_ask_level = ask_clusters[0]["price_level"] if ask_clusters else round(asks[-1][0], 2)
            strongest_bid_level = bid_clusters[0]["price_level"] if bid_clusters else round(bids[-1][0], 2)

            liquidity_cluster_summary = {
                "methodology": "orderbook_liquidity_clusters",
                "strongest_overhead_ask_cluster": strongest_ask_level,
                "strongest_underlying_bid_cluster": strongest_bid_level,
                "top_ask_clusters": ask_clusters,
                "top_bid_clusters": bid_clusters,
                "derivatives_context": {
                    "perp_venue": perp_venue,
                    "open_interest_contracts": open_interest_contracts,
                    "funding_rate_8h_pct": funding_rate_8h,
                },
            }

            latency_ms = int((time.time() - start_t) * 1000)

            return {
                "status": "success",
                "data_source": f"live:{venue}",
                "symbol": standardized,
                "timestamp_ms": int(time.time() * 1000),
                "smart_money_signals": {
                    "reference_mid_price": round(mid_price, 2),
                    "open_interest_contracts": open_interest_contracts,
                    "funding_rate_8h_pct": funding_rate_8h,
                    "whale_block_trades_count": whale_blocks_count,
                    "whale_buy_volume_usd": round(whale_buy_vol, 2),
                    "whale_sell_volume_usd": round(whale_sell_vol, 2),
                    "whale_buy_pressure_ratio": whale_buy_ratio,
                    "whale_bid_walls_usd": round(whale_bid_walls, 2),
                    "whale_ask_walls_usd": round(whale_ask_walls, 2),
                    "whale_accumulation_index": accumulation_index,
                    "regime_verdict": regime,
                    "orderbook_liquidity_clusters": liquidity_cluster_summary,
                    "liquidation_hazard_clusters": {
                        "methodology": "orderbook_liquidity_clusters",
                        "short_squeeze_trigger_level": strongest_ask_level,
                        "long_flush_trigger_level": strongest_bid_level,
                    },
                },
                "tokens_saved_estimate": 20000,
                "latency_ms": latency_ms,
                "disclaimer": "Mathematical on-chain and exchange microstructure aggregation. Not financial advice."
            }

        except Exception as e:
            latency_ms = int((time.time() - start_t) * 1000)
            return _upstream_unavailable(
                providers_tried=["coinbase_exchange", "kraken", "hyperliquid", "binance_vision"],
                detail=str(e),
                extra={"symbol": standardized, "latency_ms": latency_ms},
            )


class PredictionMarketArbitrageRadar:
    """
    Real-time cross-market probability discrepancy engine comparing live Polymarket
    binary contracts against live spot price and Deribit DVOL / 30-day realized-volatility
    pricing (distinguishing one-touch barrier contracts from European expiry contracts).
    """

    ASSET_ALIASES: Dict[str, Tuple[str, ...]] = {
        "BTC": ("bitcoin", "btc"),
        "ETH": ("ethereum", "eth"),
        "SOL": ("solana", "sol"),
        "XRP": ("ripple", "xrp"),
        "DOGE": ("dogecoin", "doge"),
    }
    STRIKE_RE = re.compile(r"\$([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+(?:\.[0-9]+)?)\s*([kKmM])?")
    RANGE_RE = re.compile(
        r"\bbetween\s+\$|\$[0-9,.]+\s*[kKmM]?\s*(?:-|–|—|\bto\b)\s*\$[0-9,.]+\s*[kKmM]?"
        r"|[0-9,.]+\s*[kKmM]\s*(?:-|–|—)\s*[0-9,.]+\s*[kKmM]",
        re.IGNORECASE,
    )
    BARRIER_KEYWORDS = ("hit", "reach", "touch")
    EUROPEAN_KEYWORDS = ("above", "below", "at or above", "at or below", "end", "close", "on ")
    DOWNWARD_KEYWORDS = ("below", "under", "less than", "drop", "fall", "dip", "crash", "at or below")
    UPWARD_KEYWORDS = ("above", "over", "exceed", "more than", "greater than", "at or above", "surge", "rally")

    def __init__(self, feed: Optional[_PublicMarketFeed] = None):
        self.feed = feed or _SHARED_FEED

    @staticmethod
    def _norm_cdf(x: float) -> float:
        """Standard normal cumulative distribution function using error function."""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    def calculate_spot_implied_probability(
        self,
        spot_price: float,
        strike_price: float,
        days_to_expiry: float,
        annualized_volatility: float = 0.55,
        risk_free_rate: float = 0.045,
        is_barrier: bool = False,
        is_below: bool = False,
    ) -> float:
        """
        Calculates risk-neutral implied probability:
        - European expiry: N(d2) for P(S_T > K) or N(-d2) for P(S_T < K)
        - One-touch barrier: reflection formula 2*N(d2) / 2*N(-d2) bounded in (0, 1),
          or 0.99 if the barrier is already breached by spot.
        """
        if spot_price <= 0 or strike_price <= 0 or days_to_expiry <= 0 or annualized_volatility <= 0:
            return 0.50

        if is_barrier:
            if not is_below and spot_price >= strike_price:
                return 0.99
            if is_below and spot_price <= strike_price:
                return 0.99

        t_years = days_to_expiry / 365.0
        sigma_sqrt_t = annualized_volatility * math.sqrt(t_years)
        d2 = (math.log(spot_price / strike_price) + (risk_free_rate - 0.5 * (annualized_volatility ** 2)) * t_years) / sigma_sqrt_t

        if is_barrier:
            raw_prob = 2.0 * self._norm_cdf(-d2 if is_below else d2)
        else:
            raw_prob = self._norm_cdf(-d2 if is_below else d2)

        return round(max(0.01, min(0.99, raw_prob)), 4)

    @classmethod
    def _is_range_contract(cls, question: str, group_item: str = "") -> bool:
        combined = f"{question} {group_item}"
        if cls.RANGE_RE.search(combined):
            return True
        if len(cls.STRIKE_RE.findall(question or "")) >= 2:
            return True
        return False

    @classmethod
    def _extract_strike_usd(cls, text: str) -> Optional[float]:
        match = cls.STRIKE_RE.search(text or "")
        if not match:
            return None
        num = float(match.group(1).replace(",", ""))
        suffix = (match.group(2) or "").lower()
        if suffix == "k":
            num *= 1000.0
        elif suffix == "m":
            num *= 1_000_000.0
        return num

    @staticmethod
    def _parse_yes_probability(market: Dict[str, Any]) -> Optional[float]:
        outcomes = market.get("outcomes")
        prices = market.get("outcomePrices")
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except Exception:
                outcomes = None
        if isinstance(prices, str):
            try:
                prices = json.loads(prices)
            except Exception:
                prices = None
        if not isinstance(outcomes, list) or not isinstance(prices, list) or len(outcomes) != len(prices):
            return None
        for outcome_label, raw_price in zip(outcomes, prices):
            if str(outcome_label).strip().lower() == "yes":
                try:
                    prob = float(raw_price)
                    if 0.005 < prob < 0.995:
                        return prob
                except (ValueError, TypeError):
                    return None
        return None

    def _classify_contract(
        self,
        question: str,
        event_title: str,
        group_item: str,
        spot: float,
        strike: float,
    ) -> Tuple[bool, bool]:
        """Determines (is_barrier, is_below) for a Polymarket binary contract."""
        q_low = (question or "").lower()
        title_low = (event_title or "").lower()

        has_barrier_word = any(re.search(rf"\b{tok}\b", q_low) for tok in self.BARRIER_KEYWORDS)
        has_euro_word = any(tok in q_low for tok in self.EUROPEAN_KEYWORDS)
        is_barrier = has_barrier_word or (
            any(re.search(rf"\b{tok}\b", title_low) for tok in self.BARRIER_KEYWORDS) and not has_euro_word
        )

        explicit_down = any(tok in q_low for tok in self.DOWNWARD_KEYWORDS) or ("↓" in group_item)
        explicit_up = any(tok in q_low for tok in self.UPWARD_KEYWORDS) or ("↑" in group_item)

        if explicit_down and not explicit_up:
            is_below = True
        elif explicit_up and not explicit_down:
            is_below = False
        elif is_barrier and strike < spot:
            is_below = True
        else:
            is_below = False

        return is_barrier, is_below

    def _evaluate_live_polymarket(
        self,
        clean_asset: str,
        spot: float,
        vol: float,
        vol_source: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        aliases = self.ASSET_ALIASES.get(clean_asset, (clean_asset.lower(),))
        events = self.feed.fetch_polymarket_events(limit=100)
        now = datetime.now(timezone.utc)
        scored: List[Dict[str, Any]] = []

        for event in events:
            event_title = str(event.get("title") or "")
            event_slug = str(event.get("slug") or "")
            markets = event.get("markets") or []
            for mkt in markets:
                question = str(mkt.get("question") or mkt.get("groupItemTitle") or event_title)
                group_item = str(mkt.get("groupItemTitle") or "")
                haystack = f"{event_title} {event_slug} {question}".lower()
                if not any(re.search(rf"\b{re.escape(alias)}\b", haystack) for alias in aliases):
                    continue

                if self._is_range_contract(question, group_item):
                    continue

                strike = self._extract_strike_usd(question)
                if not strike or strike < spot * 0.15 or strike > spot * 5.0:
                    continue

                poly_yes = self._parse_yes_probability(mkt)
                if poly_yes is None:
                    continue

                end_str = mkt.get("endDate") or event.get("endDate")
                days_to_expiry = 30.0
                if end_str:
                    try:
                        end_dt = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
                        delta_days = (end_dt - now).total_seconds() / 86400.0
                        if delta_days <= 0.1:
                            continue
                        days_to_expiry = round(delta_days, 2)
                    except ValueError:
                        pass

                is_barrier, is_below = self._classify_contract(question, event_title, group_item, spot, strike)
                model_prob = self.calculate_spot_implied_probability(
                    spot_price=spot,
                    strike_price=strike,
                    days_to_expiry=days_to_expiry,
                    annualized_volatility=vol,
                    is_barrier=is_barrier,
                    is_below=is_below,
                )
                edge = round((model_prob - poly_yes) * 10000.0, 1)
                vol_24h = float(mkt.get("volume24hr") or mkt.get("volumeNum") or event.get("volume24hr") or 0.0)

                if edge > 300:
                    signal = "BUY_YES_UNDERVALUED"
                elif edge < -300:
                    signal = "BUY_NO_OVERVALUED"
                else:
                    signal = "FAIR_VALUE"

                scored.append({
                    "market_title": question,
                    "market_slug": mkt.get("slug") or event_slug,
                    "polymarket_url": f"https://polymarket.com/event/{event_slug}" if event_slug else None,
                    "contract_type": "one_touch_barrier" if is_barrier else "european_expiry",
                    "direction": "BELOW_STRIKE" if is_below else "ABOVE_STRIKE",
                    "target_strike_usd": round(strike, 2),
                    "days_to_expiry": days_to_expiry,
                    "annualized_vol_used": vol,
                    "vol_source": vol_source,
                    "polymarket_consensus_prob": round(poly_yes, 4),
                    "spot_implied_prob": model_prob,
                    "arbitrage_edge_bps": edge,
                    "mispricing_pct": round(edge / 100.0, 2),
                    "volume_24hr_usd": round(vol_24h, 2),
                    "signal": signal,
                })

        scored.sort(key=lambda item: (abs(item["arbitrage_edge_bps"]), item["volume_24hr_usd"]), reverse=True)
        return scored[:limit]

    def scan_prediction_arbitrage(self, asset: str = "BTC", limit: int = 5) -> Dict[str, Any]:
        """
        Scans live binary Polymarket contracts vs live spot + Deribit DVOL / 30d realized volatility pricing.
        """
        start_t = time.time()
        ok, clean_input = _validate_symbol(asset)
        if not ok:
            return {
                "status": "error",
                "error": "invalid_symbol",
                "message": "asset must match ^[A-Z0-9/_-]{2,20}$",
            }
        clean_asset, _ = _PublicMarketFeed.split_symbol(clean_input)
        symbol = f"{clean_asset}/USDT"
        providers_tried: List[str] = []

        try:
            spot, spot_src = self.feed.fetch_spot_price(symbol)
            providers_tried.append(str(spot_src))
        except Exception as exc:
            return _upstream_unavailable(
                providers_tried=["coinbase_exchange", "kraken", "deribit_index", "coingecko", "binance_vision"],
                detail=f"Failed to fetch live spot price for {symbol}: {exc}",
                extra={"asset": clean_asset, "latency_ms": int((time.time() - start_t) * 1000)},
            )

        vol_used: Optional[float] = None
        vol_source = "realized_vol_30d"
        if isinstance(self.feed, _PublicMarketFeed):
            dvol = self.feed.fetch_deribit_dvol(clean_asset)
            if isinstance(dvol, float) and dvol > 0:
                vol_used = dvol
                vol_source = f"{clean_asset}_DVOL"
                providers_tried.append("deribit_dvol")

        if vol_used is None:
            try:
                vol_used = float(self.feed.fetch_realized_volatility(symbol, lookback_days=30))
                vol_source = "realized_vol_30d"
                providers_tried.append("realized_vol_klines")
            except Exception as exc:
                return _upstream_unavailable(
                    providers_tried=providers_tried + ["coinbase_candles", "kraken_ohlc", "binance_vision_klines"],
                    detail=f"Failed to fetch live implied or realized volatility for {symbol}: {exc}",
                    extra={"asset": clean_asset, "latency_ms": int((time.time() - start_t) * 1000)},
                )

        try:
            opportunities = self._evaluate_live_polymarket(
                clean_asset,
                spot,
                vol_used,
                vol_source,
                limit=max(1, int(limit)),
            )
        except Exception as exc:
            return _upstream_unavailable(
                providers_tried=providers_tried + ["polymarket_gamma"],
                detail=f"Failed to fetch live Polymarket Gamma markets: {exc}",
                extra={"asset": clean_asset, "latency_ms": int((time.time() - start_t) * 1000)},
            )

        latency_ms = int((time.time() - start_t) * 1000)
        return {
            "status": "success",
            "data_source": "live_polymarket_gamma",
            "spot_venue": spot_src,
            "vol_source": vol_source,
            "model_basis": "black_scholes_barrier_and_european",
            "asset": clean_asset,
            "benchmark_spot_price": round(spot, 2),
            "annualized_vol_used": vol_used,
            "annualized_realized_vol_30d": vol_used,
            "timestamp_ms": int(time.time() * 1000),
            "opportunities_analyzed": len(opportunities),
            "market_discrepancies": opportunities,
            "tokens_saved_estimate": 35000,
            "latency_ms": latency_ms,
            "disclaimer": "Quantitative probability discrepancy telemetry. Descriptive statistical model, not financial advice."
        }
