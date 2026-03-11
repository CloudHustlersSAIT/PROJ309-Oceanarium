from unittest.mock import patch

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
