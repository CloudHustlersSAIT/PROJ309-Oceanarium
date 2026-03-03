"""
Mock poller service -- deterministic Clorian-style test data generator.

Simulates what the real Clorian integration will do: produces batches of
reservation/ticket records with configurable CREATE/UPDATE/UNCHANGED
ratios, inserts them into staging tables, and tracks each run.

This module is used exclusively for testing and local development.
In production, the real Clorian adapter (Phase 6, ADR-005) will replace
the data generation logic, but the staging table schema stays the same.

Tables used (in the ``santiago_tests`` schema):
    - ``mock_poller_runs``: One row per execution; tracks status and counts.
    - ``mock_clorian_staging``: Individual staged records with JSONB payloads.
"""

import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import ValidationError

# ----------------------------------
# Constants
# ----------------------------------

SCHEMA = "santiago_tests"

# ----------------------------------
# Pydantic Request and Response Models
# ----------------------------------


class MockRunRequest(BaseModel):
    """Parameters for a single mock-poller execution."""

    seed: int = Field(
        default=42, description="Deterministic seed for repeatable generation."
    )
    batch_size: int = Field(
        default=10,
        ge=1,
        le=500,
        description="Total number of staged records to generate.",
    )
    update_ratio: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Fraction of records that should be UPDATE.",
    )
    unchanged_ratio: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Fraction of records that should be UNCHANGED.",
    )
    entity_types: List[Literal["reservation", "ticket"]] = Field(
        default=["reservation", "ticket"],
        description="Entity types to generate. Keep Sprint 1 minimal: reservation/ticket.",
    )


class MockRunResponse(BaseModel):
    """Result summary returned after a successful mock-poller run."""

    run_id: str
    status: str
    generated_total: int
    generated_created: int
    generated_updated: int
    generated_unchanged: int


# ----------------------------------
# Deterministic Mock Data Generation Logic
# ----------------------------------

Scenario = Literal["CREATE", "UPDATE", "UNCHANGED"]
EntityType = Literal["reservation", "ticket", "purchase"]


def _deterministic_external_id(rng: random.Random, entity_type: str) -> str:
    """Generate a prefixed external ID like ``RSV-000123`` or ``TKT-000456``.

    The RNG state determines the numeric suffix, so the same seed always
    produces the same sequence of IDs.
    """
    prefix = {"reservation": "RSV", "ticket": "TKT", "purchase": "PUR"}.get(
        entity_type, "UNK"
    )
    n = rng.randint(1, 999999)
    return f"{prefix}-{n:06d}"


def _generate_event_window(rng: random.Random) -> Tuple[str, str]:
    """Return a (start, end) ISO-8601 datetime pair for a 1-hour event.

    The event is placed 1-30 days in the future, between 09:00 and 18:00 UTC.
    """
    days_ahead = rng.randint(1, 30)
    base_date = datetime.now(timezone.utc).date() + timedelta(days=days_ahead)

    start_hour = rng.randint(9, 18)

    start_dt = datetime(
        base_date.year,
        base_date.month,
        base_date.day,
        start_hour,
        0,
        0,
        tzinfo=timezone.utc,
    )

    end_dt = start_dt + timedelta(hours=1)

    return (
        start_dt.isoformat().replace("+00:00", "Z"),
        end_dt.isoformat().replace("+00:00", "Z"),
    )


