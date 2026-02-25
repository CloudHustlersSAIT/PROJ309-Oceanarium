"""Unit tests for assignment execution (Phase 7b).

Covers auto-assign, load balancing, unassigned flagging,
manual override, and audit logging.
"""
from datetime import date, time

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.audit_log import TourAssignmentLog
from app.models.guide import Guide
from app.services.assignment import assign_guide_to_tour, manual_assign, release_guide
from tests.conftest import make_availability, make_guide, make_tour


def test_single_eligible_guide_assigned(db):
    guide = make_guide(db, name="Ana")
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db)
    db.commit()

    result = assign_guide_to_tour(tour, db)
    db.commit()

    assert result is not None
    assert result.id == guide.id
    assert tour.status == "assigned"
    assert tour.assigned_guide_id == guide.id

    log = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
        TourAssignmentLog.action == "assigned",
    ).first()
    assert log is not None
    assert log.assignment_type == "auto"


def test_multiple_guides_least_busy_wins(db):
    """AC-10: guide with fewest tours that day is assigned."""
    guide_a = make_guide(db, name="A", email="a@test.com")
    guide_b = make_guide(db, name="B", email="b@test.com")
    guide_c = make_guide(db, name="C", email="c@test.com")

    for g in [guide_a, guide_b, guide_c]:
        make_availability(db, g, slots=[
            {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
        ])

    for i in range(3):
        make_tour(db, clorian_booking_id=f"A-{i}", tour_date=date(2026, 3, 2),
                  start_time=time(6+i, 0), end_time=time(6+i, 30),
                  status="assigned", assigned_guide_id=guide_a.id)
    make_tour(db, clorian_booking_id="B-0", tour_date=date(2026, 3, 2),
              start_time=time(6, 0), end_time=time(6, 30),
              status="assigned", assigned_guide_id=guide_b.id)
    for i in range(2):
        make_tour(db, clorian_booking_id=f"C-{i}", tour_date=date(2026, 3, 2),
                  start_time=time(6+i, 0), end_time=time(6+i, 30),
                  status="assigned", assigned_guide_id=guide_c.id)

    new_tour = make_tour(db, clorian_booking_id="NEW-LB",
                         tour_date=date(2026, 3, 2),
                         start_time=time(14, 0), end_time=time(15, 0))
    db.commit()

    result = assign_guide_to_tour(new_tour, db)
    db.commit()

    assert result is not None
    assert result.id == guide_b.id


def test_multiple_guides_tie_breaking(db):
    guide_a = make_guide(db, name="A", email="a@test.com")
    guide_b = make_guide(db, name="B", email="b@test.com")

    for g in [guide_a, guide_b]:
        make_availability(db, g, slots=[
            {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
        ])

    tour = make_tour(db)
    db.commit()

    result = assign_guide_to_tour(tour, db)
    db.commit()

    assert result is not None
    assert result.id in (guide_a.id, guide_b.id)


def test_no_eligible_guide_flags_unassigned(db):
    """AC-09: no suitable guide -> tour flagged unassigned."""
    tour = make_tour(db)
    db.commit()

    result = assign_guide_to_tour(tour, db)
    db.commit()

    assert result is None
    assert tour.status == "unassigned"

    log = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
        TourAssignmentLog.action == "unassigned",
    ).first()
    assert log is not None


def test_assignment_creates_audit_log(db):
    guide = make_guide(db)
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db)
    db.commit()

    assign_guide_to_tour(tour, db)
    db.commit()

    logs = db.query(TourAssignmentLog).filter(TourAssignmentLog.tour_id == tour.id).all()
    assert len(logs) >= 1
    assigned_log = [l for l in logs if l.action == "assigned"][0]
    assert assigned_log.guide_id == guide.id
    assert assigned_log.assignment_type == "auto"
    assert assigned_log.assigned_at is not None


def test_manual_override_bypasses_rules(db):
    """AC-12: admin manually assigns guide bypassing suitability."""
    guide = make_guide(db, is_active=False)  # wouldn't pass auto-assignment
    tour = make_tour(db)
    db.commit()

    manual_assign(tour, guide, db, assigned_by="admin@oceanarium.com")
    db.commit()

    assert tour.assigned_guide_id == guide.id
    assert tour.status == "assigned"


