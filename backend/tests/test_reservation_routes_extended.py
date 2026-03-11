from unittest.mock import patch

import pytest

from app.services.exceptions import ConflictError, NotFoundError


@pytest.mark.asyncio
async def test_reschedule_reservation_success(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.reschedule_reservation.return_value = {"id": 1, "schedule_id": 5}
        response = await client.patch("/reservations/1/reschedule", json={"new_schedule_id": 5})

    assert response.status_code == 200
    assert response.json()["schedule_id"] == 5


@pytest.mark.asyncio
async def test_reschedule_not_found(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.reschedule_reservation.side_effect = NotFoundError("Not found")
        response = await client.patch("/reservations/999/reschedule", json={"new_schedule_id": 5})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reschedule_conflict(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.reschedule_reservation.side_effect = ConflictError("Duplicate")
        response = await client.patch("/reservations/1/reschedule", json={"new_schedule_id": 5})

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reschedule_internal_error(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.reschedule_reservation.side_effect = RuntimeError("crash")
        response = await client.patch("/reservations/1/reschedule", json={"new_schedule_id": 5})

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_create_reservation_not_found(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.create_reservation.side_effect = NotFoundError("Customer not found")
        response = await client.post(
            "/reservations",
            json={
                "customer_id": 999,
                "schedule_id": 1,
                "adult_tickets": 1,
                "child_tickets": 0,
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_reservation_conflict(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.create_reservation.side_effect = ConflictError("Duplicate")
        response = await client.post(
            "/reservations",
            json={
                "customer_id": 1,
                "schedule_id": 1,
                "adult_tickets": 1,
                "child_tickets": 0,
            },
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_reservation_internal_error(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.create_reservation.side_effect = RuntimeError("crash")
        response = await client.post(
            "/reservations",
            json={
                "customer_id": 1,
                "schedule_id": 1,
                "adult_tickets": 1,
                "child_tickets": 0,
            },
        )

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_cancel_reservation_validation_error(client):
    from app.services.exceptions import ValidationError

    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.cancel_reservation.side_effect = ValidationError("Already cancelled")
        response = await client.patch("/reservations/1/cancel")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cancel_reservation_internal_error(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.cancel_reservation.side_effect = RuntimeError("crash")
        response = await client.patch("/reservations/1/cancel")

    assert response.status_code == 500


# Legacy aliases
@pytest.mark.asyncio
async def test_legacy_get_bookings(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.list_reservations.return_value = []
        response = await client.get("/bookings")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_legacy_create_booking(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.create_reservation.return_value = {"id": 1}
        response = await client.post(
            "/bookings",
            json={
                "customer_id": 1,
                "schedule_id": 1,
                "adult_tickets": 1,
                "child_tickets": 0,
            },
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_legacy_reschedule_booking(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.reschedule_reservation.return_value = {"id": 1}
        response = await client.patch("/bookings/1/reschedule", json={"new_schedule_id": 5})

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_legacy_cancel_booking(client):
    with patch("app.routes.reservation.reservation_service") as mock_svc:
        mock_svc.cancel_reservation.return_value = {"id": 1, "status": "CANCELLED"}
        response = await client.patch("/bookings/1/cancel")

    assert response.status_code == 200
