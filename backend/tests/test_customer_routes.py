from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_customers_success(client):
    with patch("app.routes.customer.customer_service") as mock_svc:
        mock_svc.list_customers.return_value = [
            {"clorian_client_id": "MANUAL-000001", "full_name": "Ana Costa", "email": "ana@test.com"}
        ]
        response = await client.get("/customers")

    assert response.status_code == 200
    assert response.json()[0]["clorian_client_id"] == "MANUAL-000001"


@pytest.mark.asyncio
async def test_get_customers_internal_error(client):
    with patch("app.routes.customer.customer_service") as mock_svc:
        mock_svc.list_customers.side_effect = RuntimeError("DB down")
        response = await client.get("/customers")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_create_customer_success(client):
    with patch("app.routes.customer.customer_service") as mock_svc:
        mock_svc.create_customer.return_value = {
            "clorian_client_id": "MANUAL-000010",
            "first_name": "Ana",
            "last_name": "Costa",
            "email": "ana@test.com",
        }

        response = await client.post(
            "/customers",
            json={"first_name": "Ana", "last_name": "Costa", "email": "ana@test.com"},
        )

    assert response.status_code == 200
    assert response.json()["clorian_client_id"] == "MANUAL-000010"


@pytest.mark.asyncio
async def test_create_customer_validation_error(client):
    from app.services.exceptions import ValidationError

    with patch("app.routes.customer.customer_service") as mock_svc:
        mock_svc.create_customer.side_effect = ValidationError("email is required")

        response = await client.post(
            "/customers",
            json={"first_name": "Ana", "last_name": "Costa", "email": ""},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_patch_customer_success(client):
    with patch("app.routes.customer.customer_service") as mock_svc:
        mock_svc.update_customer.return_value = {
            "clorian_client_id": "MANUAL-000001",
            "first_name": "Ana Maria",
            "last_name": "Costa",
            "email": "ana@test.com",
        }

        response = await client.patch("/customers/MANUAL-000001", json={"first_name": "Ana Maria"})

    assert response.status_code == 200
    assert response.json()["first_name"] == "Ana Maria"


@pytest.mark.asyncio
async def test_patch_customer_not_found(client):
    with patch("app.routes.customer.customer_service") as mock_svc:
        mock_svc.update_customer.return_value = None

        response = await client.patch("/customers/MANUAL-999999", json={"first_name": "Ana"})

    assert response.status_code == 404
