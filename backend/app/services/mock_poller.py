"""
Mock poller service for Clorian integration testing.

Current behavior
----------------
- Creates a poll execution record
- Generates deterministic reservation payloads
- Each reservation contains nested tickets
- Inserts reservation payloads into staging as raw JSON
- Finalizes execution with success/failure metadata

Design notes
------------
- Only reservation entities are staged
- Tickets are embedded inside the reservation payload
- JSON-first approach is intentional to support a listener/processor
- Deterministic generation supports replayability and idempotency testing
- UPDATE and UNCHANGED only apply to reservations that already exist
  from previous successful runs
- Tour/program metadata is loaded from public.tours
"""

import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import text

from .exceptions import ValidationError
from .mock_seed import load_guide_capabilities

# =========================================================
# Constants
# =========================================================

RUN_TABLE = "public.poll_execution"
STAGING_TABLE = "public.poll_staging"

Scenario = Literal["CREATE", "UPDATE", "UNCHANGED"]

FIRST_NAMES = [
    "Emma",
    "Liam",
    "Sofia",
    "Noah",
    "Olivia",
    "Lucas",
    "Mia",
    "Ethan",
    "Isabella",
    "James",
    "Ana",
    "Miguel",
    "Maria",
    "Pedro",
    "Joana",
]

LAST_NAMES = [
    "Silva",
    "Santos",
    "Ferreira",
    "Oliveira",
    "Costa",
    "Rodrigues",
    "Martins",
    "Pereira",
    "Almeida",
    "Sousa",
    "Johnson",
    "Williams",
    "Brown",
    "Taylor",
    "Anderson",
]

LANGUAGES = ["en", "pt", "es", "fr", "zh"]

# Weighted language distribution for generated payloads.
# - en: most common
# - zh: least common
# - pt/es/fr: equal likelihood
LANGUAGE_WEIGHTS = {
    "en": 5,
    "pt": 2,
    "es": 2,
    "fr": 2,
    "zh": 1,
}

VENUES = [
    {"venue_id": 10, "venue_name": "Main Oceanarium"},
    {"venue_id": 11, "venue_name": "Deep Sea Pavilion"},
    {"venue_id": 12, "venue_name": "Tropical Reef Wing"},
]

BUYER_TYPES = {
    "adult": {"buyer_type_id": 1, "buyer_type_name": "Adult", "price": 45.00},
    "child": {"buyer_type_id": 2, "buyer_type_name": "Child", "price": 25.00},
}

# Future reservations should not look "used" yet
TICKET_STATUSES_FUTURE = ["ACTIVE", "PENDING"]
RESERVATION_STATUSES_CREATE = ["CONFIRMED", "PENDING"]
RESERVATION_STATUSES_UPDATE = ["CONFIRMED", "PENDING", "CANCELLED"]

# Bias create scenarios toward a smaller reusable slot pool so batches naturally
# produce multiple reservations for the same schedule.
CREATE_SLOT_REUSE_PROBABILITY = 0.80
CREATE_SLOT_POOL_MAX_SIZE = 4


# =========================================================
# Request / Response Models
# =========================================================


class MockRunRequest(BaseModel):
    seed: int = Field(default=42, description="Deterministic seed for repeatable generation.")
    batch_size: int = Field(default=10, ge=1, le=500, description="Number of reservations to generate.")
    update_ratio: float = Field(
        default=0.30, ge=0.0, le=1.0, description="Fraction of reservations that should be UPDATE."
    )
    unchanged_ratio: float = Field(
        default=0.20, ge=0.0, le=1.0, description="Fraction of reservations that should be UNCHANGED."
    )
    create_slot_reuse_probability: float = Field(
        default=CREATE_SLOT_REUSE_PROBABILITY,
        ge=0.0,
        le=1.0,
        description="Probability that each CREATE reservation reuses a shared schedule fingerprint.",
    )
    create_slot_pool_max_size: int = Field(
        default=CREATE_SLOT_POOL_MAX_SIZE,
        ge=1,
        le=50,
        description="Maximum number of distinct shared schedule fingerprints available to CREATE reservations.",
    )


class MockRunResponse(BaseModel):
    run_id: str
    status: str
    generated_total: int
    generated_created: int
    generated_updated: int
    generated_unchanged: int


# =========================================================
# Helper Functions - IDs / Dates / Payloads
# =========================================================


def _deterministic_external_id(rng: random.Random, prefix: str) -> str:
    """
    Generates deterministic string external IDs.
    Examples:
      RSV-000123
      TKT-000123-001
      CUST-000123
    """
    n = rng.randint(1, 999999)
    return f"{prefix}-{n:06d}"


