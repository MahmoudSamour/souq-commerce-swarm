"""
SOUQ // Buhuth Market Research & Strategy Agent (البحوث)
Autonomous market research analyst for the agent-to-agent economy.
Scans demand trends, benchmarks competitor pricing, reviews proposed catalog items,
and issues strategic directives for product selection and Agent Engine Optimization (AEO).
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class AgentDemandSignal(BaseModel):
    category: str
    target_tool: str
    search_volume_score: float = Field(ge=0.0, le=10.0)
    willingness_to_pay_usdc: float
    competitive_density: str  # "LOW", "MEDIUM", "HIGH"
    key_intent_queries: List[str]
    growth_driver: str


class MarketResearchDirective(BaseModel):
    directive_id: str
    generated_at: float
    market_regime: str
    prioritized_tools: List[str]
    pricing_adjustments: Dict[str, float]
    aeo_target_keywords: List[str]
    strategic_verdict: str


class MarketResearchAgent:
    """
    Autonomous intelligence officer that analyzes the A2A marketplace,
    audits the daily catalog proposals, and decides what products and SEO
    initiatives the swarm must prioritize.
    """

    CONCEPT_TO_TOOL: Dict[str, str] = {
        "PREDICTION_MARKET_ARBITRAGE": "prediction_market_arbitrage_radar",
        "TOKEN_CONTEXT_COMPRESSOR": "token_context_compressor",
        "CROSS_EXCHANGE_ARBITRAGE": "cross_exchange_arbitrage_scanner",
        "DEV_API_CHEATSHEET_VAULT": "dev_api_cheatsheet_vault",
        "A2A_QUANT_RADAR": "quant_microstructure_radar",
        "MARKET_MICROSTRUCTURE": "quant_microstructure_radar",
        "QUANT_MICROSTRUCTURE_RADAR": "quant_microstructure_radar",
        "AST_STRUCTURAL_SLICER": "ast_structural_slicer",
        "AST_SECURITY_LINTER": "deep_ast_vulnerability_auditor",
        "DEEP_AST_VULNERABILITY_AUDITOR": "deep_ast_vulnerability_auditor",
        "PROMPT_INJECTION_FIREWALL": "prompt_injection_firewall",
        "SMART_CONTRACT_HONEYPOT_RADAR": "smart_contract_honeypot_radar",
        "SECRET_LEAK_SCANNER": "secret_leak_scanner",
        "ORDERBOOK_SLIPPAGE_SIMULATOR": "orderbook_slippage_simulator",
        "SMART_MONEY_WHALE_RADAR": "smart_money_whale_flow_radar",
        "DAILY_TECH_AI_TRENDS": "daily_tech_ai_trends_radar",
    }

    def __init__(self):
        # Baseline agent market demand index
        self._trend_signals = [
            AgentDemandSignal(
                category="PREDICTION_MARKETS",
                target_tool="prediction_market_arbitrage_radar",
                search_volume_score=9.9,
                willingness_to_pay_usdc=0.03,
                competitive_density="LOW",
                key_intent_queries=[
                    "polymarket binary probability api",
                    "crypto prediction market arbitrage edge",
                    "black scholes implied probability vs polymarket",
                    "election and event trading agent tools"
                ],
                growth_driver="Explosion in prediction market trading bots needing low-latency mispricing calculations."
            ),
            AgentDemandSignal(
                category="CONTEXT_OPTIMIZATION",
                target_tool="token_context_compressor",
                search_volume_score=9.8,
                willingness_to_pay_usdc=0.01,
                competitive_density="LOW",
                key_intent_queries=[
                    "compress llm context prompt 90 percent",
                    "reduce tokens agent cost x402",
                    "cheap semantic context summarizer mcp",
                    "slash openai anthropic prompt bloat"
                ],
                growth_driver="Inference costs dominate agent operating budgets; prompt compression has immediate positive ROI."
            ),
            AgentDemandSignal(
                category="MARKET_MICROSTRUCTURE",
                target_tool="quant_microstructure_radar",
                search_volume_score=9.4,
                willingness_to_pay_usdc=0.02,
                competitive_density="MEDIUM",
                key_intent_queries=[
                    "crypto order book imbalance obi api",
                    "crypto liquidation cascade risk feed",
                    "real time orderbook depth mcp",
                    "sub-cent crypto microstructure"
                ],
                growth_driver="DeFi & algorithmic trading agents requiring sub-second order book features without raw websocket overhead."
            ),
            AgentDemandSignal(
                category="ARBITRAGE_FUNDING",
                target_tool="cross_exchange_arbitrage_scanner",
                search_volume_score=9.5,
                willingness_to_pay_usdc=0.03,
                competitive_density="LOW",
                key_intent_queries=[
                    "delta neutral funding rate apr scanner",
                    "spot perpetual futures basis spread",
                    "crypto funding arbitrage bot tool"
                ],
                growth_driver="Institutional and retail agents hunting risk-free yield across perp exchanges."
            ),
            AgentDemandSignal(
                category="CODE_INTELLIGENCE",
                target_tool="ast_structural_slicer",
                search_volume_score=9.1,
                willingness_to_pay_usdc=0.02,
                competitive_density="LOW",
                key_intent_queries=[
                    "python ast surgical function slicer",
                    "extract function without full file llm",
                    "ast code dependency extractor mcp"
                ],
                growth_driver="Coding agents like Cursor, Windsurf, and Claude needing precise code snippets without wasting context."
            ),
            AgentDemandSignal(
                category="DEV_SCHEMAS",
                target_tool="dev_api_cheatsheet_vault",
                search_volume_score=9.3,
                willingness_to_pay_usdc=0.01,
                competitive_density="LOW",
                key_intent_queries=[
                    "clean openai anthropic api schema json",
                    "zero fluff developer api snippets agent",
                    "fastmcp duckdb api cheat sheet"
                ],
                growth_driver="Agents hallucinate API syntax; compressed reference schemas eliminate documentation scraping."
            ),
            AgentDemandSignal(
                category="CYBER_PROMPT_FIREWALL",
                target_tool="prompt_injection_firewall",
                search_volume_score=9.9,
                willingness_to_pay_usdc=0.01,
                competitive_density="LOW",
                key_intent_queries=[
                    "prompt injection firewall api",
                    "prevent system prompt leak agent",
                    "ai agent jailbreak defense mcp",
                    "dan mode injection filter"
                ],
                growth_driver="Explosion in public-facing autonomous agents requiring pre-execution injection defenses."
            ),
            AgentDemandSignal(
                category="CYBER_SMART_CONTRACT",
                target_tool="smart_contract_honeypot_radar",
                search_volume_score=9.8,
                willingness_to_pay_usdc=0.03,
                competitive_density="LOW",
                key_intent_queries=[
                    "solidity honeypot detector api",
                    "evm reentrancy tax trap scanner",
                    "base memecoin honeypot audit bot",
                    "check token sell tax mcp"
                ],
                growth_driver="Web3 trading bots risking immediate capital loss on fraudulent token contracts."
            ),
            AgentDemandSignal(
                category="CYBER_SECRET_SCANNER",
                target_tool="secret_leak_scanner",
                search_volume_score=9.6,
                willingness_to_pay_usdc=0.01,
                competitive_density="LOW",
                key_intent_queries=[
                    "high entropy secret scanner api",
                    "detect openai private key leak",
                    "prevent api key leak in git prompt",
                    "secret leak scanner mcp"
                ],
                growth_driver="Developer and coding agents generating pull requests needing pre-flight secret audits."
            ),
            AgentDemandSignal(
                category="CODE_SECURITY",
                target_tool="deep_ast_vulnerability_auditor",
                search_volume_score=9.2,
                willingness_to_pay_usdc=0.03,
                competitive_density="LOW",
                key_intent_queries=[
                    "python ast security vulnerability scanner api",
                    "detect eval exec shell injection mcp",
                    "static ast security linter for ai agents"
                ],
                growth_driver="Autonomous coding agents need deterministic pre-execution AST linting before merging generated code."
            )
        ]

    def scan_agent_economy_trends(self) -> List[Dict[str, Any]]:
        """
        Synthesizes current search volume, buyer sentiment, and competitive saturation.
        """
        return [s.model_dump() for s in self._trend_signals]

    def analyze_competitive_moat(self) -> Dict[str, Any]:
        """
        Benchmarks SOUQ pricing against traditional human-centric cloud APIs and raw LLM token consumption.
        """
        return {
            "comparison_metrics": [
                {
                    "service": "Traditional Crypto API Subscriptions (CoinAPI / Kaiko)",
                    "pricing_model": "$150.00 - $1,500.00 / month flat subscription",
                    "friction": "High KYC, credit card requirement, zero x402 support",
                    "souq_advantage": "$0.02 per call on Base USDC, zero subscription lock-in"
                },
                {
                    "service": "Raw LLM Scraping & Document Parsing",
                    "pricing_model": "$0.10 - $0.35 per search query in tokens",
                    "friction": "Consumes 20k-50k context tokens and takes 8-15 seconds",
                    "souq_advantage": "$0.01 fixed USDC, pre-computed in < 500ms, saves 80-95% tokens"
                },
                {
                    "service": "Polymarket On-Chain Polling via Web3 RPC",
                    "pricing_model": "Polygon RPC costs + heavy local mathematical modeling",
                    "friction": "Complex Black-Scholes lognormal calibration required locally",
                    "souq_advantage": "Instant statistical arbitrage edge in basis points for $0.03 USDC"
                }
            ],
            "freemium_conversion_multiplier": "3.8x higher discovery rate with 1 free daily evaluation call",
            "net_roi_range_pct": "483% - 1900%"
        }

    @staticmethod
    def _normalize_slug(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")

    def _match_signal(
        self,
        concept_id: str,
        demand_map: Dict[str, AgentDemandSignal],
    ) -> Optional[AgentDemandSignal]:
        """Resolves a catalog concept_id to an AgentDemandSignal without single-word false positives."""
        concept_norm = self._normalize_slug(concept_id)
        if not concept_norm:
            return None

        mapped_tool = self.CONCEPT_TO_TOOL.get(concept_norm.upper())
        if mapped_tool and mapped_tool in demand_map:
            return demand_map[mapped_tool]

        if concept_norm in demand_map:
            return demand_map[concept_norm]

        for signal in self._trend_signals:
            if concept_norm == self._normalize_slug(signal.category):
                return signal

        # Full-slug boundary matching (requires multi-token concept to avoid generic single-word hits)
        concept_tokens = [tok for tok in concept_norm.split("_") if tok]
        for tool_name, signal in demand_map.items():
            if re.search(rf"(?:^|_){re.escape(tool_name)}(?:$|_)", concept_norm):
                return signal
            if len(concept_tokens) >= 2 and len(concept_norm) >= 12:
                if re.search(rf"(?:^|_){re.escape(concept_norm)}(?:$|_)", tool_name):
                    return signal
        return None

    @staticmethod
    def _load_live_stats(
        db_path: str,
        telemetry_summary: Optional[Dict[str, Any]],
        negotiation_stats: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        loaded_telemetry = telemetry_summary
        loaded_negotiations = negotiation_stats
        if loaded_telemetry is None:
            try:
                from agents.analytics.traffic_telemetry import TrafficTelemetryEngine

                loaded_telemetry = TrafficTelemetryEngine(db_path=db_path).get_summary()
            except Exception:
                loaded_telemetry = {}
        if loaded_negotiations is None:
            try:
                from agents.analytics.negotiation_tracker import NegotiationTracker

                loaded_negotiations = NegotiationTracker(db_path=db_path).get_market_intelligence_summary()
            except Exception:
                loaded_negotiations = {}
        return loaded_telemetry or {}, loaded_negotiations or {}

    @staticmethod
    def _synthesize_regime_and_verdict(
        prioritized_tools: List[str],
        telemetry_summary: Dict[str, Any],
        negotiation_stats: Dict[str, Any],
    ) -> Tuple[str, str]:
        total_interactions = int(negotiation_stats.get("total_interactions", 0) or 0)
        successful_settlements = int(negotiation_stats.get("successful_settlements", 0) or 0)
        conversion_rate_pct = float(negotiation_stats.get("conversion_rate_pct", 0.0) or 0.0)
        rejections = negotiation_stats.get("rejection_analysis") or []

        total_requests = int(telemetry_summary.get("total_requests", 0) or 0)
        client_cats = telemetry_summary.get("client_categories") or {}
        agent_traffic = int(client_cats.get("AI_AGENT", 0) or 0) + int(client_cats.get("MCP_CLIENT", 0) or 0)

        if successful_settlements > 0 and conversion_rate_pct >= 50.0:
            market_regime = "HIGH_CONVERSION_AGENT_SETTLEMENT"
        elif successful_settlements > 0:
            market_regime = "GROWING_SETTLEMENT_WITH_PRICE_DISCOVERY"
        elif total_interactions > 0:
            market_regime = "HIGH_402_CHALLENGE_FRICTION"
        elif total_requests > 0:
            market_regime = "ACTIVE_DISCOVERY_TRAFFIC_SCALING"
        else:
            market_regime = "COLD_START_HIGH_ARBITRAGE_AND_TOKEN_SENSITIVITY"

        verdict_parts: List[str] = []
        if prioritized_tools:
            top_focus = ", ".join(prioritized_tools[:3])
            verdict_parts.append(f"Prioritize {top_focus} based on catalog demand and live telemetry.")
        else:
            verdict_parts.append("No fulfillment-ready tools currently prioritized; verify catalog and SKU readiness.")

        if total_interactions > 0:
            neg_clause = (
                f"Observed {total_interactions} A2A negotiations "
                f"({successful_settlements} settled, {conversion_rate_pct:.1f}% conversion)."
            )
            if rejections:
                top_rej = max(rejections, key=lambda r: int(r.get("count", 0) or 0))
                neg_clause += (
                    f" Primary friction: {top_rej.get('rejection_reason')} "
                    f"({int(top_rej.get('count', 0) or 0)} events)."
                )
            verdict_parts.append(neg_clause)
        else:
            verdict_parts.append(
                "No live A2A negotiations recorded yet; leverage 1-call daily freemium onboarding "
                "to convert crawlers into x402 Base USDC or prepaid X-API-Key settlements."
            )

        if total_requests > 0:
            verdict_parts.append(
                f"Edge traffic telemetry: {total_requests} requests ({agent_traffic} AI/MCP clients)."
            )

        return market_regime, " ".join(verdict_parts)

    @staticmethod
    def query_funnel_telemetry(db_path: str) -> Dict[str, Any]:
        """
        Queries real Postgres/DuckDB tables for:
        1. 402 -> SETTLED conversion & drop-off rates per tool (`a2a_negotiations`)
        2. UNKNOWN_TOOL unmet buyer demand (`http_traffic_telemetry`)
        """
        dropoffs: Dict[str, Dict[str, Any]] = {}
        unknown_tools: List[Dict[str, Any]] = []
        try:
            from agents.treasury.db_backend import resolve_db_target, db_transaction

            db_target, _ = resolve_db_target(db_path)
            with db_transaction(db_target, read_only=True) as con:
                try:
                    rows = con.execute("""
                        SELECT
                            tool_requested,
                            SUM(CASE WHEN outcome = 'CHALLENGED_402' THEN 1 ELSE 0 END) AS challenged_402,
                            SUM(CASE WHEN outcome = 'SETTLED' THEN 1 ELSE 0 END) AS settled_count,
                            COUNT(*) AS total_events
                        FROM a2a_negotiations
                        GROUP BY tool_requested
                    """).fetchall()
                    for tool_name, ch_402, settled, total in rows:
                        ch_i = int(ch_402 or 0)
                        set_i = int(settled or 0)
                        dropoff_pct = round(((ch_i - set_i) / ch_i) * 100.0, 2) if ch_i > 0 else 0.0
                        dropoffs[str(tool_name)] = {
                            "tool": str(tool_name),
                            "challenged_402_count": ch_i,
                            "settled_count": set_i,
                            "total_events": int(total or 0),
                            "dropoff_rate_pct": max(0.0, dropoff_pct),
                        }
                except Exception:
                    pass

                try:
                    unk_rows = con.execute("""
                        SELECT tool_name, COUNT(*) AS hits
                        FROM http_traffic_telemetry
                        WHERE billing_status = 'UNKNOWN_TOOL' AND tool_name IS NOT NULL
                        GROUP BY tool_name
                        ORDER BY hits DESC
                        LIMIT 20
                    """).fetchall()
                    unknown_tools = [
                        {"requested_tool": str(r[0]), "hits": int(r[1] or 0)}
                        for r in unk_rows
                    ]
                except Exception:
                    pass
        except Exception:
            pass

        return {
            "funnel_dropoffs_402_to_settled": dropoffs,
            "unknown_tool_demand": unknown_tools,
        }

    def review_catalog_and_decide(
        self,
        proposed_catalog: List[Dict[str, Any]],
        telemetry_summary: Optional[Dict[str, Any]] = None,
        negotiation_stats: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Audits proposed catalog items from the Conductor, scores each against
        baseline demand plus live telemetry/negotiation conversion stats & real DB 402->SETTLED drop-offs.
        """
        funnel_metrics = self.query_funnel_telemetry(db_path) if db_path else {
            "funnel_dropoffs_402_to_settled": {},
            "unknown_tool_demand": [],
        }
        if db_path and (telemetry_summary is None or negotiation_stats is None):
            live_telemetry, live_negotiations = self._load_live_stats(
                db_path=db_path,
                telemetry_summary=telemetry_summary,
                negotiation_stats=negotiation_stats,
            )
        else:
            live_telemetry = telemetry_summary if isinstance(telemetry_summary, dict) else {}
            live_negotiations = negotiation_stats if isinstance(negotiation_stats, dict) else {}

        neg_by_tool: Dict[str, Dict[str, Any]] = {
            str(entry.get("tool_requested")): entry
            for entry in (live_negotiations.get("tool_telemetry") or [])
            if isinstance(entry, dict) and entry.get("tool_requested")
        }
        hits_by_tool: Dict[str, int] = {
            str(entry.get("tool")): int(entry.get("invocations", 0) or 0)
            for entry in (live_telemetry.get("top_tools") or [])
            if isinstance(entry, dict) and entry.get("tool")
        }

        reviewed_items: List[Dict[str, Any]] = []
        prioritized_candidates: List[Tuple[str, float, int]] = []
        pricing_directives: Dict[str, float] = {}
        all_aeo_keywords: List[str] = []

        demand_map = {s.target_tool: s for s in self._trend_signals}

        for idx, item in enumerate(proposed_catalog):
            concept_id = str(item.get("concept_id", "") or "")
            concept_norm = self._normalize_slug(concept_id)
            matching_signal = self._match_signal(concept_id, demand_map)
            resolved_tool = (
                matching_signal.target_tool
                if matching_signal
                else self.CONCEPT_TO_TOOL.get(concept_norm.upper())
            )

            neg = neg_by_tool.get(resolved_tool, {}) if resolved_tool else {}
            settled_calls = int(neg.get("successful_calls", 0) or 0)
            settled_volume = float(neg.get("total_volume_usd", 0.0) or 0.0)
            live_invocations = int(hits_by_tool.get(resolved_tool, 0) or 0) if resolved_tool else 0
            live_boost = min(2.0, settled_calls * 0.35 + settled_volume * 5.0 + live_invocations * 0.05)
            is_ready = item.get("fulfillment_ready", True) is not False

            if matching_signal:
                base_score = matching_signal.search_volume_score
                demand_score = round(min(10.0, base_score + live_boost * 0.1), 2)
                recommended_price = matching_signal.willingness_to_pay_usdc
                if not is_ready:
                    decision = "DEFERRED_UNCONFIGURED_SKU"
                elif demand_score >= 9.5 or settled_calls > 0:
                    decision = "APPROVED_HIGH_PRIORITY"
                else:
                    decision = "APPROVED_STANDARD"

                if is_ready:
                    prioritized_candidates.append((matching_signal.target_tool, base_score + live_boost, idx))
                    pricing_directives[matching_signal.target_tool] = recommended_price
                    all_aeo_keywords.extend(matching_signal.key_intent_queries)
            else:
                demand_score = round(min(10.0, 7.5 + live_boost * 0.1), 2)
                recommended_price = item.get("suggested_price", 0.02)
                decision = "DEFERRED_UNCONFIGURED_SKU" if not is_ready else "APPROVED_SECONDARY"
                if is_ready and resolved_tool and (settled_calls > 0 or live_invocations > 0):
                    prioritized_candidates.append((resolved_tool, 7.5 + live_boost, idx))
                    pricing_directives[resolved_tool] = recommended_price

            reviewed_items.append({
                "concept_id": item.get("concept_id"),
                "title": item.get("title"),
                "matched_tool": resolved_tool,
                "market_demand_score": demand_score,
                "review_decision": decision,
                "current_price_usd": item.get("suggested_price"),
                "recommended_price_usd": recommended_price,
                "settled_calls": settled_calls,
                "settled_volume_usd": round(settled_volume, 4),
                "live_invocations": live_invocations,
            })

        prioritized_candidates.sort(key=lambda entry: (-entry[1], entry[2]))
        unique_keywords = list(dict.fromkeys(all_aeo_keywords))
        unique_prioritized_tools = list(dict.fromkeys(tool for tool, _, _ in prioritized_candidates))

        market_regime, strategic_verdict = self._synthesize_regime_and_verdict(
            prioritized_tools=unique_prioritized_tools,
            telemetry_summary=live_telemetry,
            negotiation_stats=live_negotiations,
        )

        directive = MarketResearchDirective(
            directive_id=f"MRD-{int(time.time())}",
            generated_at=time.time(),
            market_regime=market_regime,
            prioritized_tools=unique_prioritized_tools,
            pricing_adjustments=pricing_directives,
            aeo_target_keywords=unique_keywords,
            strategic_verdict=strategic_verdict,
        )

        return {
            "status": "REVIEW_COMPLETE",
            "total_items_reviewed": len(reviewed_items),
            "reviewed_catalog": reviewed_items,
            "funnel_dropoffs_402_to_settled": funnel_metrics.get("funnel_dropoffs_402_to_settled", {}),
            "unknown_tool_demand": funnel_metrics.get("unknown_tool_demand", []),
            "market_directive": directive.model_dump()
        }
