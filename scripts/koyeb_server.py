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
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, FileResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
import uvicorn

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.production.mcp_tool_builder import MarketMicrostructureEngine, ASTSecurityScanner, SyntheticSchemaVerifier
from agents.production.token_compressor import TokenContextCompressor, CodeASTSlicer
from agents.treasury.x402_gateway import X402PaymentGateway

# Initialize Engines
micro_engine = MarketMicrostructureEngine()
security_scanner = ASTSecurityScanner()
schema_verifier = SyntheticSchemaVerifier()
token_compressor = TokenContextCompressor()
ast_slicer = CodeASTSlicer()
payment_gw = X402PaymentGateway()


async def homepage(request):
    index_path = os.path.join("web", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>SOUQ Autonomous Agent Commerce</h1>")


async def well_known_mcp(request):
    mcp_json_path = os.path.join("web", ".well-known", "mcp.json")
    if os.path.exists(mcp_json_path):
        return FileResponse(mcp_json_path, media_type="application/json")
    return JSONResponse({"status": "active", "tools": ["token_compressor", "quant_radar"]})


async def health(request):
    return JSONResponse({
        "status": "healthy",
        "service": "souq-commerce-swarm",
        "network": "Base",
        "currency": "USDC",
        "a2a_rail": "x402-v1.0"
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

    # Pricing table
    prices = {
        "token_context_compressor": 0.01,
        "ast_structural_slicer": 0.02,
        "quant_microstructure_radar": 0.02,
        "ast_security_scanner": 0.03,
        "synthetic_schema_verifier": 0.01
    }

    price = prices.get(tool_name, 0.02)

    if not payment_tx:
        challenge = payment_gw.generate_402_challenge(
            tool_name=tool_name,
            price_usdc=price,
            client_agent_id=request.headers.get("User-Agent", "anonymous-agent")
        )
        return JSONResponse(challenge, status_code=402)

    simulate = payment_tx.startswith("0x_simulated_") or payment_tx.startswith("0x_test_")
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
    elif tool_name == "ast_security_scanner":
        res = security_scanner.scan_python_code(body.get("source_code", ""))
    else:
        res = {"status": "success", "message": f"Tool '{tool_name}' executed."}

    res["settlement_receipt"] = settlement
    return JSONResponse(res)


routes = [
    Route("/", homepage),
    Route("/health", health),
    Route("/.well-known/mcp.json", well_known_mcp),
    Route("/api/tools/call", api_tool_call, methods=["POST"]),
]

app = Starlette(debug=False, routes=routes)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 SOUQ Koyeb Server starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
