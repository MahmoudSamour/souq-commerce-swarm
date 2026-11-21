"""
SOUQ // Koyeb Production Edge Server
Unified ASGI server running on Koyeb:
- Serves the Web Storefront to humans at '/'
- Serves Machine Registries at '/.well-known/mcp.json', '/.well-known/agent-card.json', '/llms.txt', '/openapi.json'
- Serves Streamable HTTP MCP JSON-RPC 2.0 at '/mcp'
- Serves Paid x402 Base USDC, Prepaid X-API-Key, & Polar MoR Commerce Endpoints
"""

import os
import sys
import json
import time
import math
import hmac
import base64
import ipaddress
import threading
import urllib.parse
from collections import OrderedDict
from functools import partial
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import anyio
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse, Response
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Ensure project root is on path & load environment
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, "config", ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MAX_PAYLOAD_BYTES = int(os.getenv("SOUQ_MAX_PAYLOAD_BYTES", "1048576"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("SOUQ_RATE_LIMIT_PER_MINUTE", "120"))
DB_PATH = os.getenv("SOUQ_DUCKDB_PATH", os.path.join(PROJECT_ROOT, "data", "souq_treasury_lake.duckdb"))
RECEIPTS_DIR = os.getenv("SOUQ_RECEIPTS_DIR", os.path.join(PROJECT_ROOT, "data", "receipts"))
_SERVER_START_TS = time.time()

from agents.analytics.traffic_telemetry import TrafficTelemetryEngine
from agents.analytics.negotiation_tracker import NegotiationTracker
from agents.treasury.db_backend import resolve_db_target, db_transaction, ensure_parent_dir
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.treasury.api_key_ledger import APIKeyLedger
from agents.treasury.x402_gateway import X402PaymentGateway, _get_tx_lock
from agents.treasury.polar_adapter import PolarAdapter, POLAR_PRODUCTS
from agents.treasury.marketplace_registry import MarketplaceRegistry

DB_TARGET, _IS_POSTGRES = resolve_db_target(DB_PATH)
if not _IS_POSTGRES:
    ensure_parent_dir(DB_TARGET)

telemetry_engine = TrafficTelemetryEngine(db_path=DB_TARGET)
negotiation_tracker = NegotiationTracker(db_path=DB_TARGET)
receipt_engine = CryptoReceiptEngine(db_path=DB_TARGET, receipts_dir=RECEIPTS_DIR)
api_key_ledger = APIKeyLedger(db_path=DB_TARGET)
marketplace_registry = MarketplaceRegistry(db_path=DB_TARGET)
payment_gw = X402PaymentGateway(
    receipt_engine=receipt_engine,
    negotiation_tracker=negotiation_tracker,
    api_key_ledger=api_key_ledger,
)
polar_adapter = PolarAdapter(api_key_ledger=api_key_ledger)

# Bounded LRU sliding-window rate-limiter keyed by hashed IP (never stores raw IP)
_MAX_RATE_LIMIT_ENTRIES = int(os.getenv("SOUQ_MAX_RATE_LIMIT_ENTRIES", "10000"))
_ip_request_history: "OrderedDict[str, list]" = OrderedDict()
_rate_limit_lock = threading.Lock()

# Explicit trusted reverse-proxy CIDRs (avoids Python 3.11 .is_private TEST-NET quirks)
_TRUSTED_PROXY_NETWORKS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
)

_CSP_HEADER = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self' https:"
)

_HEALTH_PROBE_UA_MARKERS = (
    "kube-probe",
    "koyeb",
    "health",
    "uptime",
    "probe",
    "monitor",
    "testclient",
    "go-http-client",
    "elb-healthchecker",
)


