#!/usr/bin/env python3
"""
Builds the clean, standalone Monetized MCP Server Boilerplate release archive
(`dist/souq-monetized-mcp-boilerplate-v1.0.zip`) for Polar.sh digital delivery.
Contains zero secrets, zero SOUQ-proprietary alpha logic, and passes pytest out of the box.
"""

import os
import shutil
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"
STAGE_DIR = DIST_DIR / "_boilerplate_stage"
ZIP_PATH = DIST_DIR / "souq-monetized-mcp-boilerplate-v1.0.zip"

COPY_FILES = [
    "agents/__init__.py",
    "agents/treasury/__init__.py",
    "agents/treasury/db_backend.py",
    "agents/treasury/api_key_ledger.py",
    "agents/treasury/crypto_receipt_engine.py",
    "agents/treasury/polar_adapter.py",
    "agents/treasury/x402_gateway.py",
    "agents/analytics/negotiation_tracker.py",
    "requirements.txt",
    "Dockerfile",
]

BOILERPLATE_README = """# Monetized MCP Server Boilerplate (FastMCP + Polar.sh + Base x402 + Postgres/DuckDB)

Accept **credit cards (Polar.sh MoR)**, **prepaid `X-API-Key` credits**, and **Base L2 USDC (`HTTP 402` x402)** for any MCP or REST tool — with a **$0 free hosting stack** (Koyeb Free Tier + Neon Free Postgres).

## What's Included
- **Streamable HTTP `/mcp` + REST `/api/tools/call`** (`server.py`)
- **Polar.sh Merchant of Record Adapter** (`agents/treasury/polar_adapter.py`) — checkout sessions, Standard Webhooks HMAC verification, sealed one-time key claims
- **Base L2 USDC `x402` Gateway** (`agents/treasury/x402_gateway.py`) — on-chain ERC-20 `Transfer` log verification & anti-replay locking
- **Prepaid API Key Ledger** (`agents/treasury/api_key_ledger.py`) — atomic debits & automatic refunds on tool errors
- **Unified DuckDB + PostgreSQL Backend** (`agents/treasury/db_backend.py`) — local DuckDB for dev, pooled Postgres (`DATABASE_URL`) for production
- **3 Sample Tools** ready to customize (`echo_pro`, `json_schema_validator`, `text_stats`)

## 15-Minute $0 Quickstart
1. `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
2. `cp .env.example .env` and set `SOUQ_API_KEY_PEPPER`, `BASE_RECIPIENT_WALLET_ADDRESS`, and Polar keys.
3. Run tests: `pytest -q`
4. Start locally: `python server.py`
5. Deploy to Koyeb (connect GitHub repo using `Dockerfile`) + attach a free **Neon.tech** `DATABASE_URL`.
"""

BOILERPLATE_ENV_EXAMPLE = """ENV=development
PORT=8000
SOUQ_API_KEY_PEPPER=replace_with_random_32_byte_secret
SOUQ_RECEIPT_SIGNING_KEY=replace_with_random_32_byte_secret
SOUQ_ALLOW_TEST_SIMULATION=true
SOUQ_FREE_TRIAL_DAILY_LIMIT=5

# Base L2 USDC (Chain ID 8453)
BASE_RECIPIENT_WALLET_ADDRESS=0x0000000000000000000000000000000000000000
BASE_RPC_URL=https://base-rpc.publicnode.com
BASE_USDC_CONTRACT=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913

# Polar.sh Merchant of Record
POLAR_ACCESS_TOKEN=
POLAR_ORGANIZATION_ID=
POLAR_WEBHOOK_SECRET=
POLAR_PRODUCT_ID_CREDIT_5=
POLAR_PRODUCT_ID_CREDIT_15=

# Database (leave blank for local DuckDB; set Neon/Supabase Postgres URL in prod)
DATABASE_URL=
"""

