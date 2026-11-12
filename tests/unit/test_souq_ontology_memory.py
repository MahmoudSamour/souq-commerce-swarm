import pytest
import os
from agents.analytics.souq_ontology_memory import SouqOntologyMemoryEngine

def test_souq_ontology_memory_lifecycle(tmp_path):
    test_db = str(tmp_path / "test_memory.duckdb")
    engine = SouqOntologyMemoryEngine(db_path=test_db)

    # 1. Record milestone
    m_id = engine.record_milestone(
        category="ARCHITECTURE",
        author_agent="Ra'is",
        title="Test Architectural Evolution",
        summary="Test summary of evolutionary step",
        technical_delta="Added new test tables",
        artifacts=["test_file.py"],
        tags=["test", "architecture"]
    )
    assert m_id.startswith("MLS-")

    # 2. Query timeline
    timeline = engine.get_memory_timeline()
    assert len(timeline) == 1
    assert timeline[0]["milestone_id"] == m_id
    assert timeline[0]["author_agent"] == "Ra'is"
    assert timeline[0]["category"] == "ARCHITECTURE"

    # 3. Upsert entity
    ent_id = engine.upsert_entity(
        name="Test Agent",
        entity_type="AGENT",
        canonical_identifier="souq.agent.test",
        description="Test agent description",
        metadata={"role": "tester"}
    )
    assert ent_id.startswith("ENT-AGE-")

    # 4. Register plan
    plan_id = engine.register_future_plan(
        target_phase="IMMEDIATE",
        priority="HIGH",
        owner_agent="Amin",
        title="Test Plan",
        description="Test plan description"
    )
    assert plan_id.startswith("PLN-")

    plans = engine.get_future_plans()
    assert len(plans) == 1
    assert plans[0]["plan_id"] == plan_id
    assert plans[0]["status"] == "PLANNED"