def _init_server_tables() -> None:
    """Initializes server-owned persistence tables (DB-backed daily free-trial ledger)."""
    with db_transaction(DB_TARGET) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS free_trial_usage (
                ip_hash TEXT PRIMARY KEY,
                last_used_ts DOUBLE,
                calls_today INTEGER DEFAULT 0,
                window_start_ts DOUBLE
            )
            """
        )
        con.execute("ALTER TABLE free_trial_usage ADD COLUMN IF NOT EXISTS calls_today INTEGER DEFAULT 0")
        con.execute("ALTER TABLE free_trial_usage ADD COLUMN IF NOT EXISTS window_start_ts DOUBLE")


_init_server_tables()


def _parse_ip_literal(raw: str) -> Optional[str]:
    """Parses and canonicalizes an IPv4/IPv6 string; returns None if malformed."""
    val = (raw or "").strip()
    if not val:
        return None
    if val.startswith("[") and val.endswith("]"):
        val = val[1:-1].strip()
    if "%" in val:
        val = val.split("%", 1)[0].strip()
    try:
        return str(ipaddress.ip_address(val))
    except ValueError:
        return None


def _get_configured_trusted_proxies() -> list:
    raw = os.getenv("SOUQ_TRUSTED_PROXY_IPS", "")
    nets = []
    for item in raw.split(","):
        token = item.strip()
        if not token:
            continue
        try:
            nets.append(ipaddress.ip_network(token, strict=False))
        except ValueError:
            continue
    return nets


def _is_trusted_proxy(host: str) -> bool:
    """Returns True only if direct peer host is loopback, RFC1918, testclient, or explicitly trusted."""
    candidate = (host or "").strip()
    if not candidate:
        return False
    if candidate.lower() == "testclient":
        return True
    parsed_str = _parse_ip_literal(candidate)
    if not parsed_str:
        return False
    addr = ipaddress.ip_address(parsed_str)
    check_addrs = [addr]
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        check_addrs.append(addr.ipv4_mapped)

    for a in check_addrs:
        if any(a in net for net in _TRUSTED_PROXY_NETWORKS):
            return True
        if any(a in net for net in _get_configured_trusted_proxies()):
            return True
    return False


def _extract_client_ip(request) -> str:
    """
    Extracts true caller IP, trusting proxy headers ONLY when the direct socket peer
    is a verified reverse proxy (loopback, RFC1918, testclient, or SOUQ_TRUSTED_PROXY_IPS)
    and SOUQ_TRUST_PROXY_HEADERS is enabled.
    """
    peer_host = request.client.host if request.client and request.client.host else ""
    trust_headers = os.getenv("SOUQ_TRUST_PROXY_HEADERS", "true").strip().lower() == "true"
    if not trust_headers or not _is_trusted_proxy(peer_host):
        return _parse_ip_literal(peer_host) or (peer_host or "unknown")

    cf_ip = _parse_ip_literal(request.headers.get("CF-Connecting-IP") or "")
    xff = (request.headers.get("X-Forwarded-For") or "").strip()
    if cf_ip and not xff:
        return cf_ip

    if xff:
        hops = [_parse_ip_literal(part) for part in xff.split(",")]
        valid_hops = [h for h in hops if h]
        if valid_hops:
            for hop in reversed(valid_hops):
                if not _is_trusted_proxy(hop):
                    return hop
            if cf_ip:
                return cf_ip
            return valid_hops[0]

    if cf_ip:
        return cf_ip

    real_ip = _parse_ip_literal(request.headers.get("X-Real-IP") or "")
    if real_ip:
        return real_ip
    return _parse_ip_literal(peer_host) or (peer_host or "unknown")


def _apply_security_headers(response: Response) -> Response:
    """Applies baseline HTTP security headers cleanly to every edge response."""
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = _CSP_HEADER
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


_SKIP_TELEMETRY_PATHS = frozenset({
    "/favicon.ico",
    "/robots.txt",
    "/sitemap.xml",
    "/souq-agent-commerce-index-key-2026.txt",
})


def _should_skip_telemetry(path: str, user_agent: str) -> bool:
    """Suppresses noisy infrastructure / health probe & static crawler logs without hiding real AI agent visits."""
    if path in _SKIP_TELEMETRY_PATHS:
        return True
    if path != "/health":
        return False
    ua_lower = (user_agent or "").strip().lower()
    if not ua_lower or any(marker in ua_lower for marker in _HEALTH_PROBE_UA_MARKERS):
        return True
    category = telemetry_engine.categorize_user_agent(user_agent, endpoint=path)
    return category in ("UNKNOWN", "CLI_TOOL")


class TrafficTelemetryMiddleware(BaseHTTPMiddleware):
    """
    Real-time HTTP traffic and agent interaction logger.
    Captures human, bot, and autonomous agent interactions off the ASGI event loop.
    """

    async def dispatch(self, request, call_next):
        start_time = time.time()
        client_ip = _extract_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        method = request.method
        path = request.url.path

        response = await call_next(request)

        if _should_skip_telemetry(path, user_agent):
            return response

        duration_ms = max(1, int((time.time() - start_time) * 1000))
        tool_name = response.headers.get("X-Souq-Tool")
        billing_status = response.headers.get("X-Souq-Billing")

        await anyio.to_thread.run_sync(
            partial(
                telemetry_engine.record_request,
                method=method,
                endpoint=path,
                status_code=response.status_code,
                client_ip=client_ip,
                user_agent=user_agent,
                tool_name=tool_name,
                billing_status=billing_status,
                duration_ms=duration_ms,
            )
        )

        return response


class SecurityHeadersAndProtectionMiddleware(BaseHTTPMiddleware):
    """
    Production Security Shield (OUTERMOST middleware):
    - Enforces CSP, HSTS, Anti-Clickjacking, and Anti-MIME sniffing headers
    - Throttles abusive DDoS requests using a bounded LRU keyed by IP hash
    - Enforces streaming MAX_PAYLOAD_BYTES cap even without Content-Length
    """

    async def dispatch(self, request, call_next):
        client_ip = _extract_client_ip(request)
        ip_hash = telemetry_engine.hash_ip(client_ip)
        now = time.time()

        with _rate_limit_lock:
            existing = _ip_request_history.get(ip_hash, [])
            history = [t for t in existing if now - t < 60]
            if len(history) >= RATE_LIMIT_PER_MINUTE:
                _ip_request_history[ip_hash] = history
                _ip_request_history.move_to_end(ip_hash)
                return _apply_security_headers(
                    JSONResponse(
                        {"error": "Too Many Requests", "message": "Rate limit exceeded. Please throttle automated calls."},
                        status_code=429,
                        headers={"Retry-After": "60"},
                    )
                )
            history.append(now)
            _ip_request_history[ip_hash] = history
            _ip_request_history.move_to_end(ip_hash)
            while len(_ip_request_history) > _MAX_RATE_LIMIT_ENTRIES:
                _ip_request_history.popitem(last=False)

        content_length = request.headers.get("Content-Length")
        if content_length is not None:
            try:
                parsed_len = int(content_length)
                if parsed_len < 0:
                    return _apply_security_headers(
                        JSONResponse({"error": "Invalid Content-Length", "code": "invalid_content_length"}, status_code=400)
                    )
                if parsed_len > MAX_PAYLOAD_BYTES:
                    return _apply_security_headers(
                        JSONResponse(
                            {
                                "error": "Payload Too Large",
                                "code": "payload_too_large",
                                "max_allowed_bytes": MAX_PAYLOAD_BYTES,
                            },
                            status_code=413,
                        )
                    )
            except ValueError:
                return _apply_security_headers(
                    JSONResponse({"error": "Invalid Content-Length", "code": "invalid_content_length"}, status_code=400)
                )

        if request.method in ("POST", "PUT", "PATCH"):
            if hasattr(request, "_body"):
                if len(getattr(request, "_body") or b"") > MAX_PAYLOAD_BYTES:
                    return _apply_security_headers(
                        JSONResponse(
                            {
                                "error": "Payload Too Large",
                                "code": "payload_too_large",
                                "max_allowed_bytes": MAX_PAYLOAD_BYTES,
                            },
                            status_code=413,
                        )
                    )
            else:
                chunks = []
                total_bytes = 0
                async for chunk in request.stream():
                    if not chunk:
                        continue
                    total_bytes += len(chunk)
                    if total_bytes > MAX_PAYLOAD_BYTES:
                        return _apply_security_headers(
                            JSONResponse(
                                {
                                    "error": "Payload Too Large",
                                    "code": "payload_too_large",
                                    "max_allowed_bytes": MAX_PAYLOAD_BYTES,
                                },
                                status_code=413,
                            )
                        )
                    chunks.append(chunk)
                request._body = b"".join(chunks)

        response = await call_next(request)
        return _apply_security_headers(response)


from agents.production.mcp_tool_builder import (
    MarketMicrostructureEngine,
    ASTSecurityScanner,
    SyntheticSchemaVerifier,
    CrossExchangeArbitrageScanner,
    OrderBookSlippageSimulator,
    SmartMoneyWhaleRadar,
    PredictionMarketArbitrageRadar,
)
from agents.production.token_compressor import TokenContextCompressor, CodeASTSlicer
from agents.production.dev_intelligence_vault import DevAPICheatSheetVault, DailyTechTrendsRadar
from agents.production.cyber_threat_intelligence import CyberThreatIntelligenceRadar
from agents.production.cyber_defense_vault import (
    PromptInjectionFirewall,
    SmartContractHoneypotRadar,
    SecretLeakScanner,
    DeepASTVulnerabilityAuditor,
    APIAttackSurfaceScanner,
)

# Initialize Production Analytical Engines
micro_engine = MarketMicrostructureEngine()
security_scanner = ASTSecurityScanner()
schema_verifier = SyntheticSchemaVerifier()
arbitrage_scanner = CrossExchangeArbitrageScanner()
slippage_simulator = OrderBookSlippageSimulator()
whale_radar = SmartMoneyWhaleRadar()
prediction_radar = PredictionMarketArbitrageRadar()
token_compressor = TokenContextCompressor()
ast_slicer = CodeASTSlicer()
dev_vault = DevAPICheatSheetVault()
trends_radar = DailyTechTrendsRadar()
threat_radar = CyberThreatIntelligenceRadar()
prompt_firewall = PromptInjectionFirewall()
honeypot_radar = SmartContractHoneypotRadar()
secret_scanner = SecretLeakScanner()
deep_ast_auditor = DeepASTVulnerabilityAuditor()
api_surface_scanner = APIAttackSurfaceScanner()


TOOL_ECONOMICS = {
    "prediction_market_arbitrage_radar": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 35000,
        "est_inference_savings_usd": 0.175,
        "net_roi_pct": 483,
        "category": "Prediction Market Arbitrage",
    },
    "token_context_compressor": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 14000,
        "est_inference_savings_usd": 0.070,
        "net_roi_pct": 600,
        "category": "Context Optimization",
    },
    "ast_structural_slicer": {
        "price_usdc": 0.02,
        "avg_tokens_saved": 3000,
        "est_inference_savings_usd": 0.015,
        "net_roi_pct": 75,
        "category": "Code Slicing",
    },
    "quant_microstructure_radar": {
        "price_usdc": 0.02,
        "avg_tokens_saved": 15000,
        "est_inference_savings_usd": 0.075,
        "net_roi_pct": 275,
        "category": "Alpha & Microstructure",
    },
    "cross_exchange_arbitrage_scanner": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 12000,
        "est_inference_savings_usd": 0.060,
        "net_roi_pct": 100,
        "category": "Arbitrage & Basis",
    },
    "orderbook_slippage_simulator": {
        "price_usdc": 0.02,
        "avg_tokens_saved": 15000,
        "est_inference_savings_usd": 0.075,
        "net_roi_pct": 275,
        "category": "Execution Optimization",
    },
    "smart_money_whale_flow_radar": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 20000,
        "est_inference_savings_usd": 0.100,
        "net_roi_pct": 233,
        "category": "Whale Flow Telemetry",
    },
    "dev_api_cheatsheet_vault": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 40000,
        "est_inference_savings_usd": 0.200,
        "net_roi_pct": 1900,
        "category": "API Schema Reference",
    },
    "daily_tech_ai_trends_radar": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 25000,
        "est_inference_savings_usd": 0.125,
        "net_roi_pct": 1150,
        "category": "AI Technology Radar",
    },
    "ast_security_scanner": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 4000,
        "est_inference_savings_usd": 0.020,
        "net_roi_pct": 67,
        "category": "Security Linting",
    },
    "synthetic_schema_verifier": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 1500,
        "est_inference_savings_usd": 0.008,
        "net_roi_pct": 80,
        "category": "Schema Conformity",
    },
    "prompt_injection_firewall": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 10000,
        "est_inference_savings_usd": 0.050,
        "net_roi_pct": 400,
        "category": "Adversarial Prompt Defense",
    },
    "smart_contract_honeypot_radar": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 25000,
        "est_inference_savings_usd": 0.125,
        "net_roi_pct": 316,
        "category": "Smart Contract & Token Security",
    },
    "secret_leak_scanner": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 15000,
        "est_inference_savings_usd": 0.075,
        "net_roi_pct": 650,
        "category": "Credential & Key Leak Prevention",
    },
    "deep_ast_vulnerability_auditor": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 15000,
        "est_inference_savings_usd": 0.075,
        "net_roi_pct": 150,
        "category": "Static AST Code Security",
    },
    "api_attack_surface_scanner": {
        "price_usdc": 0.02,
        "avg_tokens_saved": 12000,
        "est_inference_savings_usd": 0.060,
        "net_roi_pct": 200,
        "category": "API Attack Surface & Defense Headers",
    },
}

MCP_TOOLS_SCHEMA = [
    {
        "name": "souq_account_status",
        "description": "Free discovery & balance check: inspects current prepaid SOUQ API key credits, Base USDC payment wallet, and available tools.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "token_context_compressor",
        "description": "Compresses bloated HTML, JSON objects/arrays, code, logs, or markdown by 60-95% while preserving entities ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_content": {"type": "string", "description": "Raw HTML, JSON, code, log, or markdown text to compress"},
                "max_compression": {"type": "boolean", "default": True},
                "mode": {
                    "type": "string",
                    "enum": ["auto", "html", "json", "code", "log", "logs", "markdown", "prose"],
                    "default": "auto",
                },
                "target_ratio": {"type": "number", "description": "Optional target compression ratio in (0.05, 0.95)"},
            },
            "required": ["raw_content"],
        },
    },
    {
        "name": "ast_structural_slicer",
        "description": "Surgically extracts a single AST function or class from Python source code ($0.02 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_code": {"type": "string"},
                "target_symbol": {"type": "string"},
            },
            "required": ["source_code", "target_symbol"],
        },
    },
    {
        "name": "quant_microstructure_radar",
        "description": "Live order book depth, spread bps, Order Book Imbalance (OBI), and cascade risk score ($0.02 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "default": "BTC/USDT"}},
        },
    },
    {
        "name": "cross_exchange_arbitrage_scanner",
        "description": "Scans Spot vs Perpetual Futures basis spreads and annualized delta-neutral funding APR ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "default": "BTC/USDT"}},
        },
    },
    {
        "name": "orderbook_slippage_simulator",
        "description": "Walks 100 levels of live order book depth to compute expected VWAP, slippage bps, and impact ($0.02 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "default": "BTC/USDT"},
                "side": {"type": "string", "enum": ["BUY", "SELL"], "default": "BUY"},
                "trade_size_usd": {"type": "number", "default": 10000.0},
            },
        },
    },
    {
        "name": "smart_money_whale_flow_radar",
        "description": "Aggregates large block trades and limit walls to calculate Whale Accumulation Index ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "default": "BTC/USDT"},
                "block_threshold_usd": {"type": "number", "default": 50000.0},
            },
        },
    },
    {
        "name": "prediction_market_arbitrage_radar",
        "description": "Compares live Polymarket crypto markets against 30d realized-volatility Black-Scholes probabilities ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "default": "BTC"},
                "limit": {"type": "integer", "default": 5},
            },
        },
    },
    {
        "name": "dev_api_cheatsheet_vault",
        "description": "High-density API schemas & snippets for openai, anthropic, stripe, base_evm, fastmcp, mcp, duckdb ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ecosystem": {"type": "string", "enum": ["openai", "anthropic", "stripe", "base_evm", "fastmcp", "mcp", "duckdb"], "default": "openai"},
            },
        },
    },
    {
        "name": "daily_tech_ai_trends_radar",
        "description": "Live AI technology radar from GitHub AI repos, HackerNews top stories, and arXiv cs.AI/cs.CL ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {"force_refresh": {"type": "boolean", "default": False}},
        },
    },
    {
        "name": "ast_security_scanner",
        "description": "Python AST code security linter (compatibility alias for deep_ast_vulnerability_auditor) ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {"source_code": {"type": "string"}},
            "required": ["source_code"],
        },
    },
    {
        "name": "synthetic_schema_verifier",
        "description": "Validates JSON payloads against expected type schemas with zero hallucinations ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {"data": {"type": "object"}, "schema": {"type": "object"}},
            "required": ["data", "schema"],
        },
    },
    {
        "name": "prompt_injection_firewall",
        "description": "Detects prompt injection, DAN jailbreaks, and system prompt exfiltration attacks ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "strict_mode": {"type": "boolean", "default": False},
            },
            "required": ["text"],
        },
    },
    {
        "name": "smart_contract_honeypot_radar",
        "description": "Audits Solidity source OR live Base contract addresses for honeypots, hidden mints, and reentrancy ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_code": {"type": "string", "default": ""},
                "contract_address": {"type": "string", "description": "Optional Base 0x... contract address for live bytecode & Blockscout source inspection"},
                "token_symbol": {"type": "string", "default": "TKN"},
            },
        },
    },
    {
        "name": "secret_leak_scanner",
        "description": "High-entropy credential scanner catching AWS, OpenAI, Anthropic, and EVM private keys ($0.01 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "entropy_threshold": {"type": "number", "default": 4.2},
            },
            "required": ["content"],
        },
    },
    {
        "name": "deep_ast_vulnerability_auditor",
        "description": "Deep Python AST vulnerability scanner detecting SQLi, SSRF, YAML/pickle RCE ($0.03 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {"source_code": {"type": "string"}},
            "required": ["source_code"],
        },
    },
    {
        "name": "api_attack_surface_scanner",
        "description": "Audits live HTTPS endpoints for security headers, CORS misconfiguration, and exposure ($0.02 USDC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_url": {"type": "string"},
                "headers_to_check": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Optional header map (name -> value) for offline header inspection",
                },
            },
            "required": ["target_url"],
        },
    },
]


def _extract_payment_credentials(request, body: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Extracts (api_key, payment_tx) from standard headers and request body."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token.startswith("souq_"):
                api_key = token
    if not api_key and isinstance(body.get("api_key"), str):
        api_key = body["api_key"].strip() or None

    raw_payment = (
        request.headers.get("X-Payment-Tx")
        or request.headers.get("X-Payment")
        or request.headers.get("PAYMENT-SIGNATURE")
        or body.get("payment_tx_hash")
        or body.get("tx_hash")
    )
    payment_tx: Optional[str] = None
    if isinstance(raw_payment, str) and raw_payment.strip():
        candidate = raw_payment.strip()
        if candidate.startswith("{"):
            try:
                parsed = json.loads(candidate)
                candidate = parsed.get("tx_hash") or parsed.get("payment_tx_hash") or candidate
            except Exception:
                pass
        elif not candidate.startswith("0x") and len(candidate) > 20:
            try:
                decoded = json.loads(base64.b64decode(candidate).decode("utf-8"))
                candidate = decoded.get("tx_hash") or decoded.get("payload", {}).get("txHash") or candidate
            except Exception:
                pass
        payment_tx = candidate.strip()

    return (api_key.strip() if api_key else None), payment_tx


_CLIENT_VALIDATION_ERRORS = frozenset({
    "invalid_symbol",
    "invalid_side",
    "invalid_trade_size",
    "ssrf_blocked_or_unresolvable_host",
    "ssrf_blocked",
    "invalid_url",
    "missing_required_parameter",
    "missing_raw_content",
    "invalid_parameter",
    "invalid_target_ratio",
    "unknown_ecosystem",
})


def _err(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    return {"status": "error", "error": code, "message": message, **extra}


def _require_str(
    body: Dict[str, Any],
    *keys: str,
    err_code: str = "missing_required_parameter",
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    for key in keys:
        if key in body and body[key] is not None:
            val = body[key]
            if not isinstance(val, str):
                return None, _err("invalid_parameter", f"Parameter '{key}' must be a string.")
            if not val.strip():
                return None, _err(err_code, f"Parameter '{key}' must be a non-empty string.")
            return val, None
    return None, _err(err_code, f"Required parameter '{keys[0]}' is missing.")


def _parse_float_param(body: Dict[str, Any], key: str, default: float) -> Tuple[float, Optional[Dict[str, Any]]]:
    if key not in body or body[key] is None:
        return default, None
    raw = body[key]
    if isinstance(raw, bool):
        return default, _err("invalid_parameter", f"Parameter '{key}' must be numeric.")
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return default, _err("invalid_parameter", f"Parameter '{key}' must be numeric.")
    if not math.isfinite(val):
        return default, _err("invalid_parameter", f"Parameter '{key}' must be finite.")
    return val, None


def _parse_int_param(body: Dict[str, Any], key: str, default: int) -> Tuple[int, Optional[Dict[str, Any]]]:
    if key not in body or body[key] is None:
        return default, None
    raw = body[key]
    if isinstance(raw, bool):
        return default, _err("invalid_parameter", f"Parameter '{key}' must be an integer.")
    try:
        return int(raw), None
    except (TypeError, ValueError):
        return default, _err("invalid_parameter", f"Parameter '{key}' must be an integer.")


def _is_dispatch_failure(res: Any) -> bool:
    if not isinstance(res, dict):
        return True
    status = res.get("status")
    if status in ("error", "upstream_unavailable"):
        return True
    if "error" in res and "status" not in res:
        return True
    return False


def _failure_http_status(res: Any) -> int:
    if not isinstance(res, dict):
        return 503
    if res.get("status") == "upstream_unavailable" or res.get("error") == "upstream_unavailable":
        return 503
    err_code = res.get("error")
    if err_code in _CLIENT_VALIDATION_ERRORS or res.get("status") == "error":
        return 400
    return 503


def _is_prod_environment() -> bool:
    return (
        os.getenv("ENV", "").strip().lower() == "production"
        or os.getenv("SOUQ_ENV", "").strip().lower() == "production"
        or bool(os.getenv("KOYEB_APP_ID", "").strip())
    )


def _is_test_simulation_allowed() -> bool:
    if _is_prod_environment():
        return False
    if os.getenv("SOUQ_ALLOW_SIMULATED_TOPUP", "true").strip().lower() == "false":
        return False
    return os.getenv("SOUQ_ALLOW_TEST_SIMULATION", "false").strip().lower() == "true"


def _get_free_trial_daily_limit() -> int:
    try:
        return max(1, int(os.getenv("SOUQ_FREE_TRIAL_DAILY_LIMIT", "5")))
    except (TypeError, ValueError):
        return 5


def _check_free_trial_eligible(ip_hash: str, now_ts: Optional[float] = None) -> bool:
    now = time.time() if now_ts is None else now_ts
    limit = _get_free_trial_daily_limit()
    with db_transaction(DB_TARGET, read_only=True) as con:
        row = con.execute(
            "SELECT last_used_ts, calls_today, window_start_ts FROM free_trial_usage WHERE ip_hash = ?",
            [ip_hash],
        ).fetchone()
    if not row or row[0] is None:
        return True
    window_start = float(row[2]) if row[2] is not None else float(row[0])
    if (now - window_start) >= 86400.0:
        return True
    calls_today = int(row[1]) if row[1] is not None else 1
    return calls_today < limit


def _consume_free_trial(ip_hash: str, now_ts: Optional[float] = None) -> Tuple[bool, int, int]:
    now = time.time() if now_ts is None else now_ts
    cutoff = now - 86400.0
    limit = _get_free_trial_daily_limit()
    with db_transaction(DB_TARGET) as con:
        row = con.execute(
            """
            INSERT INTO free_trial_usage (ip_hash, last_used_ts, calls_today, window_start_ts)
            VALUES (?, ?, 1, ?)
            ON CONFLICT (ip_hash) DO UPDATE
            SET last_used_ts = EXCLUDED.last_used_ts,
                calls_today = CASE
                    WHEN COALESCE(free_trial_usage.window_start_ts, free_trial_usage.last_used_ts, 0) <= ? THEN 1
                    ELSE COALESCE(free_trial_usage.calls_today, 1) + 1
                END,
                window_start_ts = CASE
                    WHEN COALESCE(free_trial_usage.window_start_ts, free_trial_usage.last_used_ts, 0) <= ? THEN EXCLUDED.window_start_ts
                    ELSE COALESCE(free_trial_usage.window_start_ts, free_trial_usage.last_used_ts)
                END
            WHERE COALESCE(free_trial_usage.window_start_ts, free_trial_usage.last_used_ts, 0) <= ?
               OR COALESCE(free_trial_usage.calls_today, 1) < ?
            RETURNING calls_today
            """,
            [ip_hash, now, now, cutoff, cutoff, cutoff, limit],
        ).fetchone()
    if not row:
        return False, limit, 0
    used = int(row[0])
    return True, limit, max(0, limit - used)


def _dispatch_tool(tool_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronously executes the requested analytical engine inside a worker thread."""
    if tool_name == "token_context_compressor":
        raw_content = None
        for key in ("raw_content", "content", "text"):
            if key in body and body[key] is not None:
                raw_content = body[key]
                break
        if raw_content is None or (isinstance(raw_content, str) and not raw_content.strip()):
            return _err("missing_raw_content", "Parameter 'raw_content' is required.")
        mode = body.get("mode", "auto")
        if not isinstance(mode, str) or not mode.strip():
            return _err("invalid_parameter", "Parameter 'mode' must be a non-empty string.")
        target_ratio = None
        if "target_ratio" in body and body["target_ratio"] is not None:
            parsed_ratio, ratio_err = _parse_float_param(body, "target_ratio", 0.5)
            if ratio_err:
                return ratio_err
            target_ratio = parsed_ratio
        return token_compressor.compress_text_or_json(
            raw_content,
            max_compression=bool(body.get("max_compression", True)),
            mode=mode,
            target_ratio=target_ratio,
        )

    if tool_name == "ast_structural_slicer":
        source_code, err = _require_str(body, "source_code")
        if err:
            return err
        target_symbol, err = _require_str(body, "target_symbol")
        if err:
            return err
        return ast_slicer.slice_symbol(source_code, target_symbol)

    if tool_name == "quant_microstructure_radar":
        symbol = body.get("symbol", "BTC/USDT")
        if not isinstance(symbol, str) or not symbol.strip():
            return _err("invalid_symbol", "Parameter 'symbol' must be a non-empty string.")
        return micro_engine.get_microstructure_metrics(symbol)

    if tool_name == "cross_exchange_arbitrage_scanner":
        symbol = body.get("symbol", "BTC/USDT")
        if not isinstance(symbol, str) or not symbol.strip():
            return _err("invalid_symbol", "Parameter 'symbol' must be a non-empty string.")
        return arbitrage_scanner.scan_arbitrage_and_funding(symbol)

    if tool_name == "orderbook_slippage_simulator":
        symbol = body.get("symbol", "BTC/USDT")
        if not isinstance(symbol, str) or not symbol.strip():
            return _err("invalid_symbol", "Parameter 'symbol' must be a non-empty string.")
        side = body.get("side", "BUY")
        if not isinstance(side, str):
            return _err("invalid_side", "Parameter 'side' must be 'BUY' or 'SELL'.")
        trade_size_usd, err = _parse_float_param(body, "trade_size_usd", 10000.0)
        if err:
            return err
        return slippage_simulator.simulate_slippage(
            symbol=symbol,
            side=side,
            trade_size_usd=trade_size_usd,
        )

    if tool_name == "smart_money_whale_flow_radar":
        symbol = body.get("symbol", "BTC/USDT")
        if not isinstance(symbol, str) or not symbol.strip():
            return _err("invalid_symbol", "Parameter 'symbol' must be a non-empty string.")
        block_threshold_usd, err = _parse_float_param(body, "block_threshold_usd", 50000.0)
        if err:
            return err
        return whale_radar.get_whale_flow_telemetry(
            symbol=symbol,
            block_threshold_usd=block_threshold_usd,
        )

    if tool_name == "dev_api_cheatsheet_vault":
        ecosystem = body.get("ecosystem", "openai")
        if not isinstance(ecosystem, str) or not ecosystem.strip():
            return _err("invalid_parameter", "Parameter 'ecosystem' must be a non-empty string.")
        return dev_vault.get_api_cheatsheet(ecosystem=ecosystem)

    if tool_name == "daily_tech_ai_trends_radar":
        return trends_radar.refresh_cache_and_get(force_refresh=bool(body.get("force_refresh", False)))

    if tool_name == "ast_security_scanner":
        source_code, err = _require_str(body, "source_code")
        if err:
            return err
        return security_scanner.scan_python_code(source_code)

    if tool_name == "synthetic_schema_verifier":
        if "data" not in body or "schema" not in body:
            return _err("missing_required_parameter", "Parameters 'data' and 'schema' are required.")
        if not isinstance(body["data"], dict) or not isinstance(body["schema"], dict):
            return _err("invalid_parameter", "Parameters 'data' and 'schema' must be JSON objects.")
        return schema_verifier.verify_schema_conformity(body["data"], body["schema"])

    if tool_name == "prediction_market_arbitrage_radar":
        asset = body.get("asset", body.get("symbol", "BTC"))
        if not isinstance(asset, str) or not asset.strip():
            return _err("invalid_parameter", "Parameter 'asset' must be a non-empty string.")
        limit, err = _parse_int_param(body, "limit", 5)
        if err:
            return err
        return prediction_radar.scan_prediction_arbitrage(asset=asset, limit=limit)

    if tool_name == "prompt_injection_firewall":
        text, err = _require_str(body, "text", "prompt")
        if err:
            return err
        return prompt_firewall.scan_prompt(
            text=text,
            strict_mode=bool(body.get("strict_mode", False)),
        )

    if tool_name == "smart_contract_honeypot_radar":
        source_code = body.get("source_code")
        contract_address = body.get("contract_address")
        if source_code is not None and not isinstance(source_code, str):
            return _err("invalid_parameter", "Parameter 'source_code' must be a string.")
        if contract_address is not None and not isinstance(contract_address, str):
            return _err("invalid_parameter", "Parameter 'contract_address' must be a string.")
        has_source = bool(source_code and source_code.strip())
        has_addr = bool(contract_address and contract_address.strip())
        if not has_source and not has_addr:
            return _err("missing_required_parameter", "Either 'source_code' or 'contract_address' is required.")
        token_symbol = body.get("token_symbol", body.get("symbol", "TKN"))
        if not isinstance(token_symbol, str) or not token_symbol.strip():
            return _err("invalid_parameter", "Parameter 'token_symbol' must be a non-empty string.")
        return honeypot_radar.audit_contract_code(
            source_code=source_code or "",
            token_symbol=token_symbol,
            contract_address=contract_address,
        )

    if tool_name == "secret_leak_scanner":
        content, err = _require_str(body, "content", "source_code", "text")
        if err:
            return err
        entropy_threshold, err = _parse_float_param(body, "entropy_threshold", 4.2)
        if err:
            return err
        return secret_scanner.scan_for_secrets(
            content=content,
            entropy_threshold=entropy_threshold,
        )

    if tool_name == "deep_ast_vulnerability_auditor":
        source_code, err = _require_str(body, "source_code")
        if err:
            return err
        return deep_ast_auditor.scan_code(source_code)

    if tool_name == "api_attack_surface_scanner":
        target_url, err = _require_str(body, "target_url", "url")
        if err:
            return err
        headers_to_check = body.get("headers_to_check")
        if headers_to_check is not None and (
            not isinstance(headers_to_check, dict)
            or not all(isinstance(k, str) and isinstance(v, str) for k, v in headers_to_check.items())
        ):
            return _err("invalid_parameter", "Parameter 'headers_to_check' must be an object mapping header names to strings.")
        res = api_surface_scanner.audit_url(
            target_url=target_url,
            headers_to_check=headers_to_check,
        )
        if isinstance(res, dict) and res.get("status") == "error" and "error" not in res:
            msg_lower = str(res.get("message", "")).lower()
            if (
                "ssrf" in msg_lower
                or "private" in msg_lower
                or "loopback" in msg_lower
                or "unresolvable" in msg_lower
                or "redirect" in msg_lower
            ):
                res["error"] = "ssrf_blocked_or_unresolvable_host"
            elif "failed to reach" in msg_lower or "timed out" in msg_lower or "timeout" in msg_lower:
                res["status"] = "upstream_unavailable"
                res["error"] = "upstream_unavailable"
            else:
                res["error"] = "invalid_url"
        return res

    if tool_name.startswith("ext_"):
        return marketplace_registry.execute_external_tool(tool_name, body)

    return _err("unknown_tool", f"Unknown tool '{tool_name}'")