def _base_payload(
    entity_type: str, external_id: str, rng: random.Random
) -> Dict[str, Any]:
    """Build a realistic Clorian-style JSON payload for a single record.

    Includes customer info, tour program, quantity, notes, and scheduling
    fields whose key names differ by entity type (``eventStartDatetime``
    for reservations vs ``startDatetime`` for tickets).
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    event_start, event_end = _generate_event_window(rng)

    payload = {
        "entity_type": entity_type,
        "external_id": external_id,
        "timestamp_utc": now,
        "customer": {
            "name": f"Customer {rng.randint(1, 200)}",
            "email": f"customer{rng.randint(1, 200)}@example.com",
        },
        "tour": {
            "program_id": rng.randint(1, 120),
            "program_name": rng.choice(
                [
                    "Behind the Scenes",
                    "Night at the Oceanarium",
                    "Coral Explorer",
                    "Shark Dive",
                    "Penguin Encounter",
                    "Whale Watching",
                ]
            ),
        },
        "qty": rng.randint(1, 6),
        "notes": rng.choice(["", "Wheelchair access", "Birthday group", "VIP"]),
    }

    if entity_type == "reservation":
        payload["eventStartDatetime"] = event_start
        payload["eventEndDatetime"] = event_end
    elif entity_type == "ticket":
        payload["startDatetime"] = event_start
        payload["endDatetime"] = event_end

    return payload


def _apply_update(payload: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    """Mutate a copy of *payload* to simulate an UPDATE scenario.

    Changes the quantity, notes, and timestamp so downstream diffing logic
    can detect the record as modified.
    """
    updated = dict(payload)
    updated["qty"] = max(1, min(10, payload.get("qty", 1) + rng.choice([-1, 1, 2])))
    updated["notes"] = rng.choice(
        [
            "Changed note",
            "Late arrival",
            "Dietary restriction",
            payload.get("notes", ""),
        ]
    )
    updated["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    return updated


def generate_records(
    seed: int,
    batch_size: int,
    update_ratio: float,
    unchanged_ratio: float,
    entity_types: List[str],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Generate a deterministic batch of staged records.

    Splits *batch_size* into CREATE, UPDATE, and UNCHANGED buckets based on
    the provided ratios.  UPDATE and UNCHANGED records reuse external IDs
    from a shared pool so that downstream processing can detect them as
    repeat occurrences.

    Args:
        seed: RNG seed for reproducible output.
        batch_size: Total number of records to generate.
        update_ratio: Fraction of records that are UPDATEs (0.0 -- 1.0).
        unchanged_ratio: Fraction that are UNCHANGED (0.0 -- 1.0).
        entity_types: Which entity types to pick from (e.g., ``["reservation", "ticket"]``).

    Returns:
        Tuple of (staged_records_list, counts_dict).

    Raises:
        ValidationError: If ``update_ratio + unchanged_ratio > 1.0``.
    """
    if update_ratio + unchanged_ratio > 1.0:
        raise ValidationError("update_ratio + unchanged_ratio must be <= 1.0")

    rng = random.Random(seed)

    n_update = int(batch_size * update_ratio)
    n_unchanged = int(batch_size * unchanged_ratio)
    n_create = batch_size - n_update - n_unchanged

    # Shared ID pool for UPDATE and UNCHANGED records
    base_ids: List[Tuple[str, str]] = []
    for _ in range(max(n_update + n_unchanged, 1)):
        et = rng.choice(entity_types)
        eid = _deterministic_external_id(rng, et)
        base_ids.append((et, eid))

    staged: List[Dict[str, Any]] = []

    for _ in range(n_create):
        et = rng.choice(entity_types)
        eid = _deterministic_external_id(rng, et)
        payload = _base_payload(et, eid, rng)
        staged.append(
            {
                "entity_type": et,
                "external_id": eid,
                "scenario": "CREATE",
                "payload": payload,
            }
        )

    for i in range(n_unchanged):
        et, eid = base_ids[i % len(base_ids)]
        payload = _base_payload(et, eid, rng)
        staged.append(
            {
                "entity_type": et,
                "external_id": eid,
                "scenario": "UNCHANGED",
                "payload": payload,
            }
        )

    for i in range(n_update):
        et, eid = base_ids[(i + n_unchanged) % len(base_ids)]
        original = _base_payload(et, eid, rng)
        updated = _apply_update(original, rng)
        staged.append(
            {
                "entity_type": et,
                "external_id": eid,
                "scenario": "UPDATE",
                "payload": updated,
            }
        )

    rng.shuffle(staged)

    counts = {
        "total": batch_size,
        "created": n_create,
        "updated": n_update,
        "unchanged": n_unchanged,
    }
    return staged, counts