def _generate_purchase_id(rng: random.Random) -> int:
    """
    Generates a deterministic numeric purchase ID.
    """
    return rng.randint(100000, 999999)


def _generate_event_window(rng: random.Random) -> tuple[str, str]:
    """
    Generates realistic future event windows:
    - 1 to 14 days in the future
    - fixed business-hour starts
    - duration 1 or 2 hours
    """
    days_ahead = rng.randint(1, 14)
    base_date = datetime.now(timezone.utc).date() + timedelta(days=days_ahead)

    start_hour = rng.choice([9, 10, 11, 14, 15, 16])
    duration_hours = rng.choice([1, 2])

    start_dt = datetime(
        base_date.year,
        base_date.month,
        base_date.day,
        start_hour,
        0,
        0,
        tzinfo=timezone.utc,
    )

    end_dt = start_dt + timedelta(hours=duration_hours)

    return (
        start_dt.isoformat().replace("+00:00", "Z"),
        end_dt.isoformat().replace("+00:00", "Z"),
    )


def _build_create_schedule_pool(
    rng: random.Random,
    tours: list[dict[str, Any]],
    guide_caps: list[dict[str, Any]],
    create_count: int,
    pool_max_size: int,
) -> list[dict[str, Any]]:
    """Build a small pool of reusable schedule fingerprints for CREATE rows."""
    if create_count <= 1:
        return []

    pool_size = max(1, min(pool_max_size, create_count // 3 or 1))
    pool: list[dict[str, Any]] = []

    for _ in range(pool_size):
        event_start, event_end = _generate_event_window(rng)

        if guide_caps:
            pair = _pick_assignable_pair(rng, guide_caps)
            selected_tour = next(
                (tour for tour in tours if tour["clorian_product_id"] == pair["clorian_product_id"]),
                rng.choice(tours),
            )
            language_code = pair["language_code"]
        else:
            selected_tour = rng.choice(tours)
            language_code = _pick_language(rng)

        pool.append(
            {
                "event_start_datetime": event_start,
                "event_end_datetime": event_end,
                "selected_tour": selected_tour,
                "language_code": language_code,
            }
        )

    return pool


def _pick_reservation_status(rng: random.Random, scenario: Scenario) -> str:
    """
    Keeps status logically consistent with the scenario.
    """
    if scenario == "CREATE":
        return rng.choice(RESERVATION_STATUSES_CREATE)
    if scenario == "UPDATE":
        return rng.choice(RESERVATION_STATUSES_UPDATE)
    # UNCHANGED should preserve previous status in practice
    return rng.choice(RESERVATION_STATUSES_CREATE)


def _pick_language(rng: random.Random) -> str:
    """Pick a language using weighted probabilities."""
    weights = [LANGUAGE_WEIGHTS.get(language_code, 1) for language_code in LANGUAGES]
    return rng.choices(LANGUAGES, weights=weights, k=1)[0]


def _pick_assignable_pair(rng: random.Random, guide_caps: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick an assignable (tour, language) pair with language-weighted bias."""
    weights = [LANGUAGE_WEIGHTS.get(pair.get("language_code", ""), 1) for pair in guide_caps]
    return rng.choices(guide_caps, weights=weights, k=1)[0]


def load_tours(conn) -> list[dict[str, Any]]:
    """
    Loads tours from the database so program_id and program_name remain consistent.

    program_id in the mock payload maps to tours.clorian_product_id
    """
    sql = text(
        """
        SELECT id, clorian_product_id, name, description, duration
        FROM public.tours
        ORDER BY id
        """
    )

    result = conn.execute(sql)
    rows = result.fetchall()

    tours: list[dict[str, Any]] = []
    for row in rows:
        tours.append(
            {
                "id": row.id,
                "clorian_product_id": row.clorian_product_id,
                "name": row.name,
                "description": row.description,
                "duration": row.duration,
            }
        )

    if not tours:
        raise ValidationError(
            "No tours found in public.tours. Populate the tours table before running the mock poller."
        )

    return tours


def _build_ticket(
    reservation_external_id: str,
    reservation_timestamp: str,
    start_datetime: str,
    end_datetime: str,
    buyer_type: Literal["adult", "child"],
    ticket_index: int,
    venue: dict[str, Any],
    rng: random.Random,
) -> dict[str, Any]:
    """
    Builds one nested ticket object inside the reservation payload.
    This mirrors the external payload, not your internal DB row.
    """
    buyer = BUYER_TYPES[buyer_type]

    reservation_suffix = reservation_external_id.split("-")[-1]
    clorian_ticket_id = f"TKT-{reservation_suffix}-{ticket_index:03d}"

    return {
        "clorian_ticket_id": clorian_ticket_id,
        "reservation_external_id": reservation_external_id,
        "buyer_type_id": buyer["buyer_type_id"],
        "buyer_type_name": buyer["buyer_type_name"],
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "ticket_status": rng.choice(TICKET_STATUSES_FUTURE),
        "price": round(buyer["price"], 2),
        "venue_id": venue["venue_id"],
        "venue_name": venue["venue_name"],
        "clorian_created_at": reservation_timestamp,
        "clorian_modified_at": reservation_timestamp,
    }


def _build_reservation_payload(
    clorian_reservation_id: str,
    rng: random.Random,
    tours: list[dict[str, Any]],
    scenario: Scenario = "CREATE",
    assignable_pair: dict[str, Any] | None = None,
    shared_schedule: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Builds a realistic reservation payload aligned with the reservations table
    and expected external/source data structure.

    When assignable_pair is provided, uses that tour+language combo to guarantee
    the resulting schedule can be assigned to a guide with matching capabilities.
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)

    if shared_schedule:
        event_start = shared_schedule["event_start_datetime"]
        event_end = shared_schedule["event_end_datetime"]
        selected_tour = shared_schedule["selected_tour"]
        language_code = shared_schedule["language_code"]
    else:
        event_start, event_end = _generate_event_window(rng)

    if not shared_schedule and assignable_pair:
        cpid = assignable_pair["clorian_product_id"]
        selected_tour = next((t for t in tours if t["clorian_product_id"] == cpid), rng.choice(tours))
        language_code = assignable_pair["language_code"]
    elif not shared_schedule:
        selected_tour = rng.choice(tours)
        language_code = _pick_language(rng)

    venue = rng.choice(VENUES)

    adult_count = rng.randint(1, 4)
    child_count = rng.randint(0, 3)
    total_tickets = adult_count + child_count

    tickets: list[dict[str, Any]] = []
    ticket_counter = 1

    for _ in range(adult_count):
        tickets.append(
            _build_ticket(
                reservation_external_id=clorian_reservation_id,
                reservation_timestamp=now,
                start_datetime=event_start,
                end_datetime=event_end,
                buyer_type="adult",
                ticket_index=ticket_counter,
                venue=venue,
                rng=rng,
            )
        )
        ticket_counter += 1

    for _ in range(child_count):
        tickets.append(
            _build_ticket(
                reservation_external_id=clorian_reservation_id,
                reservation_timestamp=now,
                start_datetime=event_start,
                end_datetime=event_end,
                buyer_type="child",
                ticket_index=ticket_counter,
                venue=venue,
                rng=rng,
            )
        )
        ticket_counter += 1

    return {
        "entity_type": "reservation",
        "clorian_reservation_id": clorian_reservation_id,
        "clorian_purchase_id": _generate_purchase_id(rng),
        "status": _pick_reservation_status(rng, scenario),
        "language_code": language_code,
        "event_start_datetime": event_start,
        "event_end_datetime": event_end,
        "current_ticket_num": total_tickets,
        "clorian_created_at": now,
        "clorian_modified_at": now,
        "customer": {
            "clorian_client_id": _deterministic_external_id(rng, "CUST"),
            "first_name": first,
            "last_name": last,
            "name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}@example.com",
        },
        "tour": {
            "program_id": selected_tour["clorian_product_id"],
            "program_name": selected_tour["name"],
            "description": selected_tour["description"],
            "duration": selected_tour["duration"],
        },
        "venue": {
            "venue_id": venue["venue_id"],
            "venue_name": venue["venue_name"],
        },
        "tickets_summary": {
            "adult": adult_count,
            "child": child_count,
            "total": total_tickets,
        },
        "tickets": tickets,
        "notes": rng.choice(["", "Wheelchair access", "Birthday group", "VIP"]),
    }


def _apply_update(payload: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """
    Applies realistic changes to simulate UPDATE scenarios.
    Since tickets are nested, changing reservation-level ticket counts also
    regenerates the nested tickets array.
    """
    updated = dict(payload)

    new_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    updated["clorian_modified_at"] = new_timestamp
    updated["notes"] = rng.choice(["Changed note", "Late arrival", "Dietary restriction", payload.get("notes", "")])

    updated["status"] = _pick_reservation_status(rng, "UPDATE")
    updated["language_code"] = _pick_language(rng)

    # Rebuild tickets_summary with a realistic small variation
    original_summary = updated.get("tickets_summary", {})
    adult = max(0, min(6, original_summary.get("adult", 1) + rng.choice([-1, 0, 1])))
    child = max(0, min(6, original_summary.get("child", 0) + rng.choice([-1, 0, 1])))

    if adult + child == 0:
        adult = 1

    total = adult + child

    updated["tickets_summary"] = {
        "adult": adult,
        "child": child,
        "total": total,
    }
    updated["current_ticket_num"] = total

    event_start = updated["event_start_datetime"]
    event_end = updated["event_end_datetime"]
    clorian_reservation_id = updated["clorian_reservation_id"]
    venue = updated["venue"]

    tickets: list[dict[str, Any]] = []
    ticket_counter = 1

    for _ in range(adult):
        ticket = _build_ticket(
            reservation_external_id=clorian_reservation_id,
            reservation_timestamp=updated["clorian_created_at"],
            start_datetime=event_start,
            end_datetime=event_end,
            buyer_type="adult",
            ticket_index=ticket_counter,
            venue=venue,
            rng=rng,
        )
        ticket["clorian_modified_at"] = new_timestamp
        tickets.append(ticket)
        ticket_counter += 1

    for _ in range(child):
        ticket = _build_ticket(
            reservation_external_id=clorian_reservation_id,
            reservation_timestamp=updated["clorian_created_at"],
            start_datetime=event_start,
            end_datetime=event_end,
            buyer_type="child",
            ticket_index=ticket_counter,
            venue=venue,
            rng=rng,
        )
        ticket["clorian_modified_at"] = new_timestamp
        tickets.append(ticket)
        ticket_counter += 1

    updated["tickets"] = tickets

    return updated


def load_existing_reservations(conn) -> dict[str, dict[str, Any]]:
    """
    Loads the latest staged payload for each reservation external_id from
    previous successful poll executions.
    """
    sql = text(
        f"""
        SELECT DISTINCT ON (ps.external_id)
            ps.external_id,
            ps.payload_json
        FROM {STAGING_TABLE} ps
        INNER JOIN {RUN_TABLE} pe
            ON pe.id = ps.poll_execution_id
        WHERE
            ps.entity_type = 'reservation'
            AND pe.status = 'SUCCESS'
        ORDER BY ps.external_id, ps.created_at DESC;
        """
    )

    result = conn.execute(sql)
    rows = result.fetchall()

    existing: dict[str, dict[str, Any]] = {}
    for row in rows:
        existing[row.external_id] = row.payload_json

    return existing


# =========================================================
# Record Generation
# =========================================================


def generate_records(
    conn,
    seed: int,
    batch_size: int,
    update_ratio: float,
    unchanged_ratio: float,
    create_slot_reuse_probability: float = CREATE_SLOT_REUSE_PROBABILITY,
    create_slot_pool_max_size: int = CREATE_SLOT_POOL_MAX_SIZE,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Generates deterministic staged reservation records.

    Rules:
    - CREATE generates brand-new reservation IDs
    - UPDATE and UNCHANGED only use reservations that already exist from prior runs
    """
    if update_ratio + unchanged_ratio > 1.0:
        raise ValidationError("update_ratio + unchanged_ratio must be <= 1.0")

    rng = random.Random(seed)

    tours = load_tours(conn)
    guide_caps = load_guide_capabilities(conn)
    existing_reservations = load_existing_reservations(conn)
    existing_ids = list(existing_reservations.keys())
    rng.shuffle(existing_ids)

    requested_update = int(batch_size * update_ratio)
    requested_unchanged = int(batch_size * unchanged_ratio)

    n_update = min(requested_update, len(existing_ids))
    remaining_existing = len(existing_ids) - n_update
    n_unchanged = min(requested_unchanged, remaining_existing)

    n_create = batch_size - n_update - n_unchanged

    staged: list[dict[str, Any]] = []
    create_schedule_pool = _build_create_schedule_pool(
        rng,
        tours,
        guide_caps,
        n_create,
        create_slot_pool_max_size,
    )

    # CREATE: always brand-new IDs
    used_ids = set(existing_ids)

    for _ in range(n_create):
        while True:
            res_id = _deterministic_external_id(rng, "RSV")
            if res_id not in used_ids:
                used_ids.add(res_id)
                break

        shared_schedule = None
        if create_schedule_pool and rng.random() < create_slot_reuse_probability:
            shared_schedule = rng.choice(create_schedule_pool)

        pair = None if shared_schedule else (_pick_assignable_pair(rng, guide_caps) if guide_caps else None)
        res_payload = _build_reservation_payload(
            clorian_reservation_id=res_id,
            rng=rng,
            tours=tours,
            scenario="CREATE",
            assignable_pair=pair,
            shared_schedule=shared_schedule,
        )

        staged.append(
            {
                "entity_type": "reservation",
                "external_id": res_payload["clorian_reservation_id"],
                "scenario": "CREATE",
                "payload": res_payload,
            }
        )

    # UPDATE: must use existing rows
    update_ids = existing_ids[:n_update]

    for res_id in update_ids:
        original = existing_reservations[res_id]
        updated = _apply_update(original, rng)

        staged.append(
            {
                "entity_type": "reservation",
                "external_id": updated["clorian_reservation_id"],
                "scenario": "UPDATE",
                "payload": updated,
            }
        )

    # UNCHANGED: must use existing rows
    unchanged_ids = existing_ids[n_update : n_update + n_unchanged]

    for res_id in unchanged_ids:
        unchanged_payload = existing_reservations[res_id]

        staged.append(
            {
                "entity_type": "reservation",
                "external_id": unchanged_payload["clorian_reservation_id"],
                "scenario": "UNCHANGED",
                "payload": unchanged_payload,
            }
        )

    rng.shuffle(staged)

    counts = {
        "total": len(staged),
        "created": n_create,
        "updated": n_update,
        "unchanged": n_unchanged,
    }

    return staged, counts


# =========================================================
# Database Operations
# =========================================================


def create_run(conn, seed: int) -> int:
    sql = text(
        f"""
        INSERT INTO {RUN_TABLE} (
            window_start,
            window_end,
            executed_at,
            status,
            seed,
            generated_total,
            generated_created,
            generated_updated,
            generated_unchanged
        )
        VALUES (
            NOW(),
            NOW(),
            NOW(),
            'RUNNING',
            :seed,
            0,
            0,
            0,
            0
        )
        RETURNING id;
        """
    )
    return conn.execute(sql, {"seed": seed}).scalar_one()


def insert_staging_rows(conn, run_id: int, staged: list[dict[str, Any]]) -> None:
    sql = text(
        f"""
        INSERT INTO {STAGING_TABLE} (
            poll_execution_id,
            entity_type,
            external_id,
            scenario,
            payload_json,
            created_at
        )
        VALUES (
            :poll_execution_id,
            :entity_type,
            :external_id,
            :scenario,
            CAST(:payload_json AS jsonb),
            NOW()
        );
        """
    )

    params = []
    for item in staged:
        params.append(
            {
                "poll_execution_id": run_id,
                "entity_type": item["entity_type"],
                "external_id": item["external_id"],
                "scenario": item["scenario"],
                "payload_json": json.dumps(item["payload"]),
            }
        )

    conn.execute(sql, params)


def finalize_run_success(conn, run_id: int, counts: dict[str, int]) -> None:
    sql = text(
        f"""
        UPDATE {RUN_TABLE}
        SET
            finished_at = NOW(),
            status = 'SUCCESS',
            generated_total = :total,
            generated_created = :created,
            generated_updated = :updated,
            generated_unchanged = :unchanged
        WHERE id = :run_id;
        """
    )
    conn.execute(sql, {"run_id": run_id, **counts})


def finalize_run_failure(conn, run_id: int, error_message: str) -> None:
    sql = text(
        f"""
        UPDATE {RUN_TABLE}
        SET
            finished_at = NOW(),
            status = 'FAILED',
            error_message = :error_message
        WHERE id = :run_id;
        """
    )
    conn.execute(
        sql,
        {
            "run_id": run_id,
            "error_message": error_message[:5000],
        },
    )


# =========================================================
# Main Service Entry Point
# =========================================================


def run_mock_poller_service(conn, req: MockRunRequest) -> MockRunResponse:
    """
    Main service used by the route layer.

    Flow:
    1. Create execution/run row
    2. Generate deterministic reservation records
    3. Insert rows into staging
    4. Finalize run
    """
    run_id = create_run(conn, seed=req.seed)

    try:
        staged, counts = generate_records(
            conn=conn,
            seed=req.seed,
            batch_size=req.batch_size,
            update_ratio=req.update_ratio,
            unchanged_ratio=req.unchanged_ratio,
            create_slot_reuse_probability=req.create_slot_reuse_probability,
            create_slot_pool_max_size=req.create_slot_pool_max_size,
        )

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

    except Exception:
        # Let the route layer catch and call finalize_run_failure if needed
        raise
