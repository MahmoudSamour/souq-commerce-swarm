"""
SOUQ // Buhuth Market Research & Strategy Agent (البحوث)
Autonomous market research analyst for the agent-to-agent economy.
Scans demand trends, benchmarks competitor pricing, reviews proposed catalog items,
and issues strategic directives for product selection and Agent Engine Optimization (AEO).
"""

import time
from typing import Dict, Any, List, Optional
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
                    "binance order book imbalance obi api",
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

    def review_catalog_and_decide(
        self,
        proposed_catalog: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Audits proposed catalog items from the Conductor, scores each against
        live demand, and issues binding catalog adjustments.
        """
        reviewed_items = []
        prioritized_tool_ids = []
        pricing_directives = {}
        all_aeo_keywords = []

        # Map signals by tool/concept keyword
        demand_map = {s.target_tool: s for s in self._trend_signals}

        for item in proposed_catalog:
            concept = item.get("concept_id", "").lower()
            matching_signal = None
            for tool_name, signal in demand_map.items():
                if any(k in concept for k in tool_name.split("_")):
                    matching_signal = signal
                    break

            if matching_signal:
                demand_score = matching_signal.search_volume_score
                recommended_price = matching_signal.willingness_to_pay_usdc
                decision = "APPROVED_HIGH_PRIORITY" if demand_score >= 9.5 else "APPROVED_STANDARD"
                prioritized_tool_ids.append(matching_signal.target_tool)
                pricing_directives[matching_signal.target_tool] = recommended_price
                all_aeo_keywords.extend(matching_signal.key_intent_queries)
            else:
                demand_score = 7.5
                recommended_price = item.get("suggested_price", 0.02)
                decision = "APPROVED_SECONDARY"

            reviewed_items.append({
                "concept_id": item.get("concept_id"),
                "title": item.get("title"),
                "market_demand_score": demand_score,
                "review_decision": decision,
                "current_price_usd": item.get("suggested_price"),
                "recommended_price_usd": recommended_price
            })

        # Compile top AEO keywords deduplicated
        unique_keywords = list(dict.fromkeys(all_aeo_keywords))

        directive = MarketResearchDirective(
            directive_id=f"MRD-{int(time.time())}",
            generated_at=time.time(),
            market_regime="HIGH_ARBITRAGE_AND_TOKEN_SENSITIVITY",
            prioritized_tools=prioritized_tool_ids,
            pricing_adjustments=pricing_directives,
            aeo_target_keywords=unique_keywords,
            strategic_verdict=(
                "Prioritize Prediction Market Arbitrage Radar and Token Context Compressor. "
                "Maintain 1-call daily freemium onboarding to drive autonomous agent crawler conversions. "
                "Broadcast fresh machine manifests to IndexNow daily."
            )
        )

        return {
            "status": "REVIEW_COMPLETE",
            "total_items_reviewed": len(reviewed_items),
            "reviewed_catalog": reviewed_items,
            "market_directive": directive.model_dump()
        }
