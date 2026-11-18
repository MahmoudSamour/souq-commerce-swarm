"""
SOUQ // Agent-to-Agent (A2A) Negotiation & Workflow Telemetry Lake
Tracks, analyzes, and learns from machine-to-machine price challenges,
tool requests, and settlement dynamics to optimize pricing and workflows.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from agents.treasury.db_backend import (
    resolve_db_target,
    db_transaction,
    ensure_parent_dir,
)

_PII_KEYS = {"client_ip", "ip", "raw_ip", "authorization", "x_api_key"}


def _sanitize_metadata(value: Any) -> Any:
    """Recursively strips PII and secret credential keys from metadata payloads."""
    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in value.items():
            norm_key = str(k).strip().lower().replace("-", "_")
            if norm_key in _PII_KEYS:
                continue
            cleaned[k] = _sanitize_metadata(v)
        return cleaned
    if isinstance(value, list):
        return [_sanitize_metadata(item) for item in value]
    return value


class NegotiationTracker:
    """
    Records every A2A interaction to refine pricing elasticity, detect unmet demand,
    and optimize autonomous business models.
    """

    def __init__(self, db_path: str = "data/souq_treasury_lake.duckdb"):
        self.db_path = db_path
        self.db_target, self.is_postgres = resolve_db_target(db_path)
        if not self.is_postgres:
            ensure_parent_dir(self.db_target)
        self._init_db()

    def _init_db(self) -> None:
        with db_transaction(self.db_target, read_only=False) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS a2a_negotiations (
                    negotiation_id VARCHAR PRIMARY KEY,
                    timestamp_utc TIMESTAMP NOT NULL,
                    client_agent_id VARCHAR NOT NULL,
                    client_user_agent VARCHAR NOT NULL,
                    tool_requested VARCHAR NOT NULL,
                    initial_quote_usd DECIMAL(10, 4) NOT NULL,
                    settled_price_usd DECIMAL(10, 4),
                    payment_protocol VARCHAR NOT NULL,       -- 'x402_http', 'nevermined', 'direct_rpc'
                    outcome VARCHAR NOT NULL,                -- 'SETTLED', 'PRICE_REJECTED', 'TIMEOUT', 'INVALID_SIG', 'BUDGET_EXCEEDED'
                    latency_ms INTEGER NOT NULL,
                    rejection_reason VARCHAR,
                    metadata_json VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def log_negotiation(
        self,
        client_agent_id: str,
        client_user_agent: str,
        tool_requested: str,
        initial_quote_usd: float,
        settled_price_usd: Optional[float],
        payment_protocol: str,
        outcome: str,
        latency_ms: int,
        rejection_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Logs a single A2A interaction into the negotiation telemetry lake.
        """
        now = datetime.now(timezone.utc)
        negotiation_id = f"NEG-{uuid.uuid4().hex[:12].upper()}"
        sanitized_meta = _sanitize_metadata(metadata or {})
        meta_str = json.dumps(sanitized_meta, default=str)

        with db_transaction(self.db_target, read_only=False) as con:
            con.execute("""
                INSERT INTO a2a_negotiations (
                    negotiation_id, timestamp_utc, client_agent_id, client_user_agent,
                    tool_requested, initial_quote_usd, settled_price_usd, payment_protocol,
                    outcome, latency_ms, rejection_reason, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                negotiation_id, now, client_agent_id, client_user_agent,
                tool_requested, initial_quote_usd, settled_price_usd, payment_protocol,
                outcome, latency_ms, rejection_reason, meta_str
            ))

        return {
            "negotiation_id": negotiation_id,
            "status": outcome,
            "tool": tool_requested,
            "settled_price": settled_price_usd
        }

    def get_market_intelligence_summary(self) -> Dict[str, Any]:
        """
        Computes real-time conversion rates, average revenue per tool,
        and pricing friction points with consistent schema for empty and populated DBs.
        """
        with db_transaction(self.db_target, read_only=True) as con:
            total_row = con.execute("SELECT COUNT(*) FROM a2a_negotiations").fetchone()
            total_requests = int(total_row[0]) if total_row else 0
            if total_requests == 0:
                return {
                    "total_interactions": 0,
                    "successful_settlements": 0,
                    "conversion_rate_pct": 0.0,
                    "tool_telemetry": [],
                    "rejection_analysis": [],
                }

            settled_row = con.execute(
                "SELECT COUNT(*) FROM a2a_negotiations WHERE outcome = 'SETTLED'"
            ).fetchone()
            settled_count = int(settled_row[0]) if settled_row else 0
            conversion_rate = (settled_count / total_requests) * 100.0

            tool_rows = con.execute("""
                SELECT
                    tool_requested,
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN outcome = 'SETTLED' THEN 1 ELSE 0 END) as successful_calls,
                    ROUND(AVG(latency_ms), 1) as avg_latency_ms,
                    ROUND(SUM(COALESCE(settled_price_usd, 0.0)), 4) as total_volume_usd
                FROM a2a_negotiations
                GROUP BY tool_requested
                ORDER BY total_calls DESC
            """).fetchall()
            tool_breakdown: List[Dict[str, Any]] = [
                {
                    "tool_requested": r[0],
                    "total_calls": int(r[1]),
                    "successful_calls": int(r[2] or 0),
                    "avg_latency_ms": float(r[3] or 0.0),
                    "total_volume_usd": float(r[4] or 0.0),
                }
                for r in tool_rows
            ]

            rej_rows = con.execute("""
                SELECT rejection_reason, COUNT(*) as count
                FROM a2a_negotiations
                WHERE outcome != 'SETTLED' AND rejection_reason IS NOT NULL
                GROUP BY rejection_reason
            """).fetchall()
            rejection_stats: List[Dict[str, Any]] = [
                {"rejection_reason": r[0], "count": int(r[1])}
                for r in rej_rows
            ]

        return {
            "total_interactions": total_requests,
            "successful_settlements": settled_count,
            "conversion_rate_pct": round(conversion_rate, 2),
            "tool_telemetry": tool_breakdown,
            "rejection_analysis": rejection_stats,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Alias for get_market_intelligence_summary()."""
        return self.get_market_intelligence_summary()

