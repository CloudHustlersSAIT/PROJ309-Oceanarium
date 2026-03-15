"""
Mock seed service for E2E testing bootstrap.

Creates the minimum reference data needed for the mock poller -> auto-assignment ->
notification chain to work end-to-end:

- Tours (with clorian_product_id matching mock_poller VENUES)
- Languages
- Admin user (email from AUTH_BYPASS_EMAIL env var)
- Guides with language and tour expertise links
- Availability patterns and slots (weekdays 09:00-17:00)

Design notes
------------
- Idempotent: uses ON CONFLICT to skip existing rows
- Follows the same service-layer pattern as mock_poller.py
- Guide capabilities are defined as structured data so mock_poller.py
  can load them to generate only assignable tour+language combinations
"""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text

logger = logging.getLogger(__name__)

# =========================================================
# Seed data definitions
# =========================================================

TOURS = [
    {
        "clorian_product_id": 10,
        "name": "Main Oceanarium",
        "description": "The main oceanarium experience",
        "duration": 90,
    },
    {"clorian_product_id": 11, "name": "Deep Sea Pavilion", "description": "Deep sea exploration tour", "duration": 60},
    {
        "clorian_product_id": 12,
        "name": "Tropical Reef Wing",
        "description": "Tropical reef guided tour",
        "duration": 75,
    },
]

LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "zh", "name": "Chinese"},
]

GUIDES = [
    {
        "first_name": "Marina",
        "last_name": "Costa",
        "email": "marina.costa@oceanarium.test",
        "phone": "+351900000001",
        "language_codes": ["en", "pt"],
        "tour_clorian_ids": [10, 11, 12],
    },
    {
        "first_name": "Carlos",
        "last_name": "Santos",
        "email": "carlos.santos@oceanarium.test",
        "phone": "+351900000002",
        "language_codes": ["es", "fr"],
        "tour_clorian_ids": [10, 11],
    },
    {
        "first_name": "Yuki",
        "last_name": "Tanaka",
        "email": "yuki.tanaka@oceanarium.test",
        "phone": "+351900000003",
        "language_codes": ["en", "zh"],
        "tour_clorian_ids": [11, 12],
    },
]

AVAILABILITY_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


# =========================================================
# Response model
# =========================================================


class SeedResponse(BaseModel):
    success: bool
    created: dict[str, int]


# =========================================================
# Helpers
# =========================================================


def _seed_tours(conn) -> tuple[dict[int, int], int]:
    """Insert tours and return {clorian_product_id: internal_id} map."""
    count = 0
    for t in TOURS:
        result = conn.execute(
            text("""
                INSERT INTO tours (clorian_product_id, name, description, duration)
                VALUES (:clorian_id, :name, :desc, :duration)
                ON CONFLICT (clorian_product_id) DO NOTHING
                RETURNING id
            """),
            {
                "clorian_id": t["clorian_product_id"],
                "name": t["name"],
                "desc": t["description"],
                "duration": t["duration"],
            },
        ).fetchone()
        if result:
            count += 1

    rows = conn.execute(text("SELECT id, clorian_product_id FROM tours ORDER BY id")).fetchall()
    tour_map = {row[1]: row[0] for row in rows}
    return tour_map, count


def _seed_languages(conn) -> tuple[dict[str, int], int]:
    """Insert languages and return {code: internal_id} map."""
    count = 0
    for lang in LANGUAGES:
        result = conn.execute(
            text("""
                INSERT INTO languages (code, name)
                VALUES (:code, :name)
                ON CONFLICT (code) DO NOTHING
                RETURNING id
            """),
            {"code": lang["code"], "name": lang["name"]},
        ).fetchone()
        if result:
            count += 1

    rows = conn.execute(text("SELECT id, code FROM languages")).fetchall()
    lang_map = {row[1]: row[0] for row in rows}
    return lang_map, count


def _seed_admin(conn) -> int:
    """Insert admin user and return count of created rows."""
    admin_email = os.getenv("AUTH_BYPASS_EMAIL", "local-dev@oceanarium.local").strip().lower()
    result = conn.execute(
        text("""
            INSERT INTO users (username, email, password_hash, full_name, role, is_active)
            VALUES ('admin_test', :email, 'not-a-real-hash', 'Test Admin', 'admin', true)
            ON CONFLICT (username) DO UPDATE SET email = EXCLUDED.email
            RETURNING id
        """),
        {"email": admin_email},
    ).fetchone()
    return 1 if result else 0


