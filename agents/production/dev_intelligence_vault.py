"""
SOUQ // Developer Intelligence & API Cheat Sheet Vault
Exposes high-density, pre-cleaned API schemas and daily AI/tech trends for autonomous agents.
Saves AI coding agents 30,000 - 80,000 prompt tokens per invocation.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
import re
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

import requests


class DevAPICheatSheetVault:
    """
    Provides ultra-compressed, zero-fluff API schemas and code patterns
    for the top developer ecosystems. Eliminates massive HTML web scraping bills.
    """

    VAULT = {
        "openai": {
            "title": "OpenAI Structured Outputs & Tools Spec",
            "version": "2026-v3",
            "primary_endpoints": [
                "POST /v1/responses (model, input, instructions, tools, text.format, reasoning)",
                "POST /v1/chat/completions (model, messages, tools, tool_choice, response_format)"
            ],
            "optimal_params": {
                "responses_structured_output": {
                    "format": {"type": "json_schema", "name": "result", "strict": True, "schema": "{...}"}
                },
                "chat_structured_output": {"type": "json_schema", "json_schema": {"name": "result", "strict": True, "schema": "{...}"}},
                "reasoning": {"effort": "low | medium | high"}
            },
            "clean_snippet": (
                "from openai import OpenAI\n"
                "client = OpenAI()\n"
                "resp = client.responses.create(\n"
                "    model='gpt-4.1',\n"
                "    input=prompt,\n"
                "    text={'format': {'type': 'json_schema', 'name': 'out', 'schema': schema, 'strict': True}}\n"
                ")"
            ),
            "tokens_saved": 40000
        },
        "anthropic": {
            "title": "Anthropic Claude Messages & Extended Thinking Spec",
            "version": "2026-v2",
            "primary_endpoints": [
                "POST /v1/messages (model, max_tokens, system, messages, tools, tool_choice, thinking)"
            ],
            "optimal_params": {
                "recommended_models": ["claude-sonnet-4-5", "claude-opus-4-1", "claude-haiku-4-5"],
                "thinking": {"type": "enabled", "budget_tokens": 2048},
                "tools": [{"name": "tool_name", "description": "...", "input_schema": {"type": "object"}}]
            },
            "clean_snippet": (
                "import anthropic\n"
                "client = anthropic.Anthropic()\n"
                "msg = client.messages.create(\n"
                "    model='claude-sonnet-4-5',\n"
                "    max_tokens=4096,\n"
                "    messages=[{'role': 'user', 'content': prompt}]\n"
                ")"
            ),
            "tokens_saved": 35000
        },
        "stripe": {
            "title": "Stripe Payment Intents & Billing x402 Architecture",
            "version": "2026-02",
            "primary_endpoints": [
                "POST /v1/payment_intents (amount, currency, automatic_payment_methods)",
                "POST /v1/checkout/sessions (mode, line_items, success_url, cancel_url)"
            ],
            "webhook_events": ["payment_intent.succeeded", "checkout.session.completed", "customer.subscription.deleted"],
            "clean_snippet": (
                "from stripe import StripeClient\n"
                "client = StripeClient(api_key)\n"
                "pi = client.payment_intents.create(params={'amount': 2000, 'currency': 'usd', 'automatic_payment_methods': {'enabled': True}})"
            ),
            "tokens_saved": 50000
        },
        "base_evm": {
            "title": "Base L2 EVM Quick Reference (Chain ID 8453)",
            "version": "Bedrock/Cancun/Pectra",
            "core_contracts": {
                "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "weth": "0x4200000000000000000000000000000000000006"
            },
            "rpc_methods": ["eth_sendRawTransaction", "eth_call", "eth_getTransactionReceipt", "eth_estimateGas"],
            "erc20_transfer_topic": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "clean_snippet": "web3.eth.contract(address=USDC, abi=ERC20_ABI).functions.transfer(recipient, amount).transact({'from': sender})",
            "tokens_saved": 45000
        },
        "fastmcp": {
            "title": "MCP & FastMCP Streamable HTTP Server Protocol Specification",
            "version": "MCP-2025-11 / PySDK-1.x",
            "transports": ["streamable-http", "stdio"],
            "tool_decorator": "@mcp.tool(name='...', description='...')",
            "python_sdk_snippet": (
                "from mcp.server.fastmcp import FastMCP\n"
                "mcp = FastMCP('server-name', stateless_http=True)\n"
                "@mcp.tool()\n"
                "def ping() -> str:\n"
                "    return 'pong'\n"
                "mcp.run(transport='streamable-http')"
            ),
            "typescript_sdk_snippet": (
                "import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';\n"
                "import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';\n"
                "const server = new McpServer({ name: 'server-name', version: '1.0.0' });\n"
                "const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });\n"
                "await server.connect(transport);"
            ),
            "clean_snippet": (
                "from mcp.server.fastmcp import FastMCP\n"
                "mcp = FastMCP('server-name', stateless_http=True)\n"
                "@mcp.tool()\n"
                "def ping() -> str:\n"
                "    return 'pong'\n"
                "mcp.run(transport='streamable-http')"
            ),
            "tokens_saved": 25000
        },
        "mcp": {
            "title": "Model Context Protocol (MCP) Streamable HTTP Python & TypeScript SDK Spec",
            "version": "2025-11-25",
            "transports": ["streamable-http", "stdio"],
            "endpoints": [
                "POST /mcp (JSON-RPC 2.0 request/batch; returns application/json or text/event-stream)",
                "GET /mcp (optional SSE server-initiated stream)",
                "DELETE /mcp (session termination via Mcp-Session-Id header)"
            ],
            "python_sdk_snippet": (
                "from mcp.server.fastmcp import FastMCP\n"
                "mcp = FastMCP('souq-mcp', stateless_http=True)\n"
                "@mcp.tool()\n"
                "def health() -> str:\n"
                "    return 'ok'\n"
                "app = mcp.streamable_http_app()"
            ),
            "typescript_sdk_snippet": (
                "import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';\n"
                "import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';\n"
                "const server = new McpServer({ name: 'souq-mcp', version: '1.0.0' });\n"
                "const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: () => crypto.randomUUID() });\n"
                "await server.connect(transport);\n"
                "await transport.handleRequest(req, res, req.body);"
            ),
            "clean_snippet": (
                "from mcp.server.fastmcp import FastMCP\n"
                "mcp = FastMCP('souq-mcp', stateless_http=True)\n"
                "@mcp.tool()\n"
                "def health() -> str:\n"
                "    return 'ok'\n"
                "mcp.run(transport='streamable-http')"
            ),
            "tokens_saved": 35000
        },
        "duckdb": {
            "title": "DuckDB Embedded Analytics & Parquet Lake Reference",
            "version": "1.2.x",
            "best_practices": [
                "Use 'read_parquet()' with pushdown projection",
                "Execute 'INSERT INTO table SELECT * FROM ... ON CONFLICT DO NOTHING'",
                "Set memory_limit='256MB' on container environments"
            ],
            "clean_snippet": "con = duckdb.connect('lake.duckdb')\ncon.execute('CREATE TABLE IF NOT EXISTS metrics AS SELECT * FROM read_parquet(\"data/*.parquet\")')",
            "tokens_saved": 30000
        }
    }

    CHEAT_SHEETS = VAULT

    def get_api_cheatsheet(self, ecosystem: str = "openai") -> Dict[str, Any]:
        start_t = time.time()
        eco_key = (ecosystem or "").lower().strip()
        data = self.VAULT.get(eco_key)

        if not data:
            available = list(self.VAULT.keys())
            return {
                "status": "error",
                "message": f"Ecosystem '{ecosystem}' not found.",
                "available_ecosystems": available,
                "hint": "Call with one of the available keys to save 30k+ tokens."
            }

        latency_ms = int((time.time() - start_t) * 1000)
        return {
            "status": "success",
            "ecosystem": eco_key,
            "timestamp_ms": int(time.time() * 1000),
            "cheatsheet": data,
            "tokens_saved_estimate": data.get("tokens_saved", 35000),
            "latency_ms": latency_ms,
            "disclaimer": "Clean-room compressed developer reference for autonomous coding agents."
        }


class DailyTechTrendsRadar:
    """
    Daily high-density snapshot of breaking AI and developer technology:
    - Top trending GitHub AI repositories & release breakthroughs
    - Top HackerNews discussions filtered for software/AI/crypto/engineering relevance
    - Landmark arXiv AI architectures
    """

    CACHE_PATH = os.path.join("data", "cache", "daily_tech_radar_latest.json")
    FORCE_REFRESH_COOLDOWN_S = 60.0
    CACHE_TTL_S = 21600.0

    _CACHE_LOCK = threading.Lock()
    _LAST_REFRESH_BY_PATH: Dict[str, float] = {}

    _HN_RELEVANCE_RE = re.compile(
        r"\b(?:"
        r"ai|llm|llms|gpt|claude|anthropic|openai|gemini|deepseek|llama|mistral|qwen|"
        r"model|models|neural|transformer|agent|agents|mcp|rag|inference|gpu|cuda|vllm|arxiv|"
        r"python|rust|typescript|javascript|golang|c\+\+|linux|kernel|compiler|ast|"
        r"database|sql|postgres|postgresql|sqlite|duckdb|redis|docker|kubernetes|git|github|"
        r"open[- ]source|api|http|tcp|security|vulnerability|cve|zero[- ]day|encryption|"
        r"wasm|webassembly|cloud|aws|serverless|cli|ide|framework|sdk|algorithm|software|"
        r"programming|coding|engineering|benchmark|latency|distributed|protocol|"
        r"crypto|bitcoin|btc|ethereum|eth|solana|base|evm|solidity|defi|usdc|stablecoin|"
        r"blockchain|zero[- ]knowledge|zk|wallet|smart[- ]contract|polymarket|x402"
        r")\b",
        re.IGNORECASE,
    )
    _HN_TECH_DOMAINS = (
        "github.com",
        "arxiv.org",
        "huggingface.co",
        "pypi.org",
        "npmjs.com",
        "openai.com",
        "anthropic.com",
        "ethereum.org",
        "docs.",
    )

    def __init__(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.CACHE_PATH)), exist_ok=True)

    @classmethod
    def _is_relevant_hn_story(cls, title: str, url: str) -> bool:
        if cls._HN_RELEVANCE_RE.search(title or ""):
            return True
        low_url = (url or "").lower()
        return any(dom in low_url for dom in cls._HN_TECH_DOMAINS)

    @staticmethod
    def _fetch_live_github_repos(timeout_s: float = 3.0) -> List[Dict[str, Any]]:
        since_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": f"(mcp OR \"ai agent\" OR llm) pushed:>={since_date} stars:>=500",
                "sort": "stars",
                "order": "desc",
                "per_page": 5,
            },
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "SOUQ-Tech-Radar/0.3",
            },
            timeout=timeout_s,
        )
        resp.raise_for_status()
        items = resp.json().get("items") or []
        return [
            {
                "repo": item.get("full_name"),
                "stars": int(item.get("stargazers_count", 0)),
                "category": item.get("language") or "AI/Agents",
                "signal": (item.get("description") or "High-velocity AI/MCP open-source repository.")[:180],
                "url": item.get("html_url"),
            }
            for item in items[:5]
            if item.get("full_name")
        ]

    @classmethod
    def _fetch_live_hackernews(cls, timeout_s: float = 3.0) -> List[Dict[str, Any]]:
        ids_resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=timeout_s,
        )
        ids_resp.raise_for_status()
        top_ids = (ids_resp.json() or [])[:30]

        def _get_item(item_id: int) -> Optional[Dict[str, Any]]:
            try:
                r = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                    timeout=timeout_s,
                )
                r.raise_for_status()
                return r.json()
            except Exception:
                return None

        stories: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=8) as pool:
            for item in pool.map(_get_item, top_ids):
                if not item or not item.get("title"):
                    continue
                title = str(item.get("title"))
                story_url = str(item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}")
                if not cls._is_relevant_hn_story(title, story_url):
                    continue
                stories.append({
                    "headline": title,
                    "points": int(item.get("score") or 0),
                    "url": story_url,
                    "relevance": "Live HackerNews software/AI/crypto engineering telemetry.",
                })
        stories.sort(key=lambda s: s["points"], reverse=True)
        return stories[:5]

    @staticmethod
    def _fetch_live_arxiv(timeout_s: float = 3.5) -> List[Dict[str, Any]]:
        resp = requests.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": "cat:cs.AI OR cat:cs.CL",
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": 3,
            },
            headers={"User-Agent": "SOUQ-Tech-Radar/0.3"},
            timeout=timeout_s,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers: List[Dict[str, Any]] = []
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            id_el = entry.find("atom:id", ns)
            sum_el = entry.find("atom:summary", ns)
            raw_id = (id_el.text or "").strip().split("/abs/")[-1] if id_el is not None else ""
            summary = " ".join(((sum_el.text if sum_el is not None else "") or "").split())[:220]
            if title_el is not None and title_el.text:
                papers.append({
                    "title": " ".join(title_el.text.split()),
                    "paper_id": raw_id,
                    "takeaway": summary,
                })
        return papers

    def _read_cache_file(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.CACHE_PATH):
            return None
        try:
            with open(self.CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get("data_source") != "curated_fallback":
                if data.get("trending_github_ai_repos") or data.get("hackernews_breakouts"):
                    return data
        except Exception:
            return None
        return None

    def _write_cache_atomic(self, payload: Dict[str, Any]) -> None:
        cache_dir = os.path.dirname(os.path.abspath(self.CACHE_PATH))
        os.makedirs(cache_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tech_radar_", suffix=".tmp", dir=cache_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(payload, tmp_file, indent=2)
            os.replace(tmp_path, self.CACHE_PATH)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise

    def refresh_cache_and_get(self, force_refresh: bool = False) -> Dict[str, Any]:
        start_t = time.time()
        abs_cache_path = os.path.abspath(self.CACHE_PATH)

        with self._CACHE_LOCK:
            now = time.time()
            cached = self._read_cache_file()

            if cached is not None:
                cached_age = now - float(cached.get("generated_at_unix", 0))
                if not force_refresh and cached_age < self.CACHE_TTL_S:
                    result = dict(cached)
                    result["cache_hit"] = True
                    result["latency_ms"] = int((time.time() - start_t) * 1000)
                    return result

                last_force_ts = self._LAST_REFRESH_BY_PATH.get(abs_cache_path, 0.0)
                if force_refresh and (
                    (now - last_force_ts) < self.FORCE_REFRESH_COOLDOWN_S
                    or cached_age < self.FORCE_REFRESH_COOLDOWN_S
                ):
                    result = dict(cached)
                    result["cache_hit"] = True
                    result["cooldown_active"] = True
                    result["latency_ms"] = int((time.time() - start_t) * 1000)
                    return result

            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            live_sources: List[str] = []
            gh_repos: List[Dict[str, Any]] = []
            hn_stories: List[Dict[str, Any]] = []
            arxiv_papers: List[Dict[str, Any]] = []

            with ThreadPoolExecutor(max_workers=3) as pool:
                gh_fut = pool.submit(self._fetch_live_github_repos)
                hn_fut = pool.submit(self._fetch_live_hackernews)
                ax_fut = pool.submit(self._fetch_live_arxiv)

                try:
                    fetched_gh = gh_fut.result(timeout=4.5)
                    if fetched_gh:
                        gh_repos = fetched_gh
                        live_sources.append("github_api")
                except Exception:
                    gh_repos = []

                try:
                    fetched_hn = hn_fut.result(timeout=4.5)
                    if fetched_hn:
                        hn_stories = fetched_hn
                        live_sources.append("hackernews_api")
                except Exception:
                    hn_stories = []

                try:
                    fetched_ax = ax_fut.result(timeout=4.5)
                    if fetched_ax:
                        arxiv_papers = fetched_ax
                        live_sources.append("arxiv_api")
                except Exception:
                    arxiv_papers = []

            # Never fabricate fake success data when both primary live feeds fail
            if not gh_repos and not hn_stories:
                if cached is not None:
                    stale_payload = dict(cached)
                    stale_payload["status"] = "stale_cache"
                    stale_payload["cache_hit"] = True
                    stale_payload["stale_reason"] = "Live GitHub and HackerNews feeds unavailable; serving last cached digest."
                    stale_payload["latency_ms"] = int((time.time() - start_t) * 1000)
                    return stale_payload

                return {
                    "status": "upstream_unavailable",
                    "error": "Live GitHub and HackerNews feeds failed and no cached digest is available.",
                    "digest_date": today_str,
                    "generated_at_unix": int(now),
                    "cache_hit": False,
                    "live_sources": live_sources,
                    "trending_github_ai_repos": [],
                    "hackernews_breakouts": [],
                    "arxiv_landmark_papers": arxiv_papers,
                    "latency_ms": int((time.time() - start_t) * 1000),
                }

            daily_digest = {
                "status": "success",
                "data_source": "+".join(live_sources),
                "digest_date": today_str,
                "generated_at_unix": int(now),
                "cache_hit": False,
                "trending_github_ai_repos": gh_repos,
                "hackernews_breakouts": hn_stories,
                "arxiv_landmark_papers": arxiv_papers,
                "tokens_saved_estimate": 25000,
                "latency_ms": int((time.time() - start_t) * 1000),
                "disclaimer": "Aggregated daily intelligence digest for autonomous researchers and agents.",
            }

            try:
                self._write_cache_atomic(daily_digest)
                self._LAST_REFRESH_BY_PATH[abs_cache_path] = time.time()
            except Exception:
                pass

            return daily_digest