async def _authorize_and_execute_tool(
    request,
    tool_name: str,
    body: Dict[str, Any],
) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
    """
    Unified authorization, billing, and execution pipeline shared by
    POST /api/tools/call and Streamable HTTP POST /mcp.
    Guarantees buyers are NEVER charged for tool errors, validation rejections, or outages.
    """
    call_start = time.time()
    is_external_tool = False
    ext_listing: Optional[Dict[str, Any]] = None
    if not tool_name or tool_name not in TOOL_ECONOMICS:
        if tool_name and tool_name.startswith("ext_"):
            ext_listing = await anyio.to_thread.run_sync(marketplace_registry.get_listing, tool_name)
            if ext_listing and ext_listing.get("status") == "ACTIVE":
                is_external_tool = True
        if not is_external_tool:
            return (
                404,
                {
                    "error": "Unknown tool",
                    "tool": tool_name,
                    "available_tools": list(TOOL_ECONOMICS.keys()),
                },
                {"X-Souq-Billing": "UNKNOWN_TOOL"},
            )

    if not isinstance(body, dict):
        return (
            400,
            _err("invalid_parameter", "Tool arguments must be a JSON object."),
            {"X-Souq-Tool": tool_name, "X-Souq-Billing": "INVALID_ARGS"},
        )

    if is_external_tool and ext_listing is not None:
        eco = {
            "price_usdc": float(ext_listing["price_usdc"]),
            "avg_tokens_saved": 5000,
            "est_inference_savings_usd": round(float(ext_listing["price_usdc"]) * 3.0, 4),
            "net_roi_pct": 200,
        }
    else:
        eco = TOOL_ECONOMICS[tool_name]
    price = eco["price_usdc"]
    user_agent = request.headers.get("User-Agent", "anonymous-agent")
    client_ip = _extract_client_ip(request)
    client_ip_hash = telemetry_engine.hash_ip(client_ip)
    api_key, payment_tx = _extract_payment_credentials(request, body)

    billing_header = "PAID_SETTLEMENT"
    extra_headers: Dict[str, str] = {}
    settlement: Dict[str, Any] = {}
    res: Dict[str, Any]

    # Priority 1: Prepaid X-API-Key Ledger (debit -> dispatch -> immediate refund on error/outage)
    if api_key:
        ok, settlement = await anyio.to_thread.run_sync(
            api_key_ledger.validate_and_debit, api_key, price, tool_name
        )
        if not ok:
            err_kind = settlement.get("error", "Invalid API Key")
            status_code = 402 if err_kind == "Insufficient Credits" else 401
            await anyio.to_thread.run_sync(
                partial(
                    negotiation_tracker.log_negotiation,
                    client_agent_id=user_agent[:64],
                    client_user_agent=user_agent,
                    tool_requested=tool_name,
                    initial_quote_usd=price,
                    settled_price_usd=None,
                    payment_protocol="prepaid_api_key",
                    outcome="INSUFFICIENT_CREDITS" if status_code == 402 else "INVALID_API_KEY",
                    latency_ms=max(1, int((time.time() - call_start) * 1000)),
                    rejection_reason=err_kind,
                    metadata={"client_ip_hash": client_ip_hash},
                )
            )
            payload = {**settlement, "topup_endpoint": "/api/credits/topup", "x402_recipient": payment_gw.recipient_wallet}
            return status_code, payload, {"X-Souq-Tool": tool_name, "X-Souq-Billing": "API_KEY_REJECTED"}

        try:
            res = await anyio.to_thread.run_sync(_dispatch_tool, tool_name, body)
        except Exception as exc:
            refund_ok, refund_info = await anyio.to_thread.run_sync(
                partial(api_key_ledger.refund_debit, api_key, price, reason=f"exception:{type(exc).__name__}")
            )
            await anyio.to_thread.run_sync(
                partial(
                    negotiation_tracker.log_negotiation,
                    client_agent_id=user_agent[:64],
                    client_user_agent=user_agent,
                    tool_requested=tool_name,
                    initial_quote_usd=price,
                    settled_price_usd=0.0,
                    payment_protocol="prepaid_api_key",
                    outcome="REFUNDED",
                    latency_ms=max(1, int((time.time() - call_start) * 1000)),
                    rejection_reason=f"Tool execution failed: {exc}",
                    metadata={"key_prefix": settlement.get("key_prefix"), "refund_ok": refund_ok},
                )
            )
            return (
                503,
                {
                    "status": "upstream_unavailable",
                    "error": "upstream_unavailable",
                    "message": "Tool execution failed; prepaid credit refunded.",
                    "refunded": bool(refund_ok),
                    "refund_receipt": refund_info,
                },
                {"X-Souq-Tool": tool_name, "X-Souq-Billing": "REFUNDED"},
            )

        if _is_dispatch_failure(res):
            err_reason = str(res.get("error") or res.get("status") or "tool_error") if isinstance(res, dict) else "tool_error"
            refund_ok, refund_info = await anyio.to_thread.run_sync(
                partial(api_key_ledger.refund_debit, api_key, price, reason=err_reason)
            )
            await anyio.to_thread.run_sync(
                partial(
                    negotiation_tracker.log_negotiation,
                    client_agent_id=user_agent[:64],
                    client_user_agent=user_agent,
                    tool_requested=tool_name,
                    initial_quote_usd=price,
                    settled_price_usd=0.0,
                    payment_protocol="prepaid_api_key",
                    outcome="REFUNDED",
                    latency_ms=max(1, int((time.time() - call_start) * 1000)),
                    rejection_reason=err_reason,
                    metadata={"key_prefix": settlement.get("key_prefix"), "refund_ok": refund_ok},
                )
            )
            fail_status = _failure_http_status(res)
            fail_payload = {
                **(res if isinstance(res, dict) else {"status": "error", "error": "tool_error"}),
                "refunded": bool(refund_ok),
                "refund_receipt": refund_info,
            }
            return fail_status, fail_payload, {"X-Souq-Tool": tool_name, "X-Souq-Billing": "REFUNDED"}

        billing_header = "PAID_PREPAID_CREDIT"
        extra_headers["X-Souq-Credit-Remaining-USD"] = str(settlement.get("balance_remaining_usd", 0.0))
        if is_external_tool:
            split_info = await anyio.to_thread.run_sync(
                partial(marketplace_registry.record_split_settlement, tool_name, price, "prepaid_api_key")
            )
            settlement["marketplace_split"] = split_info
        await anyio.to_thread.run_sync(
            partial(
                negotiation_tracker.log_negotiation,
                client_agent_id=user_agent[:64],
                client_user_agent=user_agent,
                tool_requested=tool_name,
                initial_quote_usd=price,
                settled_price_usd=price,
                payment_protocol="prepaid_api_key",
                outcome="SETTLED",
                latency_ms=max(1, int((time.time() - call_start) * 1000)),
                metadata={
                    "key_prefix": settlement.get("key_prefix"),
                    "tokens_saved": eco["avg_tokens_saved"],
                    "client_ip_hash": client_ip_hash,
                },
            )
        )

    # Priority 2: Direct x402 Base USDC transaction hash (atomic lock across precheck -> dispatch -> commit)
    elif payment_tx:
        allow_sim = _is_test_simulation_allowed()
        simulate = allow_sim and (payment_tx.startswith("0x_simulated_") or payment_tx.startswith("0x_test_"))
        payer_signature = request.headers.get("X-Payer-Signature") or body.get("payer_signature")
        payer_challenge = request.headers.get("X-Payer-Challenge") or body.get("payer_challenge")

        def _execute_x402_locked() -> Tuple[str, int, Dict[str, Any], Dict[str, Any]]:
            norm_tx = payment_tx.strip().lower()
            tx_lock = _get_tx_lock(norm_tx)
            with tx_lock.lock:
                ok_pre, precheck = payment_gw.verify_payment_precheck(
                    tx_hash=norm_tx,
                    expected_price_usdc=price,
                    tool_name=tool_name,
                    client_agent_id=user_agent[:64],
                    client_user_agent=user_agent,
                    simulate_test=simulate,
                    payer_signature=payer_signature,
                    payer_challenge=payer_challenge,
                )
                if not ok_pre:
                    err_label = str(precheck.get("error", "VERIFICATION_FAILED"))
                    if err_label not in ("Payment Nullified", "Payment Rejected: Restricted Source"):
                        negotiation_tracker.log_negotiation(
                            client_agent_id=user_agent[:64],
                            client_user_agent=user_agent,
                            tool_requested=tool_name,
                            initial_quote_usd=price,
                            settled_price_usd=None,
                            payment_protocol="x402_http",
                            outcome="INVALID_PAYMENT",
                            latency_ms=max(1, int((time.time() - call_start) * 1000)),
                            rejection_reason=err_label,
                            metadata={"client_ip_hash": client_ip_hash},
                        )
                    return "precheck_failed", 400, {"error": "Payment Verification Failed", "details": precheck}, {}

                try:
                    tool_res = _dispatch_tool(tool_name, body)
                except Exception as exc:
                    return (
                        "tool_failed",
                        503,
                        {
                            "status": "upstream_unavailable",
                            "error": "upstream_unavailable",
                            "message": f"Tool execution failed before settlement; tx_hash not consumed: {exc}",
                            "tx_consumed": False,
                            "refunded": False,
                        },
                        {},
                    )

                if _is_dispatch_failure(tool_res):
                    fail_code = _failure_http_status(tool_res)
                    fail_body = {
                        **(tool_res if isinstance(tool_res, dict) else {"status": "error", "error": "tool_error"}),
                        "tx_consumed": False,
                        "refunded": False,
                    }
                    return "tool_failed", fail_code, fail_body, {}

                settled_ok, final_settlement = payment_gw.commit_payment_settlement(
                    tx_hash=norm_tx,
                    expected_price_usdc=price,
                    tool_name=tool_name,
                    payload_data=body,
                    payer_address=precheck.get("payer_address", ""),
                    gas_fee_eth=float(precheck.get("gas_fee_eth", 0.00002)),
                    is_simulated=bool(precheck.get("is_simulated", simulate)),
                    client_agent_id=user_agent[:64],
                    client_user_agent=user_agent,
                    start_t=call_start,
                )
                if not settled_ok:
                    return "commit_failed", 400, {"error": "Payment Verification Failed", "details": final_settlement}, {}

                return "ok", 200, tool_res, final_settlement

        outcome_kind, http_code, res, settlement = await anyio.to_thread.run_sync(_execute_x402_locked)
        if outcome_kind == "precheck_failed" or outcome_kind == "commit_failed":
            return http_code, res, {"X-Souq-Tool": tool_name, "X-Souq-Billing": "INVALID_PAYMENT"}
        if outcome_kind == "tool_failed":
            return http_code, res, {"X-Souq-Tool": tool_name, "X-Souq-Billing": "TX_UNCONSUMED_ERROR"}
        if is_external_tool:
            split_info = await anyio.to_thread.run_sync(
                partial(marketplace_registry.record_split_settlement, tool_name, price, "x402_base_usdc")
            )
            settlement["marketplace_split"] = split_info

    # Priority 3: 1 DB-persisted Free Trial per IP hash per 24h (only consumed if tool succeeds; 1st-party tools only)
    else:
        enable_free_trial = (not is_external_tool) and (os.getenv("SOUQ_ENABLE_FREE_TRIAL", "true").lower() == "true")
        trial_eligible = (
            await anyio.to_thread.run_sync(_check_free_trial_eligible, client_ip_hash)
            if enable_free_trial
            else False
        )

        trial_granted = False
        if trial_eligible:
            try:
                res = await anyio.to_thread.run_sync(_dispatch_tool, tool_name, body)
            except Exception as exc:
                return (
                    503,
                    {
                        "status": "upstream_unavailable",
                        "error": "upstream_unavailable",
                        "message": f"Tool execution failed; daily free trial preserved: {exc}",
                        "trial_consumed": False,
                    },
                    {"X-Souq-Tool": tool_name, "X-Souq-Billing": "FREE_TRIAL_UNCONSUMED_ERROR"},
                )

            if _is_dispatch_failure(res):
                return (
                    _failure_http_status(res),
                    {
                        **(res if isinstance(res, dict) else {"status": "error", "error": "tool_error"}),
                        "trial_consumed": False,
                    },
                    {"X-Souq-Tool": tool_name, "X-Souq-Billing": "FREE_TRIAL_UNCONSUMED_ERROR"},
                )

            trial_granted, trial_limit, trial_remaining = await anyio.to_thread.run_sync(
                _consume_free_trial, client_ip_hash
            )
            if trial_granted:
                billing_header = "FREE_TRIAL_EVALUATION"
                extra_headers["X-Souq-Free-Trial-Remaining"] = str(trial_remaining)
                if trial_remaining == 0:
                    extra_headers["X-Souq-Next-Call"] = "HTTP_402_PAYMENT_REQUIRED"
                settlement = {
                    "status": "FREE_TRIAL_GRANTED",
                    "daily_free_limit": trial_limit,
                    "daily_free_remaining": trial_remaining,
                    "notice": (
                        f"Daily free trial evaluation granted ({trial_remaining}/{trial_limit} free calls remaining today). "
                        "Subsequent calls after quota require Base USDC (x402) or a prepaid X-API-Key."
                    ),
                    "recipient_wallet": payment_gw.recipient_wallet,
                    "chain": "Base",
                    "currency": "USDC",
                    "topup_endpoint": "/api/credits/topup",
                    "economic_arbitrage": {
                        "tokens_saved": eco["avg_tokens_saved"],
                        "est_inference_savings_usd": eco["est_inference_savings_usd"],
                        "net_roi_pct": eco["net_roi_pct"],
                    },
                }
                await anyio.to_thread.run_sync(
                    partial(
                        negotiation_tracker.log_negotiation,
                        client_agent_id=user_agent[:64],
                        client_user_agent=user_agent,
                        tool_requested=tool_name,
                        initial_quote_usd=price,
                        settled_price_usd=0.0,
                        payment_protocol="freemium_trial",
                        outcome="FREE_TRIAL_GRANTED",
                        latency_ms=max(1, int((time.time() - call_start) * 1000)),
                        metadata={"tokens_saved": eco["avg_tokens_saved"], "client_ip_hash": client_ip_hash},
                    )
                )

        if not trial_granted:
            challenge = await anyio.to_thread.run_sync(
                partial(
                    payment_gw.generate_402_challenge,
                    tool_name=tool_name,
                    price_usdc=price,
                    client_agent_id=user_agent[:64],
                    client_user_agent=user_agent,
                )
            )
            challenge_headers = {
                "X-Souq-Tool": tool_name,
                "X-Souq-Price-USDC": str(price),
                "X-Souq-Tokens-Saved": str(eco["avg_tokens_saved"]),
                "X-Souq-Inference-Savings-USD": f"${eco['est_inference_savings_usd']:.3f}",
                "X-Souq-Net-ROI": f"{eco['net_roi_pct']}%",
                "X-Souq-Recipient": payment_gw.recipient_wallet,
                "X-Souq-Network": "Base",
                "X-Souq-Token": "USDC",
                "X-Souq-Billing": "HTTP_402_CHALLENGE",
            }
            return 402, challenge, challenge_headers

    res["settlement_receipt"] = settlement

    headers = {
        "X-Souq-Tool": tool_name,
        "X-Souq-Price-USDC": str(price),
        "X-Souq-Tokens-Saved": str(eco.get("avg_tokens_saved", 10000)),
        "X-Souq-Inference-Savings-USD": f"${eco.get('est_inference_savings_usd', 0.05):.3f}",
        "X-Souq-Net-ROI": f"{eco.get('net_roi_pct', 100)}%",
        "X-Souq-Recipient": payment_gw.recipient_wallet,
        "X-Souq-Network": "Base",
        "X-Souq-Token": "USDC",
        "X-Souq-Billing": billing_header,
        **extra_headers,
    }
    return 200, res, headers


