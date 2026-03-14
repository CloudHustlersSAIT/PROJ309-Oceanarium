from unittest.mock import MagicMock, patch

import pytest

from app.services.exceptions import NotFoundError, UnassignableError, ValidationError


@pytest.mark.asyncio
async def test_auto_assign_success(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.auto_assign_guide.return_value = {
            "schedule_id": 1,
            "guide_id": 2,
            "guide_name": "Maria Silva",
            "assignment_type": "AUTO",
            "constraints_met": {
                "language": True,
                "availability": True,
                "expertise": True,
            },
        }
        response = await client.post("/schedules/1/assign")

    assert response.status_code == 200
    data = response.json()
    assert data["guide_id"] == 2
    assert data["guide_name"] == "Maria Silva"
    assert data["assignment_type"] == "AUTO"


@pytest.mark.asyncio
async def test_auto_assign_schedule_not_found(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.auto_assign_guide.side_effect = NotFoundError("Schedule not found")
        response = await client.post("/schedules/999/assign")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_auto_assign_unassignable(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.auto_assign_guide.side_effect = UnassignableError(
            "No eligible guide found for this schedule",
            reasons=["NO_LANGUAGE_MATCH"],
        )
        response = await client.post("/schedules/1/assign")

    assert response.status_code == 422
    data = response.json()
    assert "NO_LANGUAGE_MATCH" in data["detail"]["reasons"]


@pytest.mark.asyncio
async def test_auto_assign_internal_error(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.auto_assign_guide.side_effect = RuntimeError("unexpected")
        response = await client.post("/schedules/1/assign")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_manual_assign_success(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.manual_assign_guide.return_value = {
            "schedule_id": 1,
            "guide_id": 3,
            "guide_name": "Ana Costa",
            "assignment_type": "MANUAL",
            "warnings": [],
        }
        response = await client.put(
            "/schedules/1/assign",
            json={"guide_id": 3},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["guide_id"] == 3
    assert data["warnings"] == []


@pytest.mark.asyncio
async def test_manual_assign_with_warnings(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.manual_assign_guide.return_value = {
            "schedule_id": 1,
            "guide_id": 7,
            "guide_name": "John Doe",
            "assignment_type": "MANUAL",
            "warnings": ["Guide does not speak requested language: pt"],
        }
        response = await client.put(
            "/schedules/1/assign",
            json={"guide_id": 7, "reason": "Customer requested specific guide"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["warnings"]) == 1
    assert "language" in data["warnings"][0].lower()


@pytest.mark.asyncio
async def test_manual_assign_schedule_not_found(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.manual_assign_guide.side_effect = NotFoundError("Schedule not found")
        response = await client.put(
            "/schedules/999/assign",
            json={"guide_id": 3},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_manual_assign_guide_not_found(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.manual_assign_guide.side_effect = NotFoundError("Guide not found")
        response = await client.put(
            "/schedules/1/assign",
            json={"guide_id": 999},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_manual_assign_inactive_guide(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.manual_assign_guide.side_effect = ValidationError("Guide is inactive")
        response = await client.put(
            "/schedules/1/assign",
            json={"guide_id": 3},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_manual_assign_missing_guide_id(client):
    response = await client.put(
        "/schedules/1/assign",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_eligible_guides_success(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.find_eligible_guides.return_value = (
            [
                {
                    "id": 3,
                    "first_name": "Maria",
                    "last_name": "Silva",
                    "guide_rating": 4.8,
                    "same_day_assignments": 1,
                },
                {
                    "id": 7,
                    "first_name": "John",
                    "last_name": "Doe",
                    "guide_rating": 4.5,
                    "same_day_assignments": 2,
                },
            ],
            [],
        )
        response = await client.get("/schedules/1/eligible-guides")

    assert response.status_code == 200
    data = response.json()
    assert data["schedule_id"] == 1
    assert data["total"] == 2
    assert data["reasons"] == []

    first = data["eligible_guides"][0]
    assert first["id"] == 3
    assert first["first_name"] == "Maria"
    assert first["last_name"] == "Silva"
    assert first["guide_rating"] == 4.8
    assert first["same_day_assignments"] == 1
    assert first["ranking_position"] == 1

    second = data["eligible_guides"][1]
    assert second["id"] == 7
    assert second["ranking_position"] == 2


@pytest.mark.asyncio
async def test_get_eligible_guides_empty(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.find_eligible_guides.return_value = ([], ["NO_LANGUAGE_MATCH"])
        response = await client.get("/schedules/1/eligible-guides")

    assert response.status_code == 200
    data = response.json()
    assert data["eligible_guides"] == []
    assert "NO_LANGUAGE_MATCH" in data["reasons"]
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_eligible_guides_schedule_not_found(client):
    with patch("app.routes.schedule.guide_assignment_service") as mock_svc:
        mock_svc.find_eligible_guides.side_effect = NotFoundError("Schedule not found")
        response = await client.get("/schedules/999/eligible-guides")

    assert response.status_code == 404


# ===== Auto-Assign All Tests =====


@pytest.mark.asyncio
async def test_auto_assign_all_mixed_results(client):
    """Test POST /schedules/auto-assign-all with a mix of assigned and unassignable."""
    from app.db import get_db
    from app.main import app

    mock_conn = MagicMock()
    mock_conn.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[(1,), (2,), (3,)]))

    def override_db():
        yield mock_conn

    app.dependency_overrides[get_db] = override_db

    try:
        with (
            patch("app.routes.schedule.guide_assignment_service") as mock_assign,
            patch("app.routes.schedule.notification_service") as mock_notif,
        ):
            mock_assign.auto_assign_guide.side_effect = [
                {"guide_id": 10, "guide_name": "Marina Costa"},
                UnassignableError("No eligible guide", reasons=["NO_LANGUAGE_MATCH"]),
                {"guide_id": 11, "guide_name": "Carlos Santos"},
            ]

            response = await client.post("/schedules/auto-assign-all")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["assigned"] == 2
        assert data["unassignable"] == 1
        assert data["errors"] == 0
        assert len(data["details"]) == 3

        assert mock_notif.notify_guide_assignment.call_count == 2
        assert mock_notif.notify_schedule_unassignable.call_count == 1
    finally:
        from tests.conftest import _mock_get_db

        app.dependency_overrides[get_db] = _mock_get_db


@pytest.mark.asyncio
async def test_auto_assign_all_no_unassigned(client):
    """Test POST /schedules/auto-assign-all when no schedules need assignment."""
    from app.db import get_db
    from app.main import app

    mock_conn = MagicMock()
    mock_conn.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[]))

    def override_db():
        yield mock_conn

    app.dependency_overrides[get_db] = override_db

    try:
        response = await client.post("/schedules/auto-assign-all")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["assigned"] == 0
        assert data["unassignable"] == 0
        assert data["details"] == []
    finally:
        from tests.conftest import _mock_get_db

        app.dependency_overrides[get_db] = _mock_get_db
