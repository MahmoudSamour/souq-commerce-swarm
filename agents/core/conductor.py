"""
SOUQ // Supreme Executive Conductor (Ra'is)
Coordinates the autonomous commerce lifecycle: Discovery -> Compliance -> Synthesis -> Listing -> Settlement.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from agents.discovery.opportunity_ranker import OpportunityRanker, ProductOpportunity
from agents.discovery.market_researcher import MarketResearchAgent
from agents.compliance.amin_auditor import AminAuditor
from agents.production.mcp_tool_builder import PredictionMarketArbitrageRadar
from agents.production.dev_intelligence_vault import DailyTechTrendsRadar
from agents.production.cyber_threat_intelligence import CyberThreatIntelligenceRadar
from agents.distribution.munadi_herald import MunadiHerald
from agents.treasury.crypto_receipt_engine import CryptoReceiptEngine
from agents.treasury.x402_gateway import X402PaymentGateway
from agents.treasury.polar_adapter import POLAR_PRODUCTS, PolarAdapter
from agents.analytics.negotiation_tracker import NegotiationTracker
from agents.analytics.souq_ontology_memory import SouqOntologyMemoryEngine
from agents.analytics.traffic_telemetry import TrafficTelemetryEngine


class RaisConductor:
    """
    Supreme Conductor & Team Lead directing the autonomous sovereign agent squad:
    1. Sayf: Cyber Threat Intelligence Sentinel (الحارس السيبراني)
    2. Kashif: AI & Tech Trends Radar (المستكشف)
    3. Riyadi: Prediction Market & Microstructure Radar (الرياضي)
    4. Buhuth: Autonomous Market Research Analyst (البحوث)
    5. Amin: Ethical & Legal Compliance Auditor (الأمين)
    6. Munadi: Discovery, AEO & Global Search Herald (المنادي)
    """

    CONCEPT_POLAR_SKU: Dict[str, str] = {
        "5Y_CRYPTO_LAKE": "crypto_5y_microstructure_lake",
    }

    CONCEPT_SOURCE_MAP: Dict[str, str] = {
        "PREDICTION_MARKET_ARBITRAGE": "agents/production/mcp_tool_builder.py",
        "CROSS_EXCHANGE_ARBITRAGE": "agents/production/mcp_tool_builder.py",
        "ORDERBOOK_SLIPPAGE_SIMULATOR": "agents/production/mcp_tool_builder.py",
        "SMART_MONEY_WHALE_RADAR": "agents/production/mcp_tool_builder.py",
        "A2A_QUANT_RADAR": "agents/production/mcp_tool_builder.py",
        "SMART_CONTRACT_HONEYPOT_RADAR": "agents/production/cyber_defense_vault.py",
        "DEEP_AST_VULNERABILITY_AUDITOR": "agents/production/cyber_defense_vault.py",
        "TOKEN_CONTEXT_COMPRESSOR": "agents/production/token_compressor.py",
        "DEV_API_CHEATSHEET_VAULT": "agents/production/dev_intelligence_vault.py",
        "DAILY_TECH_AI_TRENDS": "agents/production/dev_intelligence_vault.py",
        "5Y_CRYPTO_LAKE": "agents/production/mcp_tool_builder.py",
    }

    def __init__(self, db_path: str = "data/souq_treasury_lake.duckdb"):
        self.db_path = db_path
        self.ranker = OpportunityRanker()
        self.researcher = MarketResearchAgent()
        self.auditor = AminAuditor()
        self.threat_radar = CyberThreatIntelligenceRadar()
        self.trends_radar = DailyTechTrendsRadar()
        self.prediction_radar = PredictionMarketArbitrageRadar()
        self.herald = MunadiHerald()
        self.receipt_engine = CryptoReceiptEngine(db_path=db_path)
        self.negotiation_tracker = NegotiationTracker(db_path=db_path)
        self.telemetry_engine = TrafficTelemetryEngine(db_path=db_path)
        self.ontology_memory = SouqOntologyMemoryEngine(db_path=db_path)
        self.polar_adapter = PolarAdapter(db_path=db_path)
        self.payment_gateway = X402PaymentGateway(
            receipt_engine=self.receipt_engine,
            negotiation_tracker=self.negotiation_tracker
        )

        # Sovereign Agent Squad Registry
        self.team_squad = {
            "sayf_cyber_sentinel": {
                "name": "Sayf (سيف)",
                "role": "Cyber Threat Intelligence Sentinel",
                "focus": "Dynamic threat signatures, prompt injection firewall rules, smart contract honeypots, secret leaks"
            },
            "kashif_tech_radar": {
                "name": "Kashif (المستكشف)",
                "role": "Daily AI & Tech Trends Radar",
                "focus": "GitHub AI trending repositories, developer schema demands, emerging tool ecosystems"
            },
            "riyadi_prediction_radar": {
                "name": "Riyadi (الرياضي)",
                "role": "Prediction Market & Quant Microstructure Engine",
                "focus": "Black-Scholes probability arbitrage, crypto order-book spreads, whale flow telemetry"
            },
            "buhuth_market_researcher": {
                "name": "Buhuth (البحوث)",
                "role": "Autonomous Market Research Analyst",
                "focus": "Willingness-to-pay elasticity, competitive moat analysis, dynamic AEO directive synthesis"
            },
            "amin_compliance_auditor": {
                "name": "Amin (الأمين)",
                "role": "Zero-Risk Compliance & Ethics Auditor",
                "focus": "Terms of service validation, zero-PII guarantee, copyright safety, clearance token signing"
            },
            "munadi_distribution_herald": {
                "name": "Munadi (المنادي)",
                "role": "Discovery, AEO & Global Search Herald",
                "focus": "Edge endpoint verification, machine catalog feeds, IndexNow instant search engine indexing"
            }
        }

    def _evaluate_fulfillment_readiness(
        self,
        concept_id: str,
        polar_catalog: Dict[str, Any],
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Checks whether a catalog concept is deliverable via live x402 APIs or configured Polar SKU."""
        sku_id = self.CONCEPT_POLAR_SKU.get(concept_id)
        if not sku_id:
            return True, None, None

        sku_entry = polar_catalog.get(sku_id, {})
        if sku_entry.get("ready"):
            return True, sku_id, None

        spec = POLAR_PRODUCTS.get(sku_id, {})
        asset_env = spec.get("asset_url_env")
        if asset_env and not os.getenv(asset_env, "").strip():
            return False, sku_id, f"{asset_env} not configured"
        checkout_env = spec.get("checkout_url_env", "POLAR_CHECKOUT_URL")
        product_env = spec.get("product_id_env", "POLAR_PRODUCT_ID")
        return False, sku_id, f"{checkout_env} / {product_env} not configured"

    def run_daily_cycle(self, broadcast_search: bool = False) -> Dict[str, Any]:
        """
        Executes an end-to-end autonomous discovery, compliance, and listing cycle
        coordinated by the Team Lead directing all specialist agents.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        core_degraded: List[str] = []
        warnings: List[str] = []

        # Squad Agent 1: Sayf (Cyber Threat Intelligence Sentinel)
        try:
            cyber_sigs = self.threat_radar.fetch_latest_threat_signatures()
            if not isinstance(cyber_sigs, dict) or int(cyber_sigs.get("total_rules", 0) or 0) <= 0:
                core_degraded.append("sayf_cyber_sentinel")
        except Exception:
            cyber_sigs = {"status": "error", "total_rules": 0}
            core_degraded.append("sayf_cyber_sentinel")

        # Squad Agent 2: Kashif (AI & Tech Trends Intelligence Radar)
        try:
            tech_trends = self.trends_radar.refresh_cache_and_get(force_refresh=True)
            if tech_trends.get("status") == "upstream_unavailable":
                warnings.append("kashif_tech_trends_upstream_unavailable")
        except Exception:
            tech_trends = {"status": "error", "trending_github_ai_repos": []}
            warnings.append("kashif_tech_trends_error")

        # Squad Agent 3: Riyadi (Prediction & Microstructure Radar)
        try:
            pred_arb = self.prediction_radar.scan_prediction_arbitrage("BTC")
            if pred_arb.get("status") in ("error", "upstream_unavailable"):
                warnings.append("riyadi_prediction_upstream_unavailable")
        except Exception:
            pred_arb = {"status": "error", "opportunities_analyzed": 0, "benchmark_spot_price": 0}
            warnings.append("riyadi_prediction_error")

        # 1. Discovery & Opportunity Ranking (Kashif & OpportunityRanker)
        test_opportunities = [
            ProductOpportunity(
                concept_id="PREDICTION_MARKET_ARBITRAGE",
                title="Black-Scholes vs. Polymarket Prediction Probability Arbitrage Radar",
                target_buyer="A2A_AGENT",
                demand_intensity=9.9,
                willingness_to_pay=9.8,
                supply_saturation=1.2,
                synthesis_complexity=1.8,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.03
            ),
            ProductOpportunity(
                concept_id="TOKEN_CONTEXT_COMPRESSOR",
                title="High-Entropy Semantic Token Context Compressor (90% Savings)",
                target_buyer="A2A_AGENT",
                demand_intensity=9.8,
                willingness_to_pay=9.5,
                supply_saturation=1.8,
                synthesis_complexity=1.5,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.01
            ),
            ProductOpportunity(
                concept_id="CROSS_EXCHANGE_ARBITRAGE",
                title="Spot vs. Perp Basis Spread & Funding Rate APR Arbitrage Scanner",
                target_buyer="A2A_AGENT",
                demand_intensity=9.7,
                willingness_to_pay=9.2,
                supply_saturation=1.9,
                synthesis_complexity=2.0,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.03
            ),
            ProductOpportunity(
                concept_id="ORDERBOOK_SLIPPAGE_SIMULATOR",
                title="Real-Time Order-Book Depth Slippage & Price Impact Simulator",
                target_buyer="A2A_AGENT",
                demand_intensity=9.6,
                willingness_to_pay=9.0,
                supply_saturation=1.7,
                synthesis_complexity=1.8,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.02
            ),
            ProductOpportunity(
                concept_id="SMART_MONEY_WHALE_RADAR",
                title="Smart Money & Whale Block Flow Accumulation Radar",
                target_buyer="A2A_AGENT",
                demand_intensity=9.9,
                willingness_to_pay=9.6,
                supply_saturation=1.5,
                synthesis_complexity=2.2,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.03
            ),
            ProductOpportunity(
                concept_id="DEV_API_CHEATSHEET_VAULT",
                title="Pre-Cleaned Developer API Reference & Schema Vault",
                target_buyer="A2A_AGENT",
                demand_intensity=9.8,
                willingness_to_pay=9.4,
                supply_saturation=1.2,
                synthesis_complexity=1.6,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.01
            ),
            ProductOpportunity(
                concept_id="DAILY_TECH_AI_TRENDS",
                title="Daily AI & Developer Technology Intelligence Snapshot",
                target_buyer="A2A_AGENT",
                demand_intensity=9.7,
                willingness_to_pay=9.3,
                supply_saturation=1.4,
                synthesis_complexity=1.8,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.01
            ),
            ProductOpportunity(
                concept_id="A2A_QUANT_RADAR",
                title="Live Crypto Order-Book Imbalance & Liquidation Radar",
                target_buyer="A2A_AGENT",
                demand_intensity=9.5,
                willingness_to_pay=8.5,
                supply_saturation=2.0,
                synthesis_complexity=2.5,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.02
            ),
            ProductOpportunity(
                concept_id="SMART_CONTRACT_HONEYPOT_RADAR",
                title="Live Base EVM Smart Contract Honeypot & Reentrancy Radar",
                target_buyer="A2A_AGENT",
                demand_intensity=9.8,
                willingness_to_pay=9.4,
                supply_saturation=1.4,
                synthesis_complexity=2.0,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.03
            ),
            ProductOpportunity(
                concept_id="DEEP_AST_VULNERABILITY_AUDITOR",
                title="Deep Python AST Security Vulnerability Auditor (Lead Magnet)",
                target_buyer="A2A_AGENT",
                demand_intensity=9.0,
                willingness_to_pay=8.0,
                supply_saturation=2.2,
                synthesis_complexity=2.0,
                legal_risk_score=1.0,
                suggested_unit_price_usd=0.03
            ),
            ProductOpportunity(
                concept_id="5Y_CRYPTO_LAKE",
                title="5-Year High-Frequency Market Microstructure DuckDB Lake",
                target_buyer="RESEARCHER",
                demand_intensity=8.5,
                willingness_to_pay=9.0,
                supply_saturation=2.5,
                synthesis_complexity=3.0,
                legal_risk_score=1.0,
                suggested_unit_price_usd=49.00
            )
        ]

        funnel_telemetry = self.researcher.query_funnel_telemetry(self.db_path)
        ranked_opportunities = self.ranker.rank_opportunities(
            test_opportunities,
            funnel_telemetry=funnel_telemetry,
        )

        # 2. Compliance Auditing (Amin Real Static AST/URL Policy Audit) & Polar SKU Fulfillment Readiness
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        polar_catalog = self.polar_adapter.list_catalog()
        approved_catalog: List[Dict[str, Any]] = []
        pending_catalog: List[Dict[str, Any]] = []
        for opp in ranked_opportunities:
            rel_src = self.CONCEPT_SOURCE_MAP.get(opp["concept_id"])
            abs_src = os.path.join(repo_root, rel_src) if rel_src else ""
            cleared, audit_result = self.auditor.audit_tool_source(
                abs_src,
                concept_id=opp["concept_id"],
            )
            if not cleared:
                continue

            fulfillment_ready, polar_sku, unready_reason = self._evaluate_fulfillment_readiness(
                opp["concept_id"], polar_catalog
            )
            opp["compliance_token"] = audit_result["clearance_token"]
            opp["compliance_source_sha256"] = audit_result.get("source_sha256")
            opp["fulfillment_ready"] = fulfillment_ready
            if polar_sku:
                opp["polar_sku"] = polar_sku

            if fulfillment_ready:
                approved_catalog.append(opp)
            else:
                opp["reason"] = unready_reason or "Fulfillment configuration pending"
                pending_catalog.append(opp)

        if not approved_catalog:
            core_degraded.append("amin_compliance_empty_catalog")

        # 3. Telemetry & Treasury Lake Summary (Sayrafi + Telemetry + Negotiation)
        try:
            market_intel = self.negotiation_tracker.get_market_intelligence_summary()
            if "error" in market_intel:
                core_degraded.append("negotiation_tracker_db")
        except Exception:
            market_intel = {"error": "negotiation_tracker_unavailable", "total_interactions": 0}
            core_degraded.append("negotiation_tracker_db")

        try:
            traffic_summary = self.telemetry_engine.get_summary()
            if "error" in traffic_summary:
                core_degraded.append("traffic_telemetry_db")
        except Exception:
            traffic_summary = {"error": "traffic_telemetry_unavailable", "total_requests": 0}
            core_degraded.append("traffic_telemetry_db")

        # 4. Market Research Review & Decision (Buhuth)
        market_decision = self.researcher.review_catalog_and_decide(
            approved_catalog,
            telemetry_summary=traffic_summary,
            negotiation_stats=market_intel,
            db_path=self.db_path,
        )

        # 5. Sovereign Ontology & Milestone Memory Sync
        ontology_status: Dict[str, Any]
        try:
            conductor_entity_id = self.ontology_memory.upsert_entity(
                name="Ra'is Autonomous Conductor",
                entity_type="AGENT",
                canonical_identifier="souq.agent.rais_conductor",
                description="Executive swarm conductor coordinating discovery, compliance, research, and distribution.",
                metadata={
                    "active_catalog_count": len(approved_catalog),
                    "pending_catalog_count": len(pending_catalog),
                    "total_threat_rules": int(cyber_sigs.get("total_rules", 0) or 0),
                },
            )
            recent_milestones = self.ontology_memory.get_memory_timeline(limit=5)
            planned_roadmap = self.ontology_memory.get_future_plans(status="PLANNED")
            ontology_status = {
                "status": "active",
                "conductor_entity_id": conductor_entity_id,
                "recent_milestones_count": len(recent_milestones),
                "planned_roadmap_count": len(planned_roadmap),
            }
        except Exception:
            ontology_status = {"status": "error"}
            core_degraded.append("souq_ontology_memory")

        # Squad Agent 6: Munadi (Herald & AEO Distribution)
        try:
            herald_audit = self.herald.verify_public_discovery_endpoints()
        except Exception as exc:
            herald_audit = {"overall_status": "DEGRADED", "error": str(exc), "endpoints": []}
        if herald_audit.get("overall_status") != "ONLINE_AND_DISCOVERABLE":
            warnings.append("munadi_public_endpoints_degraded")

        herald_index = self.herald.broadcast_to_indexnow() if broadcast_search else {"status": "SKIPPED_LOCAL_TEST"}
        if broadcast_search and herald_index.get("status") == "error":
            warnings.append("munadi_indexnow_error")

        overall_status = "DEGRADED" if core_degraded else "OPERATIONAL_AND_REVENUE_READY"
        degraded_components = list(dict.fromkeys(core_degraded + warnings))
        polar_ready_count = sum(1 for info in polar_catalog.values() if info.get("ready"))

        sanitized_traffic = {
            "total_requests": int(traffic_summary.get("total_requests", 0) or 0),
            "unique_visitors": int(traffic_summary.get("unique_visitors", 0) or 0),
            "client_categories": traffic_summary.get("client_categories", {}),
            "billing_funnel": traffic_summary.get("billing_funnel", {}),
            "top_tools": traffic_summary.get("top_tools", []),
        }

        # Squad Agent 7: Marketplace Health & Auto-Pruning Sentinel (Ra'is)
        try:
            from agents.treasury.marketplace_registry import MarketplaceRegistry
            mkt_reg = MarketplaceRegistry(db_path=getattr(self, "db_path", "data/souq_treasury_lake.duckdb"))
            marketplace_health = mkt_reg.audit_active_listings(timeout_s=3.0)
            marketplace_kpis = mkt_reg.get_marketplace_kpis()
        except Exception as mkt_exc:
            marketplace_health = {"checked_listings": 0, "suspended_listings": 0, "error": str(mkt_exc)}
            marketplace_kpis = {}

        return {
            "cycle_timestamp": timestamp,
            "status": overall_status,
            "degraded_components": degraded_components,
            "warnings": warnings,
            "team_lead": {
                "name": "Ra'is (الرئيس)",
                "role": "Supreme Autonomous Update Team Lead",
                "total_specialist_agents": len(self.team_squad),
                "squad": self.team_squad
            },
            "cybersecurity_intelligence": {
                "sentinel": "Sayf",
                "status": "DEGRADED" if "sayf_cyber_sentinel" in core_degraded else "ACTIVE_AND_REGULARLY_UPDATED",
                "version": cyber_sigs.get("version", "2.0.0"),
                "total_threat_rules": cyber_sigs.get("total_rules", 0),
                "prompt_injection_rules": len(cyber_sigs.get("prompt_injection_rules", [])),
                "honeypot_rules": len(cyber_sigs.get("honeypot_rules", [])),
                "secret_leak_rules": len(cyber_sigs.get("secret_rules", []))
            },
            "tech_ai_trends": {
                "radar": "Kashif",
                "status": tech_trends.get("status", "success"),
                "digest_date": tech_trends.get("digest_date"),
                "data_source": tech_trends.get("data_source", "curated"),
                "total_trending_topics": len(tech_trends.get("trending_github_ai_repos", []))
            },
            "prediction_arbitrage": {
                "quant": "Riyadi",
                "status": pred_arb.get("status", "success"),
                "markets_analyzed": pred_arb.get("opportunities_analyzed", 0),
                "benchmark_spot": pred_arb.get("benchmark_spot_price", 0)
            },
            "active_catalog": approved_catalog,
            "pending_catalog": pending_catalog,
            "polar_catalog_readiness": {
                sku: bool(info.get("ready", False)) for sku, info in polar_catalog.items()
            },
            "market_research": market_decision,
            "market_intelligence": market_intel,
            "traffic_telemetry": sanitized_traffic,
            "ontology_memory": ontology_status,
            "herald_distribution": {
                "endpoints_health": herald_audit.get("overall_status"),
                "indexnow": herald_index
            },
            "marketplace_health": marketplace_health,
            "marketplace_kpis": marketplace_kpis,
            "payment_rails": {
                "rail_a_agent_crypto": "ACTIVE (HTTP 402 + Base USDC)",
                "rail_b_human_mor": (
                    f"ACTIVE (Polar.sh Merchant of Record, {polar_ready_count} SKUs ready)"
                    if polar_ready_count > 0
                    else "PENDING_SKU_CONFIGURATION (Polar.sh Merchant of Record)"
                ),
                "rail_c_prepaid_api_key": "ACTIVE (X-API-Key DuckDB Credit Ledger)"
            }
        }


# Autonomous Team Lead Aliases
AutonomousUpdateTeamLead = RaisConductor
UpdateTeamLead = RaisConductor