async def homepage(request):
    index_path = os.path.join(PROJECT_ROOT, "web", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>SOUQ Autonomous Agent Commerce</h1>")


async def well_known_mcp(request):
    mcp_json_path = os.path.join(PROJECT_ROOT, "web", ".well-known", "mcp.json")
    if os.path.exists(mcp_json_path):
        return FileResponse(mcp_json_path, media_type="application/json")
    return JSONResponse({"status": "active", "tools": list(TOOL_ECONOMICS.keys())})


async def llms_txt(request):
    txt_path = os.path.join(PROJECT_ROOT, "web", "llms.txt")
    if os.path.exists(txt_path):
        return FileResponse(txt_path, media_type="text/plain")
    return HTMLResponse("# SOUQ Agent Commerce\n", media_type="text/plain")


async def llms_full_txt(request):
    txt_path = os.path.join(PROJECT_ROOT, "web", "llms-full.txt")
    if os.path.exists(txt_path):
        return FileResponse(txt_path, media_type="text/plain")
    return HTMLResponse("# SOUQ Full Specification\n", media_type="text/plain")


async def openapi_spec(request):
    spec_path = os.path.join(PROJECT_ROOT, "web", "openapi.json")
    if os.path.exists(spec_path):
        return FileResponse(spec_path, media_type="application/json")
    return JSONResponse({"openapi": "3.1.0", "info": {"title": "SOUQ"}})


async def agent_card(request):
    card_path = os.path.join(PROJECT_ROOT, "web", ".well-known", "agent-card.json")
    if os.path.exists(card_path):
        return FileResponse(card_path, media_type="application/json")
    return JSONResponse({"name": "SOUQ Autonomous Commerce Swarm"})


async def agent_dot_json(request):
    agent_path = os.path.join(PROJECT_ROOT, "web", ".well-known", "agent.json")
    if os.path.exists(agent_path):
        return FileResponse(agent_path, media_type="application/json")
    return await agent_card(request)


async def robots_txt(request):
    robots_path = os.path.join(PROJECT_ROOT, "web", "robots.txt")
    if os.path.exists(robots_path):
        return FileResponse(robots_path, media_type="text/plain")
    return HTMLResponse("User-agent: *\nAllow: /\n", media_type="text/plain")


async def sitemap_xml(request):
    sitemap_path = os.path.join(PROJECT_ROOT, "web", "sitemap.xml")
    if os.path.exists(sitemap_path):
        return FileResponse(sitemap_path, media_type="application/xml")
    return HTMLResponse("<?xml version='1.0'?><urlset></urlset>", media_type="application/xml")


_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#090b10"/>'
    '<path d="M18 22h28l-4 22H22z" fill="#00e5a3"/>'
    '<circle cx="26" cy="18" r="3" fill="#00e5a3"/>'
    '<circle cx="38" cy="18" r="3" fill="#00e5a3"/>'
    '</svg>'
)