def test_manual_override_logged(db):
    guide = make_guide(db)
    tour = make_tour(db)
    db.commit()

    manual_assign(tour, guide, db, assigned_by="admin@oceanarium.com")
    db.commit()

    log = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
        TourAssignmentLog.action == "assigned",
    ).first()
    assert log is not None
    assert log.assignment_type == "manual"
    assert log.assigned_by == "admin@oceanarium.com"


def test_reassignment_releases_previous_guide(db):
    guide_a = make_guide(db, name="A", email="a@test.com")
    guide_b = make_guide(db, name="B", email="b@test.com")
    tour = make_tour(db, status="assigned", assigned_guide_id=guide_a.id)
    db.commit()

    manual_assign(tour, guide_b, db, assigned_by="admin@oceanarium.com")
    db.commit()

    assert tour.assigned_guide_id == guide_b.id

    logs = (
        db.query(TourAssignmentLog)
        .filter(TourAssignmentLog.tour_id == tour.id)
        .order_by(TourAssignmentLog.id)
        .all()
    )
    actions = [l.action for l in logs]
    assert "released" in actions
    assert "assigned" in actions

    released_log = [l for l in logs if l.action == "released"][0]
    assert released_log.guide_id == guide_a.id


# ── Edge-case / Robustness Tests ─────────────────────────────────────


def test_release_guide_clears_assignment_and_resets_status(db):
    guide = make_guide(db)
    tour = make_tour(db, status="assigned", assigned_guide_id=guide.id)
    db.commit()

    release_guide(tour, db)
    db.commit()

    assert tour.assigned_guide_id is None
    assert tour.status == "pending"

    log = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
        TourAssignmentLog.action == "released",
    ).first()
    assert log is not None
    assert log.guide_id == guide.id


def test_release_guide_keeps_cancelled_status(db):
    guide = make_guide(db)
    tour = make_tour(db, status="cancelled", assigned_guide_id=guide.id)
    db.commit()

    release_guide(tour, db)
    db.commit()

    assert tour.assigned_guide_id is None
    assert tour.status == "cancelled"


def test_release_guide_noop_when_no_guide_assigned(db):
    tour = make_tour(db, status="pending")
    db.commit()

    release_guide(tour, db)
    db.commit()

    assert tour.assigned_guide_id is None
    logs = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
    ).all()
    assert len(logs) == 0


def test_unassigned_log_has_no_guide_id(db):
    tour = make_tour(db)
    db.commit()

    assign_guide_to_tour(tour, db)
    db.commit()

    log = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
        TourAssignmentLog.action == "unassigned",
    ).first()
    assert log is not None
    assert log.guide_id is None
    assert log.assignment_type == "auto"


def test_reassign_same_guide_no_release_log(db):
    guide = make_guide(db)
    tour = make_tour(db, status="assigned", assigned_guide_id=guide.id)
    db.commit()

    manual_assign(tour, guide, db, assigned_by="admin@oceanarium.com")
    db.commit()

    assert tour.assigned_guide_id == guide.id

    logs = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
    ).all()
    released_logs = [l for l in logs if l.action == "released"]
    assert len(released_logs) == 0


def test_auto_assign_after_release(db):
    guide = make_guide(db, name="OnlyGuide")
    make_availability(db, guide, slots=[
        {"day_of_week": 0, "start_time": time(8, 0), "end_time": time(17, 0)},
    ])
    tour = make_tour(db, status="assigned", assigned_guide_id=guide.id)
    db.commit()

    release_guide(tour, db)
    db.commit()
    assert tour.assigned_guide_id is None
    assert tour.status == "pending"

    result = assign_guide_to_tour(tour, db)
    db.commit()

    assert result is not None
    assert result.id == guide.id
    assert tour.status == "assigned"


def test_manual_assign_to_pending_tour(db):
    guide = make_guide(db)
    tour = make_tour(db, status="pending")
    db.commit()

    manual_assign(tour, guide, db, assigned_by="admin@oceanarium.com")
    db.commit()

    assert tour.assigned_guide_id == guide.id
    assert tour.status == "assigned"
    log = db.query(TourAssignmentLog).filter(
        TourAssignmentLog.tour_id == tour.id,
        TourAssignmentLog.action == "assigned",
    ).first()
    assert log is not None
    assert log.assignment_type == "manual"


def test_manual_assign_to_unassigned_tour(db):
    tour = make_tour(db, status="unassigned")
    db.commit()

    guide = make_guide(db)
    manual_assign(tour, guide, db, assigned_by="admin@oceanarium.com")
    db.commit()

    assert tour.assigned_guide_id == guide.id
    assert tour.status == "assigned"
