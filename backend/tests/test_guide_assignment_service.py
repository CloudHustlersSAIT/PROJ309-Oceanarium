from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.exceptions import NotFoundError, UnassignableError, ValidationError
from app.services.guide_assignment import (
    auto_assign_all_unassigned,
    auto_assign_and_notify,
    auto_assign_guide,
    find_eligible_guides,
    manual_assign_and_notify,
    manual_assign_guide,
)


def _schedule_row(
    schedule_id=1,
    guide_id=None,
    tour_id=10,
    language_code="en",
    start=None,
    end=None,
    status="UNASSIGNED",
):
    start = start or datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    end = end or datetime(2026, 3, 10, 11, 0, tzinfo=timezone.utc)
    mapping = {
        "id": schedule_id,
        "guide_id": guide_id,
        "tour_id": tour_id,
        "language_code": language_code,
        "event_start_datetime": start,
        "event_end_datetime": end,
        "status": status,
    }
    row = MagicMock()
    row._mapping = mapping
    return row


def _fetchall_ids(*ids):
    result = MagicMock()
    result.fetchall.return_value = [(i,) for i in ids]
    return result


def _ranked_fetchall(guides):
    """Build a mock result for the ranking query.

    Each item in *guides* is (id, first_name, last_name, rating, same_day).
    """
    result = MagicMock()
    result.fetchall.return_value = [tuple(g) for g in guides]
    return result


def _schedule_fetch_result(row=None):
    result = MagicMock()
    result.fetchone.return_value = row
    return result


# ── TestFindEligibleGuides ──────────────────────────────────────────


class TestFindEligibleGuides:
    def test_schedule_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None
        with pytest.raises(NotFoundError, match="Schedule not found"):
            find_eligible_guides(mock_conn, 999)

    def test_no_language_match(self, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(_schedule_row()),
            _fetchall_ids(),  # empty language result
        ]
        guides, reasons = find_eligible_guides(mock_conn, 1)
        assert guides == []
        assert "NO_LANGUAGE_MATCH" in reasons

    def test_no_expertise_match(self, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(_schedule_row()),
            _fetchall_ids(1, 2),  # language match
            _fetchall_ids(),  # empty expertise result
        ]
        guides, reasons = find_eligible_guides(mock_conn, 1)
        assert guides == []
        assert "NO_EXPERTISE_MATCH" in reasons

    def test_no_availability_match(self, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(_schedule_row()),
            _fetchall_ids(1, 2),  # language match
            _fetchall_ids(1, 2),  # expertise match
            _fetchall_ids(),  # empty availability result
        ]
        guides, reasons = find_eligible_guides(mock_conn, 1)
        assert guides == []
        assert "NO_AVAILABILITY_MATCH" in reasons

    def test_returns_ranked_guides(self, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(_schedule_row()),
            _fetchall_ids(1, 2, 3),  # language
            _fetchall_ids(1, 2, 3),  # expertise
            _fetchall_ids(1, 2, 3),  # availability
            _ranked_fetchall(
                [
                    (2, "Maria", "Silva", 4.9, 0),
                    (1, "John", "Doe", 4.5, 1),
                    (3, "Ana", "Costa", 4.5, 1),
                ]
            ),
        ]
        guides, reasons = find_eligible_guides(mock_conn, 1)
        assert reasons == []
        assert len(guides) == 3
        assert guides[0]["id"] == 2
        assert guides[0]["guide_rating"] == 4.9
        assert guides[0]["same_day_assignments"] == 0

    def test_priority_fewest_assignments_first(self, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(_schedule_row()),
            _fetchall_ids(1, 2),
            _fetchall_ids(1, 2),
            _fetchall_ids(1, 2),
            _ranked_fetchall(
                [
                    (2, "Maria", "Silva", 3.0, 0),
                    (1, "John", "Doe", 5.0, 2),
                ]
            ),
        ]
        guides, _ = find_eligible_guides(mock_conn, 1)
        assert guides[0]["id"] == 2

    def test_priority_highest_rating_tiebreaker(self, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(_schedule_row()),
            _fetchall_ids(1, 2),
            _fetchall_ids(1, 2),
            _fetchall_ids(1, 2),
            _ranked_fetchall(
                [
                    (2, "Maria", "Silva", 4.9, 1),
                    (1, "John", "Doe", 4.5, 1),
                ]
            ),
        ]
        guides, _ = find_eligible_guides(mock_conn, 1)
        assert guides[0]["id"] == 2
        assert guides[0]["guide_rating"] == 4.9

    def test_priority_lowest_id_final_tiebreaker(self, mock_conn):
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(_schedule_row()),
            _fetchall_ids(1, 2),
            _fetchall_ids(1, 2),
            _fetchall_ids(1, 2),
            _ranked_fetchall(
                [
                    (1, "John", "Doe", 4.5, 1),
                    (2, "Maria", "Silva", 4.5, 1),
                ]
            ),
        ]
        guides, _ = find_eligible_guides(mock_conn, 1)
        assert guides[0]["id"] == 1