_SUPPORTED_MCP_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")


def _extract_admin_candidate(request) -> str:
    header_tok = (request.headers.get("X-Admin-Token") or "").strip()
    if header_tok:
        return header_tok
    auth_hdr = (request.headers.get("Authorization") or "").strip()
    if auth_hdr.lower().startswith("bearer "):
        return auth_hdr[7:].strip()
    return ""


def _is_admin_request(request) -> bool:
    configured = (os.getenv("SOUQ_ADMIN_TOKEN") or "").strip()
    if not configured:
        return False
    candidate = _extract_admin_candidate(request)
    if not candidate:
        return False
    return hmac.compare_digest(candidate, configured)


def _validate_same_origin_url(raw_url: str, request) -> Optional[str]:
    """Validates success_url is relative or same-origin with the current host / SOUQ_PUBLIC_URL."""
    candidate = (raw_url or "").strip()
    if not candidate or any(ch in candidate for ch in ("\r", "\n", "\x00", "\\")):
        return None
    parsed = urllib.parse.urlparse(candidate)
    if parsed.username or parsed.password:
        return None

    req_base = str(request.base_url).rstrip("/")
    req_parsed = urllib.parse.urlparse(req_base)
    allowed_hosts = {req_parsed.netloc.lower()} if req_parsed.netloc else set()
    for env_name in ("SOUQ_PUBLIC_URL", "PUBLIC_BASE_URL"):
        env_url = (os.getenv(env_name) or "").strip()
        if env_url:
            env_netloc = urllib.parse.urlparse(env_url).netloc.lower()
            if env_netloc:
                allowed_hosts.add(env_netloc)

    if not parsed.scheme and not parsed.netloc:
        if not candidate.startswith("/") or candidate.startswith("//"):
            return None
        return urllib.parse.urljoin(f"{req_base}/", candidate.lstrip("/"))

    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return None
    if parsed.netloc.lower() not in allowed_hosts:
        return None
    return candidate