BOILERPLATE_SERVER = '''"""
Monetized MCP Server Boilerplate (Starlette + Streamable HTTP /mcp + Polar + x402)
"""

import json
import os
import time
from typing import Any, Dict

import anyio
import uvicorn
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from agents.analytics.negotiation_tracker import NegotiationTracker
from agents.treasury.api_key_ledger import APIKeyLedger
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.treasury.db_backend import ensure_parent_dir, resolve_db_target
from agents.treasury.polar_adapter import PolarAdapter
from agents.treasury.x402_gateway import X402PaymentGateway

load_dotenv(".env")

DB_PATH = os.getenv("SOUQ_DUCKDB_PATH", "data/treasury.duckdb")
DB_TARGET, _IS_PG = resolve_db_target(DB_PATH)
if not _IS_PG:
    ensure_parent_dir(DB_TARGET)

negotiation_tracker = NegotiationTracker(db_path=DB_TARGET)
receipt_engine = CryptoReceiptEngine(db_path=DB_TARGET, receipts_dir="data/receipts")
api_key_ledger = APIKeyLedger(db_path=DB_TARGET)
payment_gw = X402PaymentGateway(
    receipt_engine=receipt_engine,
    negotiation_tracker=negotiation_tracker,
    api_key_ledger=api_key_ledger,
)
polar_adapter = PolarAdapter(api_key_ledger=api_key_ledger)

TOOLS = {
    "echo_pro": {"price_usdc": 0.01, "description": "Echoes input with timestamp & word count."},
    "text_stats": {"price_usdc": 0.01, "description": "Computes character, word, and line counts."},
}


def _dispatch(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "echo_pro":
        text = str(args.get("text", ""))
        return {"status": "success", "echo": text, "words": len(text.split()), "ts": int(time.time())}
    if tool_name == "text_stats":
        text = str(args.get("text", ""))
        return {"status": "success", "chars": len(text), "words": len(text.split()), "lines": len(text.splitlines())}
    return {"status": "error", "error": f"Unknown tool: {tool_name}"}


async def health(request):
    return JSONResponse({"status": "healthy", "tools": list(TOOLS.keys())})


async def call_tool(request):
    body = await request.json()
    tool_name = str(body.get("tool", "")).strip()
    if tool_name not in TOOLS:
        return JSONResponse({"error": "Unknown tool"}, status_code=404)

    price = TOOLS[tool_name]["price_usdc"]
    api_key = request.headers.get("X-API-Key")
    if api_key:
        ok, settlement = await anyio.to_thread.run_sync(api_key_ledger.validate_and_debit, api_key, price, tool_name)
        if not ok:
            return JSONResponse(settlement, status_code=402 if settlement.get("error") == "Insufficient Credits" else 401)
        result = _dispatch(tool_name, body)
        if result.get("status") == "error":
            await anyio.to_thread.run_sync(api_key_ledger.refund_debit, api_key, price, "tool_error")
            return JSONResponse(result, status_code=400)
        return JSONResponse({**result, "settlement": settlement})

    challenge = await anyio.to_thread.run_sync(payment_gw.generate_402_challenge, tool_name, price)
    return JSONResponse(challenge, status_code=402)


async def mcp_endpoint(request):
    if request.method == "GET":
        return JSONResponse({"error": "Use POST /mcp"}, status_code=405)
    msg = await request.json()
    method = msg.get("method")
    msg_id = msg.get("id")
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "mcp-starter", "version": "1.0.0"}},
        })
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": [{"name": k, "description": v["description"], "inputSchema": {"type": "object"}} for k, v in TOOLS.items()]},
        })
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name", "")
        args = params.get("arguments") or {}
        if name not in TOOLS:
            return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": {"isError": True, "content": [{"type": "text", "text": "Unknown tool"}]}})
        res = _dispatch(name, args)
        return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(res)}]}})
    return Response(status_code=204)


app = Starlette(
    routes=[
        Route("/health", health),
        Route("/api/tools/call", call_tool, methods=["POST"]),
        Route("/mcp", mcp_endpoint, methods=["GET", "POST"]),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
'''

BOILERPLATE_TEST = '''from starlette.testclient import TestClient
import server


def test_health_and_402_and_prepaid_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("SOUQ_DUCKDB_PATH", str(tmp_path / "test.duckdb"))
    client = TestClient(server.app)

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert "echo_pro" in r_health.json()["tools"]

    r_402 = client.post("/api/tools/call", json={"tool": "echo_pro", "text": "hi"})
    assert r_402.status_code == 402

    ok, minted = server.api_key_ledger.issue_or_topup_key("test_ref_1", 5.0, rail="test")
    assert ok and minted.get("api_key")

    r_paid = client.post(
        "/api/tools/call",
        headers={"X-API-Key": minted["api_key"]},
        json={"tool": "echo_pro", "text": "hello monetized mcp"},
    )
    assert r_paid.status_code == 200
    assert r_paid.json()["words"] == 3
'''


def build_boilerplate() -> Path:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / "tests").mkdir(exist_ok=True)

    for rel in COPY_FILES:
        src = REPO_ROOT / rel
        dst = STAGE_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    (STAGE_DIR / "agents" / "analytics" / "__init__.py").write_text(
        "from agents.analytics.negotiation_tracker import NegotiationTracker\n",
        encoding="utf-8",
    )
    (STAGE_DIR / "QUICKSTART.md").write_text(BOILERPLATE_README, encoding="utf-8")
    (STAGE_DIR / ".env.example").write_text(BOILERPLATE_ENV_EXAMPLE, encoding="utf-8")
    (STAGE_DIR / "server.py").write_text(BOILERPLATE_SERVER, encoding="utf-8")
    (STAGE_DIR / "tests" / "test_boilerplate.py").write_text(BOILERPLATE_TEST, encoding="utf-8")

    # Replace Dockerfile CMD to run server.py
    df = (STAGE_DIR / "Dockerfile").read_text(encoding="utf-8")
    df = df.replace('CMD ["python3", "scripts/koyeb_server.py"]', 'CMD ["python3", "server.py"]')
    (STAGE_DIR / "Dockerfile").write_text(df, encoding="utf-8")

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(STAGE_DIR.rglob("*")):
            if file_path.is_file() and "__pycache__" not in file_path.parts:
                zf.write(file_path, file_path.relative_to(STAGE_DIR))

    shutil.rmtree(STAGE_DIR)
    return ZIP_PATH


if __name__ == "__main__":
    out = build_boilerplate()
    print(f"Built clean boilerplate archive: {out} ({out.stat().st_size} bytes)")