def _seed_guides(conn, tour_map: dict[int, int], lang_map: dict[str, int]) -> dict[str, int]:
    """Insert guides with language and tour expertise links. Returns per-entity counts."""
    counts: dict[str, int] = {"guides": 0, "guide_languages": 0, "guide_tour_types": 0}

    for g in GUIDES:
        row = conn.execute(
            text("""
                INSERT INTO guides (first_name, last_name, email, phone, is_active)
                VALUES (:first, :last, :email, :phone, true)
                ON CONFLICT DO NOTHING
                RETURNING id
            """),
            {"first": g["first_name"], "last": g["last_name"], "email": g["email"], "phone": g["phone"]},
        ).fetchone()

        if row:
            guide_id = row[0]
            counts["guides"] += 1
        else:
            existing = conn.execute(
                text("SELECT id FROM guides WHERE email = :email"),
                {"email": g["email"]},
            ).fetchone()
            guide_id = existing[0] if existing else None

        if guide_id is None:
            continue

        for lc in g["language_codes"]:
            lid = lang_map.get(lc)
            if lid:
                r = conn.execute(
                    text("""
                        INSERT INTO guide_languages (guide_id, language_id)
                        VALUES (:gid, :lid)
                        ON CONFLICT DO NOTHING
                        RETURNING guide_id
                    """),
                    {"gid": guide_id, "lid": lid},
                ).fetchone()
                if r:
                    counts["guide_languages"] += 1

        for cpid in g["tour_clorian_ids"]:
            tid = tour_map.get(cpid)
            if tid:
                r = conn.execute(
                    text("""
                        INSERT INTO guide_tour_types (guide_id, tour_id)
                        VALUES (:gid, :tid)
                        ON CONFLICT DO NOTHING
                        RETURNING guide_id
                    """),
                    {"gid": guide_id, "tid": tid},
                ).fetchone()
                if r:
                    counts["guide_tour_types"] += 1

    return counts


def _seed_availability(conn) -> dict[str, int]:
    """Create availability patterns and weekday slots for all guides."""
    counts: dict[str, int] = {"availability_patterns": 0, "availability_slots": 0}

    guide_ids = [
        row[0] for row in conn.execute(text("SELECT id FROM guides WHERE is_active = true ORDER BY id")).fetchall()
    ]

    for guide_id in guide_ids:
        existing = conn.execute(
            text("SELECT id FROM availability_patterns WHERE guide_id = :gid"),
            {"gid": guide_id},
        ).fetchone()
        if existing:
            continue

        pattern = conn.execute(
            text("""
                INSERT INTO availability_patterns (guide_id, timezone)
                VALUES (:gid, 'Europe/Lisbon')
                RETURNING id
            """),
            {"gid": guide_id},
        ).fetchone()
        pattern_id = pattern[0]
        counts["availability_patterns"] += 1

        for day in AVAILABILITY_WEEKDAYS:
            conn.execute(
                text("""
                    INSERT INTO availability_slots (pattern_id, day_of_week, start_time, end_time)
                    VALUES (:pid, :day, '09:00', '17:00')
                """),
                {"pid": pattern_id, "day": day},
            )
            counts["availability_slots"] += 1

    return counts


# =========================================================
# Public API — guide capabilities for mock_poller
# =========================================================


def load_guide_capabilities(conn) -> list[dict[str, Any]]:
    """Load assignable (tour_clorian_product_id, language_code) pairs from the DB.

    Used by mock_poller to generate reservations that can actually be assigned.
    """
    rows = conn.execute(
        text("""
            SELECT DISTINCT t.clorian_product_id, l.code
            FROM guide_tour_types gtt
            JOIN guides g ON g.id = gtt.guide_id AND g.is_active = true
            JOIN tours t ON t.id = gtt.tour_id
            JOIN guide_languages gl ON gl.guide_id = g.id
            JOIN languages l ON l.id = gl.language_id
        """)
    ).fetchall()

    return [{"clorian_product_id": row[0], "language_code": row[1]} for row in rows]


# =========================================================
# Main entry point
# =========================================================


def run_seed(conn) -> SeedResponse:
    """Idempotent seed of all reference data required for E2E testing."""
    tour_map, tours_created = _seed_tours(conn)
    lang_map, langs_created = _seed_languages(conn)
    admin_created = _seed_admin(conn)
    guide_counts = _seed_guides(conn, tour_map, lang_map)
    avail_counts = _seed_availability(conn)

    created = {
        "tours": tours_created,
        "languages": langs_created,
        "users": admin_created,
        **guide_counts,
        **avail_counts,
    }

    logger.info(f"Seed completed: {created}")
    return SeedResponse(success=True, created=created)