async def indexnow_key_txt(request):
    return PlainTextResponse("souq-agent-commerce-index-key-2026")


async def favicon_ico(request):
    return Response(content=_FAVICON_SVG, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})


async def health(request):
    return JSONResponse({
        "status": "healthy",
        "service": "souq-commerce-swarm",
        "version": "0.3.1",
        "network": "Base",
        "currency": "USDC",
        "a2a_rail": "x402-v1.0",
        "prepaid_rail": "X-API-Key",
        "mcp_http_endpoint": "/mcp",
    })


async def api_catalog(request):
    """
    Free discovery endpoint for visiting agents to inspect tools, prices, and payment options.
    """
    tools_list = []
    for name, data in TOOL_ECONOMICS.items():
        tools_list.append({
            "name": name,
            "category": data["category"],
            "price_usdc": data["price_usdc"],
            "avg_tokens_saved": data["avg_tokens_saved"],
            "est_inference_savings_usd": data["est_inference_savings_usd"],
            "net_roi_pct": data["net_roi_pct"],
            "settlement_rail": "Base L2 USDC (x402) or Prepaid X-API-Key",
        })

    ext_listings = await anyio.to_thread.run_sync(marketplace_registry.list_active_listings)
    for ext in ext_listings:
        tools_list.append({
            "name": ext["tool_id"],
            "title": ext["title"],
            "description": ext["description"],
            "category": ext["category"],
            "seller_name": ext["seller_name"],
            "price_usdc": ext["price_usdc"],
            "marketplace_partner": True,
            "settlement_rail": "Base L2 USDC (x402) or Prepaid X-API-Key (80% Seller / 20% SOUQ)",
        })

    return JSONResponse({
        "vendor": "SOUQ Autonomous Commerce Swarm",
        "version": "0.3.1",
        "protocol": "x402-v1.0",
        "network": "Base",
        "currency": "USDC",
        "recipient_wallet": payment_gw.recipient_wallet,
        "mcp_http_endpoint": "/mcp",
        "topup_endpoint": "/api/credits/topup",
        "marketplace_list_endpoint": "/api/marketplace/listings",
        "tools": tools_list,
        "marketplace_listings": ext_listings,
        "digital_products": polar_adapter.list_catalog(),
    })


async def api_products(request):
    """Lists digital datasets, boilerplates, and prepaid API credit packs."""
    return JSONResponse({
        "status": "online",
        "provider": "Polar.sh Merchant of Record + Base L2 USDC",
        "usdc_recipient_wallet": payment_gw.recipient_wallet,
        "products": polar_adapter.list_catalog(),
    })


async def api_cyber_threat_intel(request):
    """Live cybersecurity threat intelligence status, rule counts, and active signatures."""
    sigs = threat_radar.load_cached_signatures()
    return JSONResponse({
        "status": "active",
        "agent": "Sayf Cyber Threat Intelligence Sentinel",
        "version": sigs.get("version", "2.0.0"),
        "last_updated_epoch": sigs.get("last_updated_epoch", 0),
        "total_rules": sigs.get("total_rules", 0),
        "prompt_injection_rules_count": len(sigs.get("prompt_injection_rules", [])),
        "honeypot_rules_count": len(sigs.get("honeypot_rules", [])),
        "secret_rules_count": len(sigs.get("secret_rules", [])),
        "services_protected": [
            "prompt_injection_firewall",
            "smart_contract_honeypot_radar",
            "secret_leak_scanner",
            "deep_ast_vulnerability_auditor",
            "api_attack_surface_scanner"
        ]
    })


