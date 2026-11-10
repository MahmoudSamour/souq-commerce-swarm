"""
SOUQ // Opportunity Scoring & Elasticity Engine (Kashif Scout)
Evaluates digital product concepts using the mathematical Souq Opportunity Metric (SOM).
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ProductOpportunity(BaseModel):
    concept_id: str
    title: str
    target_buyer: str                       # 'A2A_AGENT', 'RESEARCHER', 'DEVELOPER'
    demand_intensity: float = Field(ge=1.0, le=10.0)
    willingness_to_pay: float = Field(ge=1.0, le=10.0)
    supply_saturation: float = Field(ge=1.0, le=10.0)
    synthesis_complexity: float = Field(ge=1.0, le=10.0)
    legal_risk_score: float = Field(ge=1.0, le=10.0)
    suggested_unit_price_usd: float

    def calculate_som_score(self) -> float:
        """
        SOM = (Demand * WTP) / (Saturation * Complexity * LegalRisk)
        """
        denominator = (self.supply_saturation * self.synthesis_complexity * self.legal_risk_score)
        if denominator == 0:
            return 0.0
        numerator = (self.demand_intensity * self.willingness_to_pay)
        return round(numerator / denominator, 3)

    def is_production_ready(self) -> bool:
        """
        Strict threshold: SOM >= 1.50 and Legal Risk <= 1.20
        """
        return self.calculate_som_score() >= 1.50 and self.legal_risk_score <= 1.20


class OpportunityRanker:
    """
    Ranks market demand signals and selects optimal product opportunities.
    """

    def rank_opportunities(self, opportunities: List[ProductOpportunity]) -> List[Dict[str, Any]]:
        scored = []
        for opp in opportunities:
            score = opp.calculate_som_score()
            scored.append({
                "concept_id": opp.concept_id,
                "title": opp.title,
                "target_buyer": opp.target_buyer,
                "som_score": score,
                "legal_risk": opp.legal_risk_score,
                "is_approved": opp.is_production_ready(),
                "suggested_price": opp.suggested_unit_price_usd
            })

        # Sort descending by SOM score
        scored.sort(key=lambda x: x["som_score"], reverse=True)
        return scored

