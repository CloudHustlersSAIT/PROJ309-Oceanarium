from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_guides_success(client):
    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.list_guides.return_value = [
            {"id": 1, "first_name": "Maria", "last_name": "Silva"},
            {"id": 2, "first_name": "João", "last_name": "Costa"},
        ]
        response = await client.get("/guides")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["first_name"] == "Maria"


@pytest.mark.asyncio
async def test_get_guides_internal_error(client):
    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.list_guides.side_effect = RuntimeError("DB error")
        response = await client.get("/guides")

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_guide_success(client):
    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.create_guide.return_value = {
            "id": 1,
            "first_name": "Maria",
            "last_name": "Silva",
            "email": "maria@test.com",
        }
        response = await client.post(
            "/guides",
            json={"first_name": "Maria", "last_name": "Silva", "email": "maria@test.com"},
        )

    assert response.status_code == 200
    assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_create_guide_validation_error(client):
    from app.services.exceptions import ValidationError

    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.create_guide.side_effect = ValidationError("email is required")
        response = await client.post(
            "/guides",
            json={"first_name": "Maria", "last_name": "Silva", "email": ""},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_patch_guide_success(client):
    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.update_guide.return_value = {
            "id": 1,
            "first_name": "Mariah",
            "last_name": "Silva",
            "email": "maria@test.com",
        }
        response = await client.patch("/guides/1", json={"first_name": "Mariah"})

    assert response.status_code == 200
    assert response.json()["first_name"] == "Mariah"


@pytest.mark.asyncio
async def test_patch_guide_not_found(client):
    with patch("app.routes.guide.guide_service") as mock_svc:
        mock_svc.update_guide.return_value = None
        response = await client.patch("/guides/999", json={"first_name": "Maria"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_swap_accept_success(client):
    with (
        patch("app.routes.guide_requests.engine.connect") as mock_connect,
        patch("app.routes.guide_requests.request_service") as mock_svc,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_svc.accept_swap_request.return_value = {
            "status": "accepted",
            "schedule_id": 10,
            "guide_id": 3,
        }

        response = await client.post("/guide/swap-accept", params={"swap_request_id": 123, "guide_id": 3})

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "accepted"


@pytest.mark.asyncio
async def test_swap_reject_success(client):
    with (
        patch("app.routes.guide_requests.engine.connect") as mock_connect,
        patch("app.routes.guide_requests.request_service") as mock_svc,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_svc.reject_swap_request.return_value = {
            "status": "rejected",
            "schedule_id": 10,
            "guide_id": 3,
        }

        response = await client.post("/guide/swap-reject", params={"swap_request_id": 123, "guide_id": 3})

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "rejected"


@pytest.mark.asyncio
async def test_swap_accept_not_found(client):
    with (
        patch("app.routes.guide_requests.engine.connect") as mock_connect,
        patch("app.routes.guide_requests.request_service") as mock_svc,
    ):
        mock_connect.return_value.__enter__.return_value = MagicMock()
        mock_svc.accept_swap_request.return_value = {"status": "not_found"}

        response = await client.post("/guide/swap-accept", params={"swap_request_id": 999999, "guide_id": 1})

    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "not_found"}
