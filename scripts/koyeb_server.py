"""
SOUQ // Koyeb Production Edge Server
Unified ASGI server running on Koyeb Free Tier:
- Serves the Web Storefront to humans at '/'
- Serves the Machine Registry at '/.well-known/mcp.json'
- Serves the Health Check at '/health'
- Serves the Paid FastMCP & x402 endpoints to autonomous agents
"""

import os
import sys
import time
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, FileResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# Ensure project root is on path & load secure environment
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, "config", ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MAX_PAYLOAD_BYTES = int(os.getenv("SOUQ_MAX_PAYLOAD_BYTES", "1048576"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("SOUQ_RATE_LIMIT_PER_MINUTE", "120"))

# In-memory sliding window rate-limiter per IP
_ip_request_history = {}
# In-memory free trial history per IP (1 free call per 24h for agent evaluation)
_ip_free_trial_history = {}


class SecurityHeadersAndProtectionMiddleware(BaseHTTPMiddleware):
    """
    Production Security Shield:
    - Enforces Anti-Clickjacking & Anti-MIME sniffing headers
    - Throttles abusive DDoS requests per IP
    - Blocks oversized memory-bomb payloads
    """

    async def dispatch(self, request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Sliding window rate limiter
        history = [t for t in _ip_request_history.get(client_ip, []) if now - t < 60]
        if len(history) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                {"error": "Too Many Requests", "message": "Rate limit exceeded. Please throttle automated calls."},
                status_code=429,
                headers={"Retry-After": "60"}
            )
        history.append(now)
        _ip_request_history[client_ip] = history

        # Enforce max payload size
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_PAYLOAD_BYTES:
            return JSONResponse(
                {"error": "Payload Too Large", "max_allowed_bytes": MAX_PAYLOAD_BYTES},
                status_code=413
            )

        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

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
from agents.treasury.x402_gateway import X402PaymentGateway

# Initialize Engines
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
payment_gw = X402PaymentGateway()


TOOL_ECONOMICS = {
    "prediction_market_arbitrage_radar": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 35000,
        "est_inference_savings_usd": 0.175,
        "net_roi_pct": 483,
        "category": "Prediction Market Arbitrage"
    },
    "token_context_compressor": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 14000,
        "est_inference_savings_usd": 0.070,
        "net_roi_pct": 600,
        "category": "Context Optimization"
    },
    "ast_structural_slicer": {
        "price_usdc": 0.02,
        "avg_tokens_saved": 3000,
        "est_inference_savings_usd": 0.015,
        "net_roi_pct": 75,
        "category": "Code Slicing"
    },
    "quant_microstructure_radar": {
        "price_usdc": 0.02,
        "avg_tokens_saved": 15000,
        "est_inference_savings_usd": 0.075,
        "net_roi_pct": 275,
        "category": "Alpha & Microstructure"
    },
    "cross_exchange_arbitrage_scanner": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 12000,
        "est_inference_savings_usd": 0.060,
        "net_roi_pct": 100,
        "category": "Arbitrage & Basis"
    },
    "orderbook_slippage_simulator": {
        "price_usdc": 0.02,
        "avg_tokens_saved": 15000,
        "est_inference_savings_usd": 0.075,
        "net_roi_pct": 275,
        "category": "Execution Optimization"
    },
    "smart_money_whale_flow_radar": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 20000,
        "est_inference_savings_usd": 0.100,
        "net_roi_pct": 233,
        "category": "Whale Flow Telemetry"
    },
    "dev_api_cheatsheet_vault": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 40000,
        "est_inference_savings_usd": 0.200,
        "net_roi_pct": 1900,
        "category": "API Schema Reference"
    },
    "daily_tech_ai_trends_radar": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 25000,
        "est_inference_savings_usd": 0.125,
        "net_roi_pct": 1150,
        "category": "AI Technology Radar"
    },
    "ast_security_scanner": {
        "price_usdc": 0.03,
        "avg_tokens_saved": 4000,
        "est_inference_savings_usd": 0.020,
        "net_roi_pct": 67,
        "category": "Security Linting"
    },
    "synthetic_schema_verifier": {
        "price_usdc": 0.01,
        "avg_tokens_saved": 1500,
        "est_inference_savings_usd": 0.008,
        "net_roi_pct": 80,
        "category": "Schema Conformity"
    }
}