# ----------------------------------
# Database operations
# ----------------------------------


def create_run(conn, seed: int):
    """Insert a new row into ``mock_poller_runs`` with status RUNNING.

    Returns:
        int: The auto-generated run ID.
    """
    sql = text(f"""
        INSERT INTO {SCHEMA}.mock_poller_runs (
            started_at, status, seed,
            generated_total, generated_created, generated_updated, generated_unchanged
        )
        VALUES (NOW(), 'RUNNING', :seed, 0, 0, 0, 0)
        RETURNING id;
    """)
    return conn.execute(sql, {"seed": seed}).scalar_one()


def insert_staging_rows(conn, run_id: str, staged: List[Dict[str, Any]]) -> None:
    """Bulk-insert all generated records into ``mock_clorian_staging``.

    Each record's payload dict is serialized to JSON and cast to JSONB.
    """
    sql = text(f"""
        INSERT INTO {SCHEMA}.mock_clorian_staging (
            run_id, entity_type, external_id, scenario, payload_json, created_at
        )
        VALUES (
            :run_id, :entity_type, :external_id, :scenario,
            CAST(:payload_json AS jsonb), NOW()
        );
    """)

    params = []
    for item in staged:
        params.append(
            {
                "run_id": run_id,
                "entity_type": item["entity_type"],
                "external_id": item["external_id"],
                "scenario": item["scenario"],
                "payload_json": json.dumps(item["payload"]),
            }
        )

    conn.execute(sql, params)


def finalize_run_success(conn, run_id: str, counts: Dict[str, int]) -> None:
    """Mark a run as SUCCESS and record the final generation counts."""
    sql = text(f"""
        UPDATE {SCHEMA}.mock_poller_runs
        SET
            finished_at = NOW(),
            status = 'SUCCESS',
            generated_total = :total,
            generated_created = :created,
            generated_updated = :updated,
            generated_unchanged = :unchanged
        WHERE id = :run_id;
    """)
    conn.execute(sql, {"run_id": run_id, **counts})


def finalize_run_failure(conn, run_id: str, error_message: str) -> None:
    """Mark a run as FAILED and store the error message (truncated to 5 000 chars)."""
    sql = text(f"""
        UPDATE {SCHEMA}.mock_poller_runs
        SET
            finished_at = NOW(),
            status = 'FAILED',
            error_message = :error_message
        WHERE id = :run_id;
    """)
    conn.execute(sql, {"run_id": run_id, "error_message": error_message[:5000]})


# ----------------------------------
# Orchestration
# ----------------------------------


def run_mock_poller_service(
    conn, req: MockRunRequest
) -> MockRunResponse:
    """Execute one full mock-poller cycle within a caller-provided transaction.

    Steps:
        1. Generate the deterministic batch of staged records.
        2. Insert a new run row (status = RUNNING).
        3. Bulk-insert all staged records.
        4. Finalize the run as SUCCESS with counts.

    The caller (the route) is responsible for committing the transaction
    and for calling ``finalize_run_failure`` if a DB error occurs after
    the run row was created.

    Args:
        conn: SQLAlchemy connection (inside an active transaction).
        req: ``MockRunRequest`` with seed, batch_size, ratios, entity_types.

    Returns:
        MockRunResponse: Summary of the completed run.

    Raises:
        ValidationError: If ratio constraints are violated.
    """
    staged, counts = generate_records(
        seed=req.seed,
        batch_size=req.batch_size,
        update_ratio=req.update_ratio,
        unchanged_ratio=req.unchanged_ratio,
        entity_types=req.entity_types,
    )

    run_id = create_run(conn, seed=req.seed)
    insert_staging_rows(conn, run_id=run_id, staged=staged)
    finalize_run_success(conn, run_id=run_id, counts=counts)

    return MockRunResponse(
        run_id=str(run_id),
        status="SUCCESS",
        generated_total=counts["total"],
        generated_created=counts["created"],
        generated_updated=counts["updated"],
        generated_unchanged=counts["unchanged"],
    )
