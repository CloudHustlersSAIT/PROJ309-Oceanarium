"""Unit tests for the guide matching algorithm (Phase 7a).

Covers all three rules (availability, expertise, language) individually
and in combination, matching acceptance criteria AC-05 through AC-11.
"""
from datetime import date, time

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.guide_matcher import find_eligible_guides
from tests.conftest import make_availability, make_guide, make_tour


# ── Availability Rule Tests ──────────────────────────────────────────


def test_available_guide_is_eligible(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2))  # Monday
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1
    assert result[0].id == guide.id


def test_inactive_guide_excluded(db):
    guide = make_guide(db, is_active=False)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_guide_without_slot_for_day_excluded(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},  # Monday only
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 3))  # Tuesday
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_slot_starts_after_tour_excluded(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(10, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(10, 30))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_slot_ends_before_tour_excluded(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(12, 0)},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2), start_time=time(11, 0), end_time=time(13, 0))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_blocking_exception_excludes_guide(db):
    """AC-06: blocking exception on tour date -> guide excluded."""
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ], exceptions=[
        {"date": date(2026, 3, 2), "type": "blocked", "reason": "Personal leave"},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_non_blocking_exception_keeps_guide(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ], exceptions=[
        {"date": date(2026, 3, 2), "type": "note", "reason": "Dentist at 15:00"},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_overlapping_tour_excludes_guide(db):
    """AC-11: guide has overlapping tour -> excluded."""
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    make_tour(
        db, clorian_booking_id="EXISTING-1",
        tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
        status="assigned", assigned_guide_id=guide.id,
    )
    new_tour = make_tour(
        db, clorian_booking_id="NEW-1",
        tour_date=date(2026, 3, 2), start_time=time(10, 0), end_time=time(12, 0),
    )
    db.commit()

    result = find_eligible_guides(new_tour, db)
    assert len(result) == 0


def test_adjacent_tours_do_not_overlap(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    make_tour(
        db, clorian_booking_id="EXISTING-2",
        tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(10, 0),
        status="assigned", assigned_guide_id=guide.id,
    )
    new_tour = make_tour(
        db, clorian_booking_id="NEW-2",
        tour_date=date(2026, 3, 2), start_time=time(10, 0), end_time=time(11, 0),
    )
    db.commit()

    result = find_eligible_guides(new_tour, db)
    assert len(result) == 1


def test_guide_with_tour_on_different_day_eligible(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
        {"day_of_week": 1, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    make_tour(
        db, clorian_booking_id="EXISTING-3",
        tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
        status="assigned", assigned_guide_id=guide.id,
    )
    new_tour = make_tour(
        db, clorian_booking_id="NEW-3",
        tour_date=date(2026, 3, 3), start_time=time(9, 0), end_time=time(11, 0),
    )
    db.commit()

    result = find_eligible_guides(new_tour, db)
    assert len(result) == 1


# ── Expertise Rule Tests ─────────────────────────────────────────────


def test_matching_expertise_name(db):
    """AC-05: guide with matching expertise name."""
    guide = make_guide(db, expertise_names=["Sharks"], expertise_categories=["Marine Biology"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Sharks", required_category=None)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_matching_expertise_category(db):
    guide = make_guide(db, expertise_names=["Sharks"], expertise_categories=["Marine Biology"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise=None, required_category="Marine Biology")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_no_matching_expertise_excluded(db):
    """AC-07: guide lacks required expertise -> excluded."""
    guide = make_guide(db, expertise_names=["Dolphins"], expertise_categories=["Marine Biology"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Sharks", required_category=None)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_guide_with_multiple_expertises(db):
    guide = make_guide(
        db, expertise_names=["Sharks", "Coral Reef"],
        expertise_categories=["Marine Biology", "Marine Ecology"],
    )
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Coral Reef", required_category=None)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


# ── Language Rule Tests ──────────────────────────────────────────────


def test_matching_language(db):
    """AC-05: guide speaks requested language."""
    guide = make_guide(db, language_codes=["en"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, requested_language_code="en")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_no_matching_language_excluded(db):
    """AC-08: guide does not speak requested language -> excluded."""
    guide = make_guide(db, language_codes=["en"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, requested_language_code="pt")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_guide_with_multiple_languages(db):
    guide = make_guide(db, language_codes=["en", "pt"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, requested_language_code="pt")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


# ── Combined Rules (AND logic) ───────────────────────────────────────


def test_all_rules_pass(db):
    guide = make_guide(db, language_codes=["en"], expertise_names=["Sharks"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Sharks", requested_language_code="en")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_available_but_wrong_expertise(db):
    guide = make_guide(db, language_codes=["en"], expertise_names=["Dolphins"], expertise_categories=["Marine Biology"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Sharks", required_category=None, requested_language_code="en")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_available_but_wrong_language(db):
    guide = make_guide(db, language_codes=["en"], expertise_names=["Sharks"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Sharks", requested_language_code="pt")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_correct_skills_but_unavailable(db):
    guide = make_guide(db, language_codes=["en"], expertise_names=["Sharks"])
    make_availability(db, guide, slots=[
        {"day_of_week": 1, "start_time": time(8, 0), "end_time": time(17, 0)},  # Tuesday only
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2), required_expertise="Sharks", requested_language_code="en")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_no_suitable_guide_returns_empty(db):
    """AC-09: no guide passes all rules -> empty list."""
    guide1 = make_guide(db, name="G1", language_codes=["pt"], expertise_names=["Dolphins"], expertise_categories=["Marine Biology"])
    make_availability(db, guide1, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    guide2 = make_guide(db, name="G2", language_codes=["en"], expertise_names=["Sharks"], is_active=False)
    make_availability(db, guide2, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Sharks", required_category=None, requested_language_code="en")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


# ── Edge-case / Robustness Tests ─────────────────────────────────────


def test_guide_without_availability_pattern_excluded(db):
    make_guide(db)
    tour = make_tour(db)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_tour_without_required_expertise_matches_any_guide(db):
    guide = make_guide(db, expertise_names=["Dolphins"], expertise_categories=["Marine Biology"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise=None, required_category=None)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_tour_without_requested_language_matches_any_guide(db):
    guide = make_guide(db, language_codes=["pt"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, requested_language_code=None)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_tour_without_any_requirements_matches_any_available_guide(db):
    guide = make_guide(db, language_codes=["pt"], expertise_names=["Corals"], expertise_categories=["Ecology"])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise=None, required_category=None, requested_language_code=None)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_cancelled_tour_not_counted_as_overlapping(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    make_tour(
        db, clorian_booking_id="CANCELLED-1",
        tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
        status="cancelled", assigned_guide_id=guide.id,
    )
    new_tour = make_tour(
        db, clorian_booking_id="NEW-CANCEL-1",
        tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0),
    )
    db.commit()

    result = find_eligible_guides(new_tour, db)
    assert len(result) == 1
    assert result[0].id == guide.id


def test_guide_with_empty_languages_excluded(db):
    guide = make_guide(db, language_codes=[])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, requested_language_code="en")
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_guide_with_empty_expertises_excluded(db):
    guide = make_guide(db, expertise_names=[], expertise_categories=[])
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, required_expertise="Sharks", required_category=None)
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0


def test_blocking_exception_on_different_date_does_not_affect(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ], exceptions=[
        {"date": date(2026, 3, 9), "type": "blocked", "reason": "Holiday"},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_eligible_guides_sorted_by_daily_load(db):
    guide_busy = make_guide(db, name="Busy", email="busy@test.com")
    guide_free = make_guide(db, name="Free", email="free@test.com")

    for g in [guide_busy, guide_free]:
        make_availability(db, g, slots=[
            {"day_of_week": 0, "start_time": time(6, 0), "end_time": time(20, 0)},
        ])

    for i in range(3):
        make_tour(
            db, clorian_booking_id=f"BUSY-{i}",
            tour_date=date(2026, 3, 2), start_time=time(6+i, 0), end_time=time(6+i, 30),
            status="assigned", assigned_guide_id=guide_busy.id,
        )

    new_tour = make_tour(
        db, clorian_booking_id="NEW-SORT",
        tour_date=date(2026, 3, 2), start_time=time(14, 0), end_time=time(15, 0),
    )
    db.commit()

    result = find_eligible_guides(new_tour, db)
    assert len(result) == 2
    assert result[0].id == guide_free.id
    assert result[1].id == guide_busy.id


def test_slot_exact_boundary_match(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(9, 0), "end_time": time(11, 0)},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2), start_time=time(9, 0), end_time=time(11, 0))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 1


def test_multiple_slots_same_day_first_matching_used(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(12, 0)},
        {"day_of_week": 0, "start_time": time(13, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, tour_date=date(2026, 3, 2), start_time=time(14, 0), end_time=time(16, 0))
    db.commit()

    result = find_eligible_guides(tour, db)
    assert len(result) == 0