async def api_tool_call(request):
    """HTTP REST endpoint for executing paid SOUQ tools."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    if not isinstance(body, dict):
        return JSONResponse({"error": "Invalid JSON object payload"}, status_code=400)

    tool_name = str(body.get("tool", "")).strip()
    status_code, payload, headers = await _authorize_and_execute_tool(request, tool_name, body)
    return JSONResponse(payload, status_code=status_code, headers=headers)


async def api_credits_topup(request):
    """
    Verifies a Base USDC transaction once (min $0.50) and mints/tops up a reusable X-API-Key.
    Prevents per-call crypto signing overhead.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    if not isinstance(body, dict):
        return JSONResponse({"error": "Invalid JSON object payload"}, status_code=400)

    tx_hash = (body.get("tx_hash") or body.get("payment_tx_hash") or request.headers.get("X-Payment-Tx") or "").strip()
    existing_api_key = body.get("api_key") or request.headers.get("X-API-Key")
    label = str(body.get("label") or request.headers.get("User-Agent", "agent"))[:120]
    client_ip_hash = telemetry_engine.hash_ip(_extract_client_ip(request))

    min_usd = float(os.getenv("SOUQ_MIN_TOPUP_USD", "0.50"))
    allow_sim = _is_test_simulation_allowed()
    simulate = allow_sim and (tx_hash.startswith("0x_simulated_") or tx_hash.startswith("0x_test_"))

    has_explicit_sim_amount = "simulated_amount_usd" in body and body["simulated_amount_usd"] is not None
    if has_explicit_sim_amount and not simulate:
        return JSONResponse(
            {
                "error": "Simulated Top-ups Disabled",
                "code": "simulated_topup_disabled",
                "message": "Simulated top-up amounts are disabled unless explicit test simulation is enabled in a non-production or test environment.",
            },
            status_code=400,
        )

    sim_amount = 5.0
    if has_explicit_sim_amount:
        raw_sim = body["simulated_amount_usd"]
        if isinstance(raw_sim, bool):
            return JSONResponse({"error": "invalid_simulated_amount", "message": "simulated_amount_usd must be numeric."}, status_code=400)
        try:
            sim_amount = float(raw_sim)
        except (TypeError, ValueError):
            return JSONResponse({"error": "invalid_simulated_amount", "message": "simulated_amount_usd must be numeric."}, status_code=400)
        if not math.isfinite(sim_amount) or sim_amount <= 0.0 or sim_amount > 100.0:
            return JSONResponse(
                {
                    "error": "invalid_simulated_amount",
                    "message": "simulated_amount_usd must be > 0 and <= 100.0 USD.",
                },
                status_code=400,
            )

    valid, payer, credited_usd, err_msg = await anyio.to_thread.run_sync(
        lambda: payment_gw.verify_usdc_topup(
            tx_hash=tx_hash,
            min_usd=min_usd,
            simulate_test=simulate,
            simulated_amount_usd=sim_amount,
        )
    )
    if not valid:
        return JSONResponse(
            {
                "error": "Top-up Verification Failed",
                "message": err_msg,
                "recipient_wallet": payment_gw.recipient_wallet,
                "usdc_contract": payment_gw.usdc_contract,
                "chain": "Base",
                "chain_id": 8453,
                "min_topup_usd": min_usd,
            },
            status_code=400,
        )

    ok, result = await anyio.to_thread.run_sync(
        lambda: api_key_ledger.issue_or_topup_key(
            reference_id=tx_hash,
            amount_usd=credited_usd,
            rail="base_usdc",
            owner_label=payer or label,
            existing_api_key=existing_api_key,
        )
    )
    if not ok:
        return JSONResponse(result, status_code=409 if "Already Redeemed" in result.get("error", "") else 400)

    # Record tax receipt + negotiation event alongside key ledger
    if not simulate:
        payer_final = payer
    else:
        payer_final = "0xSimulatedClientAgentWallet999"

    receipt = await anyio.to_thread.run_sync(
        lambda: receipt_engine.generate_receipt(
            tx_hash=tx_hash,
            payer_address=payer_final,
            recipient_address=payment_gw.recipient_wallet,
            amount_usdc=credited_usd,
            product_id="prepaid_credit_topup",
            service_rendered=f"SOUQ Prepaid API Credit Pack (${credited_usd:.2f} USD)",
            payload_data={"key_prefix": result.get("key_prefix"), "credited_usd": credited_usd},
            chain="Base",
            token_contract=payment_gw.usdc_contract,
            is_simulated=simulate,
        )
    )
    await anyio.to_thread.run_sync(
        partial(
            negotiation_tracker.log_negotiation,
            client_agent_id=label[:64],
            client_user_agent=request.headers.get("User-Agent", ""),
            tool_requested="prepaid_credit_topup",
            initial_quote_usd=credited_usd,
            settled_price_usd=credited_usd,
            payment_protocol="base_usdc_topup",
            outcome="SETTLED",
            latency_ms=10,
            metadata={
                "receipt_id": receipt["receipt_id"],
                "key_prefix": result.get("key_prefix"),
                "is_simulated": simulate,
                "client_ip_hash": client_ip_hash,
            },
        )
    )

    result["receipt_id"] = receipt["receipt_id"]
    return JSONResponse(result, status_code=200)


async def api_credits_balance(request):
    """Returns credit balance & usage metadata for an X-API-Key."""
    api_key, _ = _extract_payment_credentials(request, {})
    if not api_key:
        return JSONResponse({"error": "Missing X-API-Key or Authorization Bearer header"}, status_code=401)
    status = await anyio.to_thread.run_sync(api_key_ledger.get_key_status, api_key)
    if not status:
        return JSONResponse({"error": "Invalid or unknown API key"}, status_code=401)
    return JSONResponse({"status": "active", **status})


async def api_checkout_create(request):
    """Creates or resolves a Polar.sh Merchant-of-Record fiat checkout link with same-origin redirect safety."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    if not isinstance(body, dict):
        return JSONResponse({"error": "Invalid JSON object payload"}, status_code=400)

    sku = str(body.get("sku") or "api_credit_pack_5").strip()
    customer_email = body.get("customer_email")
    base = str(request.base_url).rstrip("/")
    raw_success_url = body.get("success_url")
    if raw_success_url is not None and str(raw_success_url).strip() != "":
        success_url = _validate_same_origin_url(str(raw_success_url), request)
        if not success_url:
            return JSONResponse(
                {
                    "error": "invalid_success_url",
                    "message": "success_url must be a relative path or same-origin http(s) URL.",
                },
                status_code=400,
            )
    else:
        success_url = f"{base}/?checkout=success"

    res = await anyio.to_thread.run_sync(
        lambda: polar_adapter.create_checkout_session(
            sku=sku,
            success_url=success_url,
            customer_email=customer_email,
        )
    )
    res_status = res.get("status")
    if res_status == "ready":
        code = 200
    elif "Unknown SKU" in str(res.get("error", "")):
        code = 404
    else:
        code = 503
    return JSONResponse(res, status_code=code)


async def api_checkout_claim(request):
    """
    One-time claim endpoint exchanging a Polar checkout claim token / order_id
    for the provisioned prepaid X-API-Key without leaking secrets into webhook responses.
    """
    claim_token = (
        request.query_params.get("claim")
        or request.query_params.get("claim_token")
        or ""
    ).strip()
    order_id = (request.query_params.get("order_id") or "").strip()
    if not claim_token and not order_id:
        return JSONResponse({"error": "Missing claim_token or order_id"}, status_code=400)

    ok, res = await anyio.to_thread.run_sync(
        partial(
            polar_adapter.claim_checkout_key,
            claim_token=claim_token or None,
            order_id=order_id or None,
        )
    )
    if not ok:
        err_msg = str(res.get("error", "Claim failed"))
        lower = err_msg.lower()
        if "missing" in lower:
            code = 400
        elif "already redeemed" in lower or "expired" in lower:
            code = 410
        elif "not found" in lower:
            code = 404
        else:
            code = 500
        return JSONResponse({"status": "error", "error": err_msg}, status_code=code)

    sku = str(res.get("sku") or "")
    credit_usd = POLAR_PRODUCTS.get(sku, {}).get("credit_usd")
    if credit_usd is None:
        credit_usd = round(float(res.get("amount_cents", 0)) / 100.0, 2)

    return JSONResponse(
        {
            "status": "success",
            "api_key": res["api_key"],
            "key_prefix": res.get("key_prefix"),
            "sku": sku,
            "order_id": res.get("order_id"),
            "credits_added_usd": float(credit_usd),
        },
        status_code=200,
        headers={"Cache-Control": "no-store"},
    )


async def webhooks_polar(request):
    """Verified webhook endpoint for Polar.sh orders & automatic credit provisioning."""
    raw_body = await request.body()
    if not polar_adapter.webhook_secret:
        return JSONResponse({"error": "Polar webhook secret is not configured"}, status_code=503)

    if not polar_adapter.verify_webhook_signature(raw_body, dict(request.headers)):
        return JSONResponse({"error": "Invalid Polar webhook signature"}, status_code=401)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return JSONResponse({"error": "Malformed JSON webhook body"}, status_code=400)

    result = await anyio.to_thread.run_sync(polar_adapter.handle_order_webhook, payload)
    return JSONResponse(result, status_code=200)


async def mcp_http_endpoint(request):
    """
    Remote Streamable HTTP MCP JSON-RPC 2.0 endpoint (/mcp).
    Supports GET (405 stateless SSE notice), DELETE (204), and POST JSON-RPC 2.0.
    """
    if request.method == "GET":
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": "SSE GET stream not enabled; use POST /mcp with JSON-RPC 2.0",
                },
            },
            status_code=405,
            headers={"Allow": "POST, DELETE"},
        )

    if request.method == "DELETE":
        return Response(status_code=204)

    try:
        msg = await request.json()
    except Exception:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    if not isinstance(msg, dict) or not isinstance(msg.get("method"), str) or not msg["method"].strip():
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": msg.get("id") if isinstance(msg, dict) else None,
                "error": {"code": -32600, "message": "Invalid Request"},
            },
            status_code=400,
        )

    method = msg["method"]
    params = msg.get("params")
    if params is None:
        params = {}
    elif not isinstance(params, dict):
        if method.startswith("notifications/") or "id" not in msg:
            return Response(status_code=202)
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {"code": -32602, "message": "Invalid params: 'params' must be an object"},
            },
            status_code=400,
        )

    if method.startswith("notifications/") or "id" not in msg:
        return Response(status_code=202)

    msg_id = msg.get("id")

    if method == "initialize":
        req_proto = str(params.get("protocolVersion") or "").strip()
        if req_proto in _SUPPORTED_MCP_PROTOCOLS:
            negotiated_proto = req_proto
        elif not req_proto:
            negotiated_proto = "2025-03-26"
        else:
            negotiated_proto = _SUPPORTED_MCP_PROTOCOLS[0]
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": negotiated_proto,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "souq-mcp", "version": "0.3.0"},
            },
        })

    if method == "ping":
        return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": {}})

    if method == "tools/list":
        ext_listings = await anyio.to_thread.run_sync(marketplace_registry.list_active_listings)
        dynamic_tools = list(MCP_TOOLS_SCHEMA)
        for ext in ext_listings:
            dynamic_tools.append({
                "name": ext["tool_id"],
                "description": f"[Partner: {ext['seller_name']} | ${ext['price_usdc']:.3f}/call] {ext['description']}",
                "inputSchema": ext.get("input_schema") or {"type": "object", "properties": {}},
            })
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": dynamic_tools},
        })

    if method == "tools/call":
        tool_name = str(params.get("name") or "").strip()
        if "arguments" in params:
            arguments = params.get("arguments")
            if not isinstance(arguments, dict):
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32602, "message": "Invalid params: 'arguments' must be an object"},
                    },
                    status_code=400,
                )
        else:
            arguments = {}

        if tool_name == "souq_account_status":
            api_key, _ = _extract_payment_credentials(request, arguments)
            key_status = (
                await anyio.to_thread.run_sync(api_key_ledger.get_key_status, api_key)
                if api_key
                else None
            )
            info = {
                "service": "SOUQ Autonomous Agent Commerce",
                "version": "0.3.0",
                "authenticated_key": key_status,
                "payment_rails": {
                    "base_usdc_wallet": payment_gw.recipient_wallet,
                    "base_usdc_contract": payment_gw.usdc_contract,
                    "topup_endpoint": "/api/credits/topup",
                    "free_trial": "1 call / 24h per client IP without key",
                },
                "available_tools": {k: v["price_usdc"] for k, v in TOOL_ECONOMICS.items()},
            }
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(info, indent=2)}]},
                },
                headers={"X-Souq-Tool": "souq_account_status", "X-Souq-Billing": "FREE_DISCOVERY"},
            )

        status_code, payload, tool_headers = await _authorize_and_execute_tool(request, tool_name, arguments)
        if status_code == 200:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]},
                },
                headers=tool_headers,
            )

        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
                },
            },
            headers=tool_headers,
        )

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method '{method}' not found"},
    })


def _fetch_sales_kpis_sync() -> Tuple[int, float, int, float]:
    confirmed_orders = 0
    confirmed_volume_usd = 0.0
    prepaid_keys_count = 0
    prepaid_volume_usd = 0.0
    try:
        with db_transaction(DB_TARGET, read_only=True) as con:
            res = con.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount_usd), 0.0)
                FROM crypto_receipts
                WHERE payer_address NOT LIKE '%Simulated%'
                  AND (is_simulated IS NULL OR is_simulated = FALSE)
            """).fetchone()
            if res:
                confirmed_orders = int(res[0])
                confirmed_volume_usd = float(res[1])

            topup_res = con.execute("""
                SELECT COUNT(DISTINCT key_hash), COALESCE(SUM(amount_usd), 0.0)
                FROM credit_topups
                WHERE payer_identifier NOT LIKE '%Simulated%'
            """).fetchone()
            if topup_res:
                prepaid_keys_count = int(topup_res[0])
                prepaid_volume_usd = float(topup_res[1])
    except Exception:
        pass
    return confirmed_orders, confirmed_volume_usd, prepaid_keys_count, prepaid_volume_usd