# ── TestAutoAssignGuide ─────────────────────────────────────────────


class TestAutoAssignGuide:
    def test_happy_path_assigns_best_guide(self, mock_conn):
        schedule_row = _schedule_row(guide_id=None)
        mock_conn.execute.side_effect = [
            # auto_assign_guide → _fetch_schedule
            _schedule_fetch_result(schedule_row),
            # find_eligible_guides → _fetch_schedule
            _schedule_fetch_result(schedule_row),
            # language
            _fetchall_ids(1, 2),
            # expertise
            _fetchall_ids(1, 2),
            # availability
            _fetchall_ids(1, 2),
            # ranking
            _ranked_fetchall(
                [
                    (2, "Maria", "Silva", 4.9, 0),
                    (1, "John", "Doe", 4.5, 1),
                ]
            ),
            # UPDATE schedule
            MagicMock(),
            # INSERT log
            MagicMock(),
        ]

        result = auto_assign_guide(mock_conn, 1)

        assert result["guide_id"] == 2
        assert result["guide_name"] == "Maria Silva"
        assert result["assignment_type"] == "AUTO"
        assert result["constraints_met"]["language"] is True
        mock_conn.commit.assert_called_once()

    def test_unassignable_raises_and_updates_status(self, mock_conn):
        schedule_row = _schedule_row(guide_id=None)
        mock_conn.execute.side_effect = [
            # auto_assign_guide → _fetch_schedule
            _schedule_fetch_result(schedule_row),
            # find_eligible_guides → _fetch_schedule
            _schedule_fetch_result(schedule_row),
            # language → empty
            _fetchall_ids(),
            # UPDATE schedule to UNASSIGNABLE
            MagicMock(),
        ]

        with pytest.raises(UnassignableError) as exc_info:
            auto_assign_guide(mock_conn, 1)

        assert "NO_LANGUAGE_MATCH" in exc_info.value.reasons
        mock_conn.commit.assert_called_once()

    def test_reassignment_logs_as_reassigned(self, mock_conn):
        schedule_row = _schedule_row(guide_id=5)
        mock_conn.execute.side_effect = [
            _schedule_fetch_result(schedule_row),
            _schedule_fetch_result(schedule_row),
            _fetchall_ids(3),
            _fetchall_ids(3),
            _fetchall_ids(3),
            _ranked_fetchall([(3, "Ana", "Costa", 4.0, 0)]),
            MagicMock(),  # UPDATE
            MagicMock(),  # INSERT log
        ]

        result = auto_assign_guide(mock_conn, 1)

        assert result["guide_id"] == 3
        log_call = mock_conn.execute.call_args_list[-1]
        params = log_call[0][1] if len(log_call[0]) > 1 else log_call[1]
        assert params["action"] == "REASSIGNED"
        assert params["assignment_type"] == "AUTO"

    def test_schedule_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None
        with pytest.raises(NotFoundError, match="Schedule not found"):
            auto_assign_guide(mock_conn, 999)


# ── TestManualAssignGuide ───────────────────────────────────────────