async def homepage(request):
    index_path = os.path.join(PROJECT_ROOT, "web", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>SOUQ Autonomous Agent Commerce</h1>")


async def well_known_mcp(request):
    mcp_json_path = os.path.join(PROJECT_ROOT, "web", ".well-known", "mcp.json")
    if os.path.exists(mcp_json_path):
        return FileResponse(mcp_json_path, media_type="application/json")
    return JSONResponse({"status": "active", "tools": ["token_compressor", "quant_radar"]})


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


async def health(request):
    return JSONResponse({
        "status": "healthy",
        "service": "souq-commerce-swarm",
        "network": "Base",
        "currency": "USDC",
        "a2a_rail": "x402-v1.0"
    })


async def api_catalog(request):
    """
    Free discovery endpoint for visiting agents to inspect tools, prices, and token savings.
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
            "settlement_rail": "Base L2 (USDC)"
        })

    return JSONResponse({
        "vendor": "SOUQ Autonomous Commerce Swarm",
        "protocol": "x402-v1.0",
        "network": "Base",
        "currency": "USDC",
        "recipient_wallet": payment_gw.recipient_wallet,
        "tools": tools_list
    })


async def api_tool_call(request):
    """
    HTTP REST / JSON-RPC endpoint for client AI agents executing paid tools with x402 headers.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    tool_name = body.get("tool", "")
    payment_tx = request.headers.get("X-Payment-Tx") or body.get("payment_tx_hash")

    eco = TOOL_ECONOMICS.get(tool_name, {
        "price_usdc": 0.02,
        "avg_tokens_saved": 10000,
        "est_inference_savings_usd": 0.05,
        "net_roi_pct": 150
    })
    price = eco["price_usdc"]
    is_free_trial = False

    if not payment_tx:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        last_trial = _ip_free_trial_history.get(client_ip, 0)
        enable_free_trial = os.getenv("SOUQ_ENABLE_FREE_TRIAL", "true").lower() == "true"

        if enable_free_trial and (now - last_trial >= 86400):
            is_free_trial = True
            _ip_free_trial_history[client_ip] = now
            settlement = {
                "status": "FREE_TRIAL_GRANTED",
                "notice": "1 daily free trial evaluation granted. Subsequent calls require HTTP 402 Base USDC micropayments.",
                "recipient_wallet": payment_gw.recipient_wallet,
                "chain": "Base",
                "currency": "USDC",
                "economic_arbitrage": {
                    "tokens_saved": eco["avg_tokens_saved"],
                    "est_inference_savings_usd": eco["est_inference_savings_usd"],
                    "net_roi_pct": eco["net_roi_pct"]
                }
            }
        else:
            challenge = payment_gw.generate_402_challenge(
                tool_name=tool_name,
                price_usdc=price,
                client_agent_id=request.headers.get("User-Agent", "anonymous-agent")
            )
            challenge_headers = {
                "X-Souq-Tool": tool_name,
                "X-Souq-Price-USDC": str(price),
                "X-Souq-Tokens-Saved": str(eco["avg_tokens_saved"]),
                "X-Souq-Inference-Savings-USD": f"${eco['est_inference_savings_usd']:.3f}",
                "X-Souq-Net-ROI": f"{eco['net_roi_pct']}%",
                "X-Souq-Recipient": payment_gw.recipient_wallet,
                "X-Souq-Network": "Base",
                "X-Souq-Token": "USDC"
            }
            return JSONResponse(challenge, status_code=402, headers=challenge_headers)
    else:
        allow_sim = os.getenv("SOUQ_ALLOW_TEST_SIMULATION", "false").lower() == "true"
        simulate = allow_sim and (payment_tx.startswith("0x_simulated_") or payment_tx.startswith("0x_test_"))
        settled, settlement = payment_gw.verify_payment_and_settle(
            tx_hash=payment_tx,
            expected_price_usdc=price,
            tool_name=tool_name,
            payload_data=body,
            simulate_test=simulate
        )

        if not settled:
            return JSONResponse({"error": "Payment Verification Failed", "details": settlement}, status_code=400)

    # Execute tool logic
    if tool_name == "token_context_compressor":
        res = token_compressor.compress_text_or_json(body.get("raw_content", ""))
    elif tool_name == "ast_structural_slicer":
        res = ast_slicer.slice_symbol(body.get("source_code", ""), body.get("target_symbol", ""))
    elif tool_name == "quant_microstructure_radar":
        res = micro_engine.get_microstructure_metrics(body.get("symbol", "BTC/USDT"))
    elif tool_name == "cross_exchange_arbitrage_scanner":
        res = arbitrage_scanner.scan_arbitrage_and_funding(body.get("symbol", "BTC/USDT"))
    elif tool_name == "orderbook_slippage_simulator":
        res = slippage_simulator.simulate_slippage(
            symbol=body.get("symbol", "BTC/USDT"),
            side=body.get("side", "BUY"),
            trade_size_usd=float(body.get("trade_size_usd", 10000.0))
        )
    elif tool_name == "smart_money_whale_flow_radar":
        res = whale_radar.get_whale_flow_telemetry(
            symbol=body.get("symbol", "BTC/USDT"),
            block_threshold_usd=float(body.get("block_threshold_usd", 50000.0))
        )
    elif tool_name == "dev_api_cheatsheet_vault":
        res = dev_vault.get_api_cheatsheet(ecosystem=body.get("ecosystem", "openai"))
    elif tool_name == "daily_tech_ai_trends_radar":
        res = trends_radar.refresh_cache_and_get(force_refresh=bool(body.get("force_refresh", False)))
    elif tool_name == "ast_security_scanner":
        res = security_scanner.scan_python_code(body.get("source_code", ""))
    elif tool_name == "synthetic_schema_verifier":
        res = schema_verifier.verify_schema_conformity(body.get("data", {}), body.get("schema", {}))
    elif tool_name == "prediction_market_arbitrage_radar":
        res = prediction_radar.scan_prediction_arbitrage(asset=body.get("asset", body.get("symbol", "BTC")))
    else:
        res = {"status": "success", "message": f"Tool '{tool_name}' executed."}

    res["settlement_receipt"] = settlement
    headers = {
        "X-Souq-Tool": tool_name,
        "X-Souq-Price-USDC": str(price),
        "X-Souq-Tokens-Saved": str(eco.get("avg_tokens_saved", 10000)),
        "X-Souq-Inference-Savings-USD": f"${eco.get('est_inference_savings_usd', 0.05):.3f}",
        "X-Souq-Net-ROI": f"{eco.get('net_roi_pct', 100)}%",
        "X-Souq-Recipient": payment_gw.recipient_wallet,
        "X-Souq-Network": "Base",
        "X-Souq-Token": "USDC"
    }
    if is_free_trial:
        headers["X-Souq-Billing"] = "FREE_TRIAL_EVALUATION"
        headers["X-Souq-Next-Call"] = "HTTP_402_PAYMENT_REQUIRED"
    else:
        headers["X-Souq-Billing"] = "PAID_SETTLEMENT"
    return JSONResponse(res, headers=headers)


routes = [
    Route("/", homepage),
    Route("/health", health),
    Route("/llms.txt", llms_txt),
    Route("/llms-full.txt", llms_full_txt),
    Route("/robots.txt", robots_txt),
    Route("/sitemap.xml", sitemap_xml),
    Route("/openapi.json", openapi_spec),
    Route("/.well-known/mcp.json", well_known_mcp),
    Route("/.well-known/agent-card.json", agent_card),
    Route("/.well-known/agent.json", agent_card),
    Route("/api/catalog", api_catalog),
    Route("/api/tools/call", api_tool_call, methods=["POST"]),
]

middleware = [
    Middleware(SecurityHeadersAndProtectionMiddleware)
]

app = Starlette(debug=False, routes=routes, middleware=middleware)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 SOUQ Koyeb Server starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

