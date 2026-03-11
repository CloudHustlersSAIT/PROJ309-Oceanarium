from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_create_issue_success(client):
    with patch("app.routes.issue.issue_service") as mock_svc:
        mock_svc.create_issue.return_value = {"id": 1, "description": "Broken pump"}
        response = await client.post("/issues", json={"description": "Broken pump"})

    assert response.status_code == 200
    assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_create_issue_internal_error(client):
    with patch("app.routes.issue.issue_service") as mock_svc:
        mock_svc.create_issue.side_effect = RuntimeError("fail")
        response = await client.post("/issues", json={"description": "test"})

    assert response.status_code == 500
