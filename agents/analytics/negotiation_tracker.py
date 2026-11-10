"""
SOUQ // Agent-to-Agent (A2A) Negotiation & Workflow Telemetry Lake
Tracks, analyzes, and learns from machine-to-machine price challenges,
tool requests, and settlement dynamics to optimize pricing and workflows.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import duckdb
import pandas as pd


class NegotiationTracker:
    """
    Records every A2A interaction to refine pricing elasticity, detect unmet demand,
    and optimize autonomous business models.
    """

    def __init__(self, db_path: str = "data/souq_treasury_lake.duckdb"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as con:
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
        meta_str = json.dumps(metadata or {}, default=str)

        with self._get_connection() as con:
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
        and pricing friction points.
        """
        with self._get_connection() as con:
            total_requests = con.execute("SELECT COUNT(*) FROM a2a_negotiations").fetchone()[0]
            if total_requests == 0:
                return {
                    "total_interactions": 0,
                    "conversion_rate_pct": 0.0,
                    "top_tools": [],
                    "pricing_friction": "No data yet"
                }

            settled_count = con.execute(
                "SELECT COUNT(*) FROM a2a_negotiations WHERE outcome = 'SETTLED'"
            ).fetchone()[0]

            conversion_rate = (settled_count / total_requests) * 100.0

            # Group by tool breakdown
            tool_breakdown = con.execute("""
                SELECT 
                    tool_requested,
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN outcome = 'SETTLED' THEN 1 ELSE 0 END) as successful_calls,
                    ROUND(AVG(latency_ms), 1) as avg_latency_ms,
                    ROUND(SUM(COALESCE(settled_price_usd, 0.0)), 4) as total_volume_usd
                FROM a2a_negotiations
                GROUP BY tool_requested
                ORDER BY total_calls DESC
            """).fetchdf().to_dict(orient="records")

            # Analyze rejections
            rejection_stats = con.execute("""
                SELECT rejection_reason, COUNT(*) as count
                FROM a2a_negotiations
                WHERE outcome != 'SETTLED' AND rejection_reason IS NOT NULL
                GROUP BY rejection_reason
            """).fetchdf().to_dict(orient="records")

        return {
            "total_interactions": total_requests,
            "successful_settlements": settled_count,
            "conversion_rate_pct": round(conversion_rate, 2),
            "tool_telemetry": tool_breakdown,
            "rejection_analysis": rejection_stats
        }

