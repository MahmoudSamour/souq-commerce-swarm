"""
SOUQ // Sovereign Swarm Ontology & Memory Engine
Manages persistent institutional memory, architectural milestones, ontology entities,
and future planning exclusively within the SOUQ repository silo (`data/souq_treasury_lake.duckdb`).

Governed by Mas2 Bot Mandate:
- SOUQ agents track their own evolution, past steps, and future roadmaps.
- Strictly isolated to /home/mm/Souq/souq-commerce-swarm with zero cross-repo bleed.
"""

import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from agents.treasury.db_backend import (
    resolve_db_target,
    db_transaction,
    ensure_parent_dir,
)

logger = logging.getLogger("souq.ontology_memory")


class SouqOntologyMemoryEngine:
    """
    Sovereign Ontology & Milestone Memory Engine for SOUQ Swarm.
    Stores and queries:
    1. souq_milestones_and_memory: Past architectural and operational steps.
    2. souq_ontology_entities: Tools, contracts, agents, schemas, and endpoints.
    3. souq_future_plans: Structured roadmap, backlog, and planned enhancements.
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
                # 1. Past Milestones & Chronological Steps
                con.execute("""
                    CREATE TABLE IF NOT EXISTS souq_milestones_and_memory (
                        milestone_id VARCHAR PRIMARY KEY,
                        timestamp_utc TIMESTAMP NOT NULL,
                        cycle_date VARCHAR NOT NULL,
                        category VARCHAR NOT NULL,         -- 'ARCHITECTURE', 'SECURITY', 'TELEMETRY', 'DISTRIBUTION', 'COMPLIANCE'
                        author_agent VARCHAR NOT NULL,     -- 'Ra\'is', 'Sayf', 'Amin', 'Munadi', 'Mas2_Bot'
                        title VARCHAR NOT NULL,
                        summary VARCHAR NOT NULL,
                        technical_delta VARCHAR NOT NULL,
                        artifacts_json VARCHAR,
                        tags_json VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 2. Sovereign Ontology Entities
                con.execute("""
                    CREATE TABLE IF NOT EXISTS souq_ontology_entities (
                        entity_id VARCHAR PRIMARY KEY,
                        name VARCHAR NOT NULL,
                        entity_type VARCHAR NOT NULL,      -- 'AGENT', 'TOOL', 'CONTRACT', 'PROTOCOL', 'SCHEMA', 'ENDPOINT'
                        canonical_identifier VARCHAR NOT NULL,
                        description VARCHAR NOT NULL,
                        metadata_json VARCHAR,
                        first_recorded_utc TIMESTAMP NOT NULL,
                        last_updated_utc TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 3. Future Plans & Roadmap
                con.execute("""
                    CREATE TABLE IF NOT EXISTS souq_future_plans (
                        plan_id VARCHAR PRIMARY KEY,
                        target_phase VARCHAR NOT NULL,     -- 'IMMEDIATE', 'NEAR_TERM', 'FUTURE_EXPANSION'
                        priority VARCHAR NOT NULL,         -- 'CRITICAL', 'HIGH', 'MEDIUM'
                        owner_agent VARCHAR NOT NULL,
                        title VARCHAR NOT NULL,
                        description VARCHAR NOT NULL,
                        dependencies_json VARCHAR,
                        status VARCHAR NOT NULL DEFAULT 'PLANNED', -- 'PLANNED', 'IN_PROGRESS', 'COMPLETED'
                        target_completion_date VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        except Exception as e:
            logger.error(f"Failed to initialize SOUQ ontology memory tables: {e}")

    @staticmethod
    def _entity_id(entity_type: str, canonical_identifier: str) -> str:
        digest = hashlib.sha256(
            f"{entity_type.strip().upper()}:{canonical_identifier.strip()}".encode("utf-8")
        ).hexdigest()[:32]
        return f"ENT-{entity_type[:3].upper()}-{digest}"

    def record_milestone(
        self,
        category: str,
        author_agent: str,
        title: str,
        summary: str,
        technical_delta: str,
        cycle_date: Optional[str] = None,
        artifacts: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Records a completed step or architectural milestone into SOUQ memory."""
        milestone_id = f"MLS-{uuid.uuid4().hex[:10].upper()}"
        now = datetime.now(timezone.utc)
        date_str = cycle_date or now.strftime("%Y-%m-%d")

        try:
            with db_transaction(self.db_target, read_only=False) as con:
                con.execute("""
                    INSERT INTO souq_milestones_and_memory (
                        milestone_id, timestamp_utc, cycle_date, category,
                        author_agent, title, summary, technical_delta,
                        artifacts_json, tags_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    milestone_id, now, date_str, category,
                    author_agent, title, summary, technical_delta,
                    json.dumps(artifacts or []), json.dumps(tags or [])
                ))
            logger.info(f"Recorded milestone {milestone_id}: {title}")
        except Exception as e:
            logger.error(f"Error recording milestone: {e}")

        return milestone_id

    def upsert_entity(
        self,
        name: str,
        entity_type: str,
        canonical_identifier: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Registers or updates a sovereign entity in SOUQ's ontology."""
        entity_id = self._entity_id(entity_type, canonical_identifier)
        now = datetime.now(timezone.utc)

        try:
            with db_transaction(self.db_target, read_only=False) as con:
                exists = con.execute(
                    "SELECT entity_id FROM souq_ontology_entities WHERE entity_id = ?",
                    (entity_id,),
                ).fetchone()
                if exists:
                    con.execute("""
                        UPDATE souq_ontology_entities
                        SET name = ?, description = ?, metadata_json = ?, last_updated_utc = ?
                        WHERE entity_id = ?
                    """, (name, description, json.dumps(metadata or {}), now, entity_id))
                else:
                    con.execute("""
                        INSERT INTO souq_ontology_entities (
                            entity_id, name, entity_type, canonical_identifier,
                            description, metadata_json, first_recorded_utc, last_updated_utc
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entity_id, name, entity_type, canonical_identifier,
                        description, json.dumps(metadata or {}), now, now
                    ))
            logger.info(f"Upserted ontology entity: {entity_id}")
        except Exception as e:
            logger.error(f"Error upserting entity: {e}")

        return entity_id

    def register_future_plan(
        self,
        target_phase: str,
        priority: str,
        owner_agent: str,
        title: str,
        description: str,
        dependencies: Optional[List[str]] = None,
        target_completion_date: Optional[str] = None
    ) -> str:
        """Registers a forward-looking plan into SOUQ's roadmap memory."""
        plan_id = f"PLN-{uuid.uuid4().hex[:8].upper()}"

        try:
            with db_transaction(self.db_target, read_only=False) as con:
                con.execute("""
                    INSERT INTO souq_future_plans (
                        plan_id, target_phase, priority, owner_agent,
                        title, description, dependencies_json, status,
                        target_completion_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PLANNED', ?)
                """, (
                    plan_id, target_phase, priority, owner_agent,
                    title, description, json.dumps(dependencies or []),
                    target_completion_date
                ))
            logger.info(f"Registered future plan {plan_id}: {title}")
        except Exception as e:
            logger.error(f"Error registering plan: {e}")

        return plan_id

    def get_memory_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves past steps in reverse chronological order."""
        try:
            with db_transaction(self.db_target, read_only=True) as con:
                rows = con.execute("""
                    SELECT milestone_id, timestamp_utc, cycle_date, category,
                           author_agent, title, summary, technical_delta,
                           artifacts_json, tags_json
                    FROM souq_milestones_and_memory
                    ORDER BY timestamp_utc DESC
                    LIMIT ?
                """, (limit,)).fetchall()

                return [
                    {
                        "milestone_id": r[0],
                        "timestamp": r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1]),
                        "cycle_date": r[2],
                        "category": r[3],
                        "author_agent": r[4],
                        "title": r[5],
                        "summary": r[6],
                        "technical_delta": r[7],
                        "artifacts": json.loads(r[8]) if r[8] else [],
                        "tags": json.loads(r[9]) if r[9] else []
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error querying memory timeline: {e}")
            return []

    def get_future_plans(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves registered future plans."""
        try:
            with db_transaction(self.db_target, read_only=True) as con:
                query = "SELECT plan_id, target_phase, priority, owner_agent, title, description, dependencies_json, status, target_completion_date FROM souq_future_plans"
                params: tuple = ()
                if status:
                    query += " WHERE status = ?"
                    params = (status,)
                query += " ORDER BY created_at DESC"

                rows = con.execute(query, params).fetchall()
                return [
                    {
                        "plan_id": r[0],
                        "target_phase": r[1],
                        "priority": r[2],
                        "owner_agent": r[3],
                        "title": r[4],
                        "description": r[5],
                        "dependencies": json.loads(r[6]) if r[6] else [],
                        "status": r[7],
                        "target_completion_date": r[8]
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error querying future plans: {e}")
            return []
