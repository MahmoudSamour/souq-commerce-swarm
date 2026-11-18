"""
SOUQ // Real-Time HTTP Traffic & Agent Telemetry Engine
Records every incoming human, agent, bot, and crawler request into DuckDB.
Provides aggregated traffic analytics, user-agent categorization, and commercial conversion funnel telemetry.
"""

import os
import hashlib
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from agents.treasury.db_backend import (
    resolve_db_target,
    db_transaction,
    ensure_parent_dir,
)

logger = logging.getLogger("souq.telemetry")
SALT = os.getenv("SOUQ_IP_SALT", "souq_telemetry_salt_2026")


class TrafficTelemetryEngine:
    """
    High-performance telemetry logger and aggregator for SOUQ edge server.
    Thread-safe DuckDB/PostgreSQL recording with client IP hashing and AI agent detection.
    """

    def __init__(self, db_path: str = "data/souq_treasury_lake.duckdb"):
        self.db_path = db_path
        self.db_target, self.is_postgres = resolve_db_target(db_path)
        if not self.is_postgres:
            ensure_parent_dir(self.db_target)
        self._init_db()

    def _init_db(self) -> None:
        try:
            with db_transaction(self.db_target, read_only=False) as con:
                con.execute("""
                    CREATE TABLE IF NOT EXISTS http_traffic_telemetry (
                        request_id VARCHAR PRIMARY KEY,
                        timestamp_utc TIMESTAMP NOT NULL,
                        method VARCHAR NOT NULL,
                        endpoint VARCHAR NOT NULL,
                        status_code INTEGER NOT NULL,
                        client_ip_hash VARCHAR NOT NULL,
                        user_agent VARCHAR,
                        client_category VARCHAR NOT NULL, -- 'AI_AGENT', 'MCP_CLIENT', 'SEARCH_BOT', 'BROWSER_HUMAN', 'CLI_TOOL', 'UNKNOWN'
                        tool_name VARCHAR,
                        billing_status VARCHAR,            -- 'FREE_DISCOVERY', 'FREE_TRIAL', 'HTTP_402_CHALLENGE', 'PAID_SETTLED', 'RATE_LIMITED', 'ERROR'
                        duration_ms INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        except Exception as e:
            logger.error(f"Failed to initialize telemetry database: {e}")

    @staticmethod
    def hash_ip(ip: str) -> str:
        """One-way salted-hash of client IP for GDPR/privacy compliance."""
        if not ip or ip == "unknown":
            return "anon_unknown"
        salt = os.getenv("SOUQ_IP_SALT", SALT)
        return hashlib.sha256(f"{salt}_{ip}".encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def categorize_user_agent(
        ua_raw: Optional[str],
        endpoint: Optional[str] = None,
        client_header: Optional[str] = None,
    ) -> str:
        """Classifies incoming HTTP traffic by client category."""
        if (client_header or "").strip().lower() == "mcp" or (endpoint or "").startswith("/mcp"):
            return "MCP_CLIENT"

        if not ua_raw:
            return "UNKNOWN"
        ua = ua_raw.lower()

        # Developer CLI / Script Clients
        cli_signals = [
            "curl", "httpie", "wget", "souq-mcp", "python-requests",
            "python-urllib", "httpx", "aiohttp", "postman", "insomnia"
        ]
        if any(signal in ua for signal in cli_signals):
            return "CLI_TOOL"

        # Autonomous AI Agents & Coding IDE Extensions
        ai_agent_signals = [
            "claude", "cursor", "windsurf", "gpt", "agent", "langchain",
            "crewai", "autogen", "smithery", "copilot", "codeium",
            "supermaven", "fastmcp", "mcp-client", "anthropic"
        ]
        if any(signal in ua for signal in ai_agent_signals):
            return "AI_AGENT"

        # Search Engine Crawlers & AEO Bots
        bot_signals = [
            "bingbot", "googlebot", "yandex", "seznam", "duckduckgo",
            "baiduspider", "slurp", "applebot", "ia_archiver", "indexnow", "semrush"
        ]
        if any(signal in ua for signal in bot_signals):
            return "SEARCH_BOT"

        # Browsers (Human traffic)
        if any(b in ua for b in ["mozilla", "chrome", "safari", "firefox", "edge"]):
            return "BROWSER_HUMAN"

        return "UNKNOWN"

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        client_ip: str,
        user_agent: Optional[str],
        tool_name: Optional[str] = None,
        billing_status: Optional[str] = None,
        duration_ms: int = 0,
        client_header: Optional[str] = None,
    ) -> str:
        """Records a single HTTP request event into DuckDB/PostgreSQL."""
        req_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)
        ip_hash = self.hash_ip(client_ip)
        category = self.categorize_user_agent(
            user_agent, endpoint=endpoint, client_header=client_header
        )

        if not billing_status:
            if endpoint.startswith("/api/tools/call"):
                billing_status = "HTTP_402_CHALLENGE" if status_code == 402 else "TOOL_CALL"
            elif status_code == 429:
                billing_status = "RATE_LIMITED"
            elif status_code >= 400:
                billing_status = "ERROR"
            else:
                billing_status = "FREE_DISCOVERY"

        try:
            with db_transaction(self.db_target, read_only=False) as con:
                con.execute("""
                    INSERT INTO http_traffic_telemetry (
                        request_id, timestamp_utc, method, endpoint, status_code,
                        client_ip_hash, user_agent, client_category, tool_name,
                        billing_status, duration_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    req_id, now, method, endpoint, status_code,
                    ip_hash, (user_agent or "")[:255], category, tool_name,
                    billing_status, duration_ms
                ))
        except Exception as e:
            logger.warning(f"Error logging telemetry for {endpoint}: {e}")

        return req_id

    def get_traffic_summary(self) -> Dict[str, Any]:
        """Calculates comprehensive traffic metrics and conversion funnel."""
        try:
            with db_transaction(self.db_target, read_only=True) as con:
                total_row = con.execute("SELECT COUNT(*) FROM http_traffic_telemetry").fetchone()
                total_hits = int(total_row[0]) if total_row else 0

                if total_hits == 0:
                    return {
                        "total_requests": 0,
                        "unique_visitors": 0,
                        "client_categories": {},
                        "billing_funnel": {},
                        "top_endpoints": [],
                        "top_tools": [],
                        "recent_activity": []
                    }

                uniq_row = con.execute("SELECT COUNT(DISTINCT client_ip_hash) FROM http_traffic_telemetry").fetchone()
                unique_visitors = int(uniq_row[0]) if uniq_row else 0

                cat_rows = con.execute("""
                    SELECT client_category, COUNT(*) as cnt
                    FROM http_traffic_telemetry
                    GROUP BY client_category
                    ORDER BY cnt DESC
                """).fetchall()
                client_categories = {r[0]: int(r[1]) for r in cat_rows}

                bill_rows = con.execute("""
                    SELECT billing_status, COUNT(*) as cnt
                    FROM http_traffic_telemetry
                    GROUP BY billing_status
                    ORDER BY cnt DESC
                """).fetchall()
                billing_funnel = {r[0]: int(r[1]) for r in bill_rows}

                ep_rows = con.execute("""
                    SELECT endpoint, COUNT(*) as cnt
                    FROM http_traffic_telemetry
                    GROUP BY endpoint
                    ORDER BY cnt DESC
                    LIMIT 10
                """).fetchall()
                top_endpoints = [{"endpoint": r[0], "hits": int(r[1])} for r in ep_rows]

                tool_rows = con.execute("""
                    SELECT tool_name, COUNT(*) as cnt
                    FROM http_traffic_telemetry
                    WHERE tool_name IS NOT NULL AND tool_name != ''
                    GROUP BY tool_name
                    ORDER BY cnt DESC
                    LIMIT 10
                """).fetchall()
                top_tools = [{"tool": r[0], "invocations": int(r[1])} for r in tool_rows]

                rec_rows = con.execute("""
                    SELECT request_id, timestamp_utc, method, endpoint, status_code,
                           client_category, tool_name, billing_status, duration_ms
                    FROM http_traffic_telemetry
                    ORDER BY timestamp_utc DESC
                    LIMIT 20
                """).fetchall()
                recent_activity = [
                    {
                        "request_id": r[0],
                        "timestamp": r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1]),
                        "method": r[2],
                        "endpoint": r[3],
                        "status_code": int(r[4]),
                        "client_category": r[5],
                        "tool": r[6],
                        "billing_status": r[7],
                        "latency_ms": int(r[8])
                    }
                    for r in rec_rows
                ]

                return {
                    "total_requests": total_hits,
                    "unique_visitors": unique_visitors,
                    "client_categories": client_categories,
                    "billing_funnel": billing_funnel,
                    "top_endpoints": top_endpoints,
                    "top_tools": top_tools,
                    "recent_activity": recent_activity
                }
        except Exception as e:
            logger.error(f"Error fetching traffic summary: {e}")
            return {
                "error": str(e),
                "total_requests": 0,
                "unique_visitors": 0,
                "client_categories": {},
                "billing_funnel": {},
                "top_endpoints": [],
                "top_tools": [],
                "recent_activity": [],
            }

    def get_summary(self) -> Dict[str, Any]:
        """Alias for get_traffic_summary()."""
        return self.get_traffic_summary()