async def api_stats(request):
    """Real-time aggregate KPIs publicly; granular recent_activity & internals gated by SOUQ_ADMIN_TOKEN."""
    is_admin = _is_admin_request(request)
    traffic = await anyio.to_thread.run_sync(telemetry_engine.get_traffic_summary)
    market = await anyio.to_thread.run_sync(negotiation_tracker.get_market_intelligence_summary)
    confirmed_orders, confirmed_volume_usd, prepaid_keys_count, prepaid_volume_usd = await anyio.to_thread.run_sync(
        _fetch_sales_kpis_sync
    )
    marketplace_kpis = await anyio.to_thread.run_sync(marketplace_registry.get_marketplace_kpis)

    if is_admin:
        traffic_out = traffic
        market_out = market
    else:
        traffic_out = {k: v for k, v in traffic.items() if k != "recent_activity"}
        market_out = {k: v for k, v in market.items() if k != "rejection_analysis"}

    return JSONResponse({
        "service": "SOUQ Autonomous Agent Commerce Swarm",
        "version": "0.3.1",
        "status": "online",
        "settlement_rail": "Base L2 USDC (x402) + Prepaid X-API-Key + Polar MoR + Partner 80/20 Split",
        "recipient_wallet": payment_gw.recipient_wallet,
        "total_settled_orders": confirmed_orders,
        "settled_volume_usdc": round(confirmed_volume_usd, 6),
        "active_tools": len(TOOL_ECONOMICS) + marketplace_kpis["active_listings"],
        "uptime": round(max(0.0, time.time() - _SERVER_START_TS), 1),
        "top_tools": traffic_out.get("top_tools", []),
        "marketplace_kpis": marketplace_kpis,
        "sales_summary": {
            "confirmed_paid_orders": confirmed_orders,
            "total_settled_usd": round(confirmed_volume_usd, 6),
            "prepaid_active_accounts": prepaid_keys_count,
            "prepaid_credited_usd": round(prepaid_volume_usd, 6),
            "currency": "USDC",
        },
        "traffic_telemetry": traffic_out,
        "negotiations_telemetry": market_out,
    })


def _is_swarm_admin_authorized(request) -> bool:
    configured = (os.getenv("SOUQ_ADMIN_TOKEN") or "").strip()
    if configured:
        return _is_admin_request(request)
    if _is_prod_environment():
        return False
    peer = request.client.host if request.client and request.client.host else ""
    has_proxy_hdrs = any(
        request.headers.get(h) for h in ("CF-Connecting-IP", "X-Forwarded-For", "X-Real-IP")
    )
    return (not has_proxy_hdrs) and peer in ("127.0.0.1", "::1", "::ffff:127.0.0.1")


async def api_swarm_cycle(request):
    """Protected operational endpoint to trigger a RaisConductor daily autonomous swarm cycle."""
    if not _is_swarm_admin_authorized(request):
        return JSONResponse({"error": "Forbidden", "message": "Valid admin authorization is required."}, status_code=403)

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse({"error": "Invalid JSON object payload"}, status_code=400)

    broadcast_search = bool(body.get("broadcast_search", False))

    def _run_cycle() -> Dict[str, Any]:
        from agents.core.conductor import RaisConductor

        conductor = RaisConductor(db_path=DB_TARGET)
        return conductor.run_daily_cycle(broadcast_search=broadcast_search)

    try:
        report = await anyio.to_thread.run_sync(_run_cycle)
        return JSONResponse({"status": "completed", "cycle": report}, status_code=200)
    except Exception as exc:
        return JSONResponse(
            {"status": "error", "error": "swarm_cycle_failed", "message": str(exc)},
            status_code=500,
        )


async def api_marketplace_listings(request):
    """GET lists active partner tools; POST registers a new external agent/human tool after Amin screening."""
    if request.method == "GET":
        listings = await anyio.to_thread.run_sync(marketplace_registry.list_active_listings)
        kpis = await anyio.to_thread.run_sync(marketplace_registry.get_marketplace_kpis)
        return JSONResponse({
            "status": "online",
            "commission_policy": {
                "seller_share_pct": 80,
                "souq_commission_pct": 20,
                "min_payout_usd": 10.0,
                "payout_rail": "Base L2 USDC",
            },
            "kpis": kpis,
            "listings": listings,
        })

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON object payload"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "Invalid JSON object payload"}, status_code=400)

    existing_seller_key = (
        request.headers.get("X-Seller-Key")
        or body.get("seller_api_key")
        or ""
    ).strip() or None

    ok, result = await anyio.to_thread.run_sync(
        partial(
            marketplace_registry.register_seller_and_listing,
            tool_slug=str(body.get("tool_slug") or body.get("slug") or body.get("title") or ""),
            title=str(body.get("title") or ""),
            description=str(body.get("description") or ""),
            endpoint_url=str(body.get("endpoint_url") or ""),
            price_usdc=body.get("price_usdc", 0.02),
            payout_wallet_base=str(body.get("payout_wallet_base") or ""),
            seller_name=str(body.get("seller_name") or "External Agent Builder"),
            category=str(body.get("category") or "External Agent Tool"),
            contact_handle=str(body.get("contact_handle") or ""),
            input_schema=body.get("input_schema") if isinstance(body.get("input_schema"), dict) else None,
            existing_seller_key=existing_seller_key,
        )
    )
    return JSONResponse(result, status_code=201 if ok else 400)


async def api_marketplace_seller_dashboard(request):
    """Returns seller earnings (80% split), calls, payout status, and listings via X-Seller-Key."""
    seller_key = (request.headers.get("X-Seller-Key") or "").strip()
    if not seller_key:
        return JSONResponse({"error": "Missing X-Seller-Key header"}, status_code=401)
    dash = await anyio.to_thread.run_sync(marketplace_registry.get_seller_dashboard, seller_key)
    if not dash:
        return JSONResponse({"error": "Invalid X-Seller-Key"}, status_code=401)
    return JSONResponse(dash, status_code=200)


async def api_marketplace_seller_payout(request):
    """Queues a Base L2 USDC payout for a seller once earned_balance_usd >= $10.00."""
    seller_key = (request.headers.get("X-Seller-Key") or "").strip()
    if not seller_key:
        return JSONResponse({"error": "Missing X-Seller-Key header"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        body = {}
    amount_usd = body.get("amount_usd") if isinstance(body, dict) else None
    ok, result = await anyio.to_thread.run_sync(
        partial(marketplace_registry.request_seller_payout, seller_key, amount_usd=amount_usd)
    )
    return JSONResponse(result, status_code=200 if ok else 400)


routes = [
    Route("/", homepage),
    Route("/favicon.ico", favicon_ico, methods=["GET"]),
    Route("/health", health),
    Route("/llms.txt", llms_txt),
    Route("/llms-full.txt", llms_full_txt),
    Route("/robots.txt", robots_txt),
    Route("/sitemap.xml", sitemap_xml),
    Route("/openapi.json", openapi_spec),
    Route("/souq-agent-commerce-index-key-2026.txt", indexnow_key_txt),
    Route("/.well-known/mcp.json", well_known_mcp),
    Route("/.well-known/agent-card.json", agent_card),
    Route("/.well-known/agent.json", agent_dot_json),
    Route("/mcp", mcp_http_endpoint, methods=["GET", "POST", "DELETE"]),
    Route("/api/catalog", api_catalog),
    Route("/api/products", api_products),
    Route("/api/cyber/threat-intel", api_cyber_threat_intel),
    Route("/api/stats", api_stats),
    Route("/api/tools/call", api_tool_call, methods=["POST"]),
    Route("/api/marketplace/listings", api_marketplace_listings, methods=["GET", "POST"]),
    Route("/api/marketplace/seller/dashboard", api_marketplace_seller_dashboard, methods=["GET"]),
    Route("/api/marketplace/seller/payout", api_marketplace_seller_payout, methods=["POST"]),
    Route("/api/credits/topup", api_credits_topup, methods=["POST"]),
    Route("/api/credits/balance", api_credits_balance, methods=["GET"]),
    Route("/api/checkout/create", api_checkout_create, methods=["POST"]),
    Route("/api/polar/checkout", api_checkout_create, methods=["POST"]),
    Route("/api/checkout/claim", api_checkout_claim, methods=["GET"]),
    Route("/webhooks/polar", webhooks_polar, methods=["POST"]),
    Route("/api/webhooks/polar", webhooks_polar, methods=["POST"]),
    Route("/api/swarm/cycle", api_swarm_cycle, methods=["POST"]),
]

middleware = [
    Middleware(SecurityHeadersAndProtectionMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    ),
    Middleware(TrafficTelemetryMiddleware),
]

app = Starlette(debug=False, routes=routes, middleware=middleware)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 SOUQ Koyeb Server v0.3.0 starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