class TestManualAssignGuide:
    def test_happy_path_assigns_guide(self, mock_conn):
        schedule_row = _schedule_row(guide_id=None)
        guide_row = MagicMock(id=3, first_name="Ana", last_name="Costa", is_active=True)
        lang_check = MagicMock()
        lang_check.fetchone.return_value = MagicMock()
        expertise_check = MagicMock()
        expertise_check.fetchone.return_value = MagicMock()
        avail_result = _fetchall_ids(3)

        mock_conn.execute.side_effect = [
            _schedule_fetch_result(schedule_row),  # _fetch_schedule
            MagicMock(fetchone=MagicMock(return_value=guide_row)),  # guide lookup
            lang_check,  # language warning check
            expertise_check,  # expertise warning check
            avail_result,  # availability warning check
            MagicMock(),  # UPDATE schedule
            MagicMock(),  # INSERT log
        ]

        result = manual_assign_guide(mock_conn, 1, 3, "admin")

        assert result["guide_id"] == 3
        assert result["guide_name"] == "Ana Costa"
        assert result["assignment_type"] == "MANUAL"
        assert result["warnings"] == []
        mock_conn.commit.assert_called_once()

    def test_returns_warnings_when_constraints_violated(self, mock_conn):
        schedule_row = _schedule_row(guide_id=None, language_code="pt")
        guide_row = MagicMock(id=3, first_name="Ana", last_name="Costa", is_active=True)
        lang_check = MagicMock()
        lang_check.fetchone.return_value = None  # no language match
        expertise_check = MagicMock()
        expertise_check.fetchone.return_value = None  # no expertise match
        avail_result = _fetchall_ids()  # not available

        mock_conn.execute.side_effect = [
            _schedule_fetch_result(schedule_row),
            MagicMock(fetchone=MagicMock(return_value=guide_row)),
            lang_check,
            expertise_check,
            avail_result,
            MagicMock(),  # UPDATE
            MagicMock(),  # INSERT
        ]

        result = manual_assign_guide(mock_conn, 1, 3, "admin")

        assert result["guide_id"] == 3
        assert len(result["warnings"]) == 3
        assert any("language" in w.lower() for w in result["warnings"])
        assert any("tour" in w.lower() for w in result["warnings"])
        assert any("available" in w.lower() for w in result["warnings"])
        mock_conn.commit.assert_called_once()

    def test_schedule_not_found_raises(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None
        with pytest.raises(NotFoundError, match="Schedule not found"):
            manual_assign_guide(mock_conn, 999, 3, "admin")

    def test_guide_not_found_raises(self, mock_conn):
        schedule_row = _schedule_row()
        guide_result = MagicMock()
        guide_result.fetchone.return_value = None

        mock_conn.execute.side_effect = [
            _schedule_fetch_result(schedule_row),
            guide_result,
        ]
        with pytest.raises(NotFoundError, match="Guide not found"):
            manual_assign_guide(mock_conn, 1, 999, "admin")

    def test_inactive_guide_raises(self, mock_conn):
        schedule_row = _schedule_row()
        guide_row = MagicMock(id=3, first_name="Ana", last_name="Costa", is_active=False)

        mock_conn.execute.side_effect = [
            _schedule_fetch_result(schedule_row),
            MagicMock(fetchone=MagicMock(return_value=guide_row)),
        ]
        with pytest.raises(ValidationError, match="inactive"):
            manual_assign_guide(mock_conn, 1, 3, "admin")

    def test_reassignment_logs_as_reassigned(self, mock_conn):
        schedule_row = _schedule_row(guide_id=5)
        guide_row = MagicMock(id=3, first_name="Ana", last_name="Costa", is_active=True)
        lang_check = MagicMock()
        lang_check.fetchone.return_value = MagicMock()
        expertise_check = MagicMock()
        expertise_check.fetchone.return_value = MagicMock()
        avail_result = _fetchall_ids(3)

        mock_conn.execute.side_effect = [
            _schedule_fetch_result(schedule_row),
            MagicMock(fetchone=MagicMock(return_value=guide_row)),
            lang_check,
            expertise_check,
            avail_result,
            MagicMock(),  # UPDATE
            MagicMock(),  # INSERT log
        ]

        manual_assign_guide(mock_conn, 1, 3, "admin")

        log_call = mock_conn.execute.call_args_list[-1]
        params = log_call[0][1] if len(log_call[0]) > 1 else log_call[1]
        assert params["action"] == "REASSIGNED"
        assert params["assignment_type"] == "MANUAL"

    def test_audit_log_created(self, mock_conn):
        schedule_row = _schedule_row(guide_id=None)
        guide_row = MagicMock(id=3, first_name="Ana", last_name="Costa", is_active=True)
        lang_check = MagicMock()
        lang_check.fetchone.return_value = MagicMock()
        expertise_check = MagicMock()
        expertise_check.fetchone.return_value = MagicMock()
        avail_result = _fetchall_ids(3)

        mock_conn.execute.side_effect = [
            _schedule_fetch_result(schedule_row),
            MagicMock(fetchone=MagicMock(return_value=guide_row)),
            lang_check,
            expertise_check,
            avail_result,
            MagicMock(),  # UPDATE
            MagicMock(),  # INSERT log
        ]

        manual_assign_guide(mock_conn, 1, 3, "admin_user")

        log_call = mock_conn.execute.call_args_list[-1]
        params = log_call[0][1] if len(log_call[0]) > 1 else log_call[1]
        assert params["schedule_id"] == 1
        assert params["guide_id"] == 3
        assert params["assigned_by"] == "admin_user"
        assert params["assignment_type"] == "MANUAL"
        assert params["action"] == "ASSIGNED"


# ===== Orchestration (and_notify) Tests =====


class TestAutoAssignAndNotify:
    def test_success_sends_notification(self):
        with (
            patch("app.services.guide_assignment.auto_assign_guide") as mock_assign,
            patch("app.services.guide_assignment.notification_service") as mock_notif,
        ):
            mock_assign.return_value = {"guide_id": 2, "guide_name": "Ana"}
            conn = MagicMock()

            result = auto_assign_and_notify(conn, 1)

        assert result["guide_id"] == 2
        mock_notif.notify_guide_assignment.assert_called_once_with(conn, 1, 2, "AUTO")

    def test_unassignable_sends_notification_and_reraises(self):
        with (
            patch("app.services.guide_assignment.auto_assign_guide") as mock_assign,
            patch("app.services.guide_assignment.notification_service") as mock_notif,
        ):
            mock_assign.side_effect = UnassignableError("no guide", reasons=["NO_LANGUAGE_MATCH"])
            conn = MagicMock()

            with pytest.raises(UnassignableError):
                auto_assign_and_notify(conn, 1)

        mock_notif.notify_schedule_unassignable.assert_called_once_with(conn, 1, ["NO_LANGUAGE_MATCH"])

    def test_notification_failure_does_not_break_flow(self):
        with (
            patch("app.services.guide_assignment.auto_assign_guide") as mock_assign,
            patch("app.services.guide_assignment.notification_service") as mock_notif,
        ):
            mock_assign.return_value = {"guide_id": 2, "guide_name": "Ana"}
            mock_notif.notify_guide_assignment.side_effect = RuntimeError("email down")
            conn = MagicMock()

            result = auto_assign_and_notify(conn, 1)

        assert result["guide_id"] == 2


class TestManualAssignAndNotify:
    def test_success_sends_notification(self):
        with (
            patch("app.services.guide_assignment.manual_assign_guide") as mock_assign,
            patch("app.services.guide_assignment.notification_service") as mock_notif,
        ):
            mock_assign.return_value = {"guide_id": 3, "warnings": []}
            conn = MagicMock()

            result = manual_assign_and_notify(conn, 1, 3, "admin")

        assert result["guide_id"] == 3
        mock_notif.notify_guide_assignment.assert_called_once_with(conn, 1, 3, "MANUAL")

    def test_notification_failure_does_not_break_flow(self):
        with (
            patch("app.services.guide_assignment.manual_assign_guide") as mock_assign,
            patch("app.services.guide_assignment.notification_service") as mock_notif,
        ):
            mock_assign.return_value = {"guide_id": 3, "warnings": []}
            mock_notif.notify_guide_assignment.side_effect = RuntimeError("email down")
            conn = MagicMock()

            result = manual_assign_and_notify(conn, 1, 3, "admin")

        assert result["guide_id"] == 3


class TestAutoAssignAllUnassigned:
    def test_mixed_results(self):
        with (
            patch("app.services.guide_assignment.auto_assign_guide") as mock_assign,
            patch("app.services.guide_assignment.notification_service"),
        ):
            mock_conn = MagicMock()
            mock_conn.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[(1,), (2,), (3,)]))
            mock_assign.side_effect = [
                {"guide_id": 10, "guide_name": "Marina Costa"},
                UnassignableError("No guide", reasons=["NO_LANGUAGE_MATCH"]),
                {"guide_id": 11, "guide_name": "Carlos Santos"},
            ]

            result = auto_assign_all_unassigned(mock_conn)

        assert result["total"] == 3
        assert result["assigned"] == 2
        assert result["unassignable"] == 1
        assert result["errors"] == 0

    def test_no_unassigned(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[]))

        result = auto_assign_all_unassigned(mock_conn)

        assert result["total"] == 0
        assert result["assigned"] == 0
        assert result["details"] == []

    def test_unexpected_error_counted(self):
        with (
            patch("app.services.guide_assignment.auto_assign_guide") as mock_assign,
            patch("app.services.guide_assignment.notification_service"),
        ):
            mock_conn = MagicMock()
            mock_conn.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[(1,)]))
            mock_assign.side_effect = RuntimeError("db gone")

            result = auto_assign_all_unassigned(mock_conn)

        assert result["total"] == 1
        assert result["errors"] == 1
        assert result["details"][0]["status"] == "error"
