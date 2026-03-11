from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_reservations_success(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.list_reservations.return_value = [
            {"id": 1, "customer_id": 10, "status": "CONFIRMED"},
        ]
        response = await client.get("/reservations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1


@pytest.mark.asyncio
async def test_get_reservations_handles_exception(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.list_reservations.side_effect = RuntimeError("DB down")
        response = await client.get("/reservations")

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_reservation_success(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.create_reservation.return_value = {"id": 42, "status": "CONFIRMED"}
        response = await client.post(
            "/reservations",
            json={
                "customer_id": 1,
                "schedule_id": 1,
                "adult_tickets": 2,
                "child_tickets": 1,
            },
        )

    assert response.status_code == 200
    assert response.json()["id"] == 42


@pytest.mark.asyncio
async def test_create_reservation_validation_error(client):
    from app.services.exceptions import ValidationError

    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.create_reservation.side_effect = ValidationError("Bad input")
        response = await client.post(
            "/reservations",
            json={
                "customer_id": 1,
                "schedule_id": 1,
                "adult_tickets": 0,
                "child_tickets": 0,
            },
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cancel_reservation_success(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.cancel_reservation.return_value = {"id": 1, "status": "CANCELLED"}
        response = await client.patch("/reservations/1/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_cancel_reservation_not_found(client):
    from app.services.exceptions import NotFoundError

    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.cancel_reservation.side_effect = NotFoundError("Not found")
        response = await client.patch("/reservations/999/cancel")

    assert response.status_code == 404
