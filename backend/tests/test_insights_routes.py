from unittest.mock import patch

import pytest
from openai import APIError, RateLimitError


class TestInsightsRoutes:
    @pytest.mark.asyncio
    async def test_query_insights_success(self, client):
        """Should return insights successfully"""
        mock_result = {
            "question": "How many guides?",
            "answer": "There are 10 active guides",
            "chart": {"type": "number", "title": "Active Guides", "data": [{"label": "Guides", "value": 10}]},
            "recommendations": [
                {"title": "Hire more guides", "description": "Consider hiring 2 more guides", "action_type": "hire"}
            ],
            "sql_used": "SELECT COUNT(*) FROM guides WHERE is_active = true",
        }

        with (
            patch("app.routes.insights.run_insight_query", return_value=mock_result),
            patch("app.routes.insights.assert_text_is_safe"),
        ):
            response = await client.post("/insights/query", json={"question": "How many guides?"})

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "How many guides?"
        assert data["answer"] == "There are 10 active guides"
        assert data["chart"]["type"] == "number"
        assert len(data["recommendations"]) == 1

    @pytest.mark.asyncio
    async def test_query_insights_empty_question(self, client):
        """Should reject empty question"""
        response = await client.post("/insights/query", json={"question": ""})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_query_insights_whitespace_only_question(self, client):
        """Should reject whitespace-only question"""
        with patch("app.routes.insights.assert_text_is_safe"):
            response = await client.post("/insights/query", json={"question": "   "})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "EMPTY_QUESTION"

    @pytest.mark.asyncio
    async def test_query_insights_question_too_long(self, client):
        """Should reject question exceeding 500 characters"""
        long_question = "a" * 501

        response = await client.post("/insights/query", json={"question": long_question})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_insights_missing_question(self, client):
        """Should reject request without question field"""
        response = await client.post("/insights/query", json={})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_insights_content_moderation_blocked(self, client):
        """Should block unsafe content"""
        from app.services.exceptions import ValidationError

        with patch("app.routes.insights.assert_text_is_safe") as mock_safety:
            mock_safety.side_effect = ValidationError("Content contains prohibited language")
            response = await client.post("/insights/query", json={"question": "bad content here"})

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "CONTENT_SAFETY_BLOCKED"

    @pytest.mark.asyncio
    async def test_query_insights_unsafe_sql(self, client):
        """Should reject unsafe SQL from LLM"""
        from app.services.exceptions import ValidationError

        with (
            patch("app.routes.insights.assert_text_is_safe"),
            patch("app.routes.insights.run_insight_query") as mock_run,
        ):
            mock_run.side_effect = ValidationError("Generated query contains disallowed keywords")
            response = await client.post("/insights/query", json={"question": "Show me customers"})

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["code"] == "UNSAFE_SQL"

    @pytest.mark.asyncio
    async def test_query_insights_openai_error(self, client):
        """Should handle OpenAI service errors"""
        from unittest.mock import MagicMock

        mock_request = MagicMock()
        mock_request.headers = {}

        with (
            patch("app.routes.insights.assert_text_is_safe"),
            patch("app.routes.insights.run_insight_query") as mock_run,
        ):
            mock_run.side_effect = APIError("Service unavailable", request=mock_request, body=None)
            response = await client.post("/insights/query", json={"question": "How many guides?"})

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["code"] == "OPENAI_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_query_insights_rate_limit_error(self, client):
        """Should handle OpenAI rate limit errors"""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 429

        with (
            patch("app.routes.insights.assert_text_is_safe"),
            patch("app.routes.insights.run_insight_query") as mock_run,
        ):
            mock_run.side_effect = RateLimitError("Rate limit exceeded", response=mock_response, body=None)
            response = await client.post("/insights/query", json={"question": "How many guides?"})

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["code"] == "OPENAI_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_query_insights_database_error(self, client):
        """Should handle database errors"""

        def raise_db_error(*args):
            raise RuntimeError("Table does not exist")

        with (
            patch("app.routes.insights.assert_text_is_safe"),
            patch("app.routes.insights.run_insight_query", side_effect=raise_db_error),
        ):
            response = await client.post("/insights/query", json={"question": "How many guides?"})

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["code"] == "DB_ERROR"

    @pytest.mark.asyncio
    async def test_query_insights_with_chart_data(self, client):
        """Should return chart data in response"""
        mock_result = {
            "question": "Top guides by rating",
            "answer": "Top 3 guides listed",
            "chart": {
                "type": "bar",
                "title": "Top Guides",
                "data": [
                    {"label": "Maria Silva", "value": 4.9},
                    {"label": "João Costa", "value": 4.7},
                    {"label": "Ana Santos", "value": 4.5},
                ],
            },
            "recommendations": [],
            "sql_used": "SELECT first_name, guide_rating FROM guides ORDER BY guide_rating DESC LIMIT 3",
        }

        with (
            patch("app.routes.insights.run_insight_query", return_value=mock_result),
            patch("app.routes.insights.assert_text_is_safe"),
        ):
            response = await client.post("/insights/query", json={"question": "Top guides by rating"})

        assert response.status_code == 200
        data = response.json()
        assert data["chart"]["type"] == "bar"
        assert len(data["chart"]["data"]) == 3

    @pytest.mark.asyncio
    async def test_query_insights_with_recommendations(self, client):
        """Should return recommendations in response"""
        mock_result = {
            "question": "Unassigned schedules",
            "answer": "5 schedules need guides",
            "chart": {"type": "number", "title": "Unassigned", "data": [{"label": "Count", "value": 5}]},
            "recommendations": [
                {
                    "title": "Assign Maria Silva",
                    "description": "Maria is qualified for 3 schedules",
                    "action_type": "assign",
                },
                {
                    "title": "Train João Costa",
                    "description": "João needs Snorkeling expertise",
                    "action_type": "train",
                },
                {
                    "title": "Hire Portuguese speaker",
                    "description": "No guides available for PT tours",
                    "action_type": "hire",
                },
            ],
            "sql_used": "SELECT * FROM schedule WHERE guide_id IS NULL",
        }

        with (
            patch("app.routes.insights.run_insight_query", return_value=mock_result),
            patch("app.routes.insights.assert_text_is_safe"),
        ):
            response = await client.post("/insights/query", json={"question": "Unassigned schedules"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 3
        assert data["recommendations"][0]["action_type"] == "assign"
        assert data["recommendations"][1]["action_type"] == "train"
        assert data["recommendations"][2]["action_type"] == "hire"

    @pytest.mark.asyncio
    async def test_query_insights_no_chart(self, client):
        """Should handle response with no chart data"""
        mock_result = {
            "question": "Test question",
            "answer": "Test answer",
            "chart": None,
            "recommendations": [],
            "sql_used": "SELECT 1",
        }

        with (
            patch("app.routes.insights.run_insight_query", return_value=mock_result),
            patch("app.routes.insights.assert_text_is_safe"),
        ):
            response = await client.post("/insights/query", json={"question": "Test question"})

        assert response.status_code == 200
        data = response.json()
        assert data["chart"] is None

    @pytest.mark.asyncio
    async def test_query_insights_requires_authentication(self, client):
        """Should require user to be authenticated"""
        with patch.dict("os.environ", {"AUTH_BYPASS": "false"}):
            response = await client.post("/insights/query", json={"question": "Test"})

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_query_insights_trims_question(self, client):
        """Should trim whitespace from question"""
        mock_result = {
            "question": "How many guides?",
            "answer": "10 guides",
            "chart": {"type": "number", "title": "Guides", "data": [{"label": "Count", "value": 10}]},
            "recommendations": [],
            "sql_used": "SELECT COUNT(*) FROM guides",
        }

        with (
            patch("app.routes.insights.run_insight_query", return_value=mock_result) as mock_run,
            patch("app.routes.insights.assert_text_is_safe"),
        ):
            response = await client.post("/insights/query", json={"question": "  How many guides?  "})

        assert response.status_code == 200
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][1] == "How many guides?"

    @pytest.mark.asyncio
    async def test_query_insights_returns_sql_used(self, client):
        """Should return the SQL query used"""
        mock_result = {
            "question": "Test",
            "answer": "Answer",
            "chart": None,
            "recommendations": [],
            "sql_used": "SELECT * FROM guides WHERE is_active = true LIMIT 100",
        }

        with (
            patch("app.routes.insights.run_insight_query", return_value=mock_result),
            patch("app.routes.insights.assert_text_is_safe"),
        ):
            response = await client.post("/insights/query", json={"question": "Test"})

        assert response.status_code == 200
        data = response.json()
        assert "sql_used" in data
        assert data["sql_used"] == "SELECT * FROM guides WHERE is_active = true LIMIT 100"

    @pytest.mark.asyncio
    async def test_query_insights_all_chart_types(self, client):
        """Should handle all chart types"""
        chart_types = ["number", "bar", "line", "donut", "list", "comparison"]

        for chart_type in chart_types:
            mock_result = {
                "question": f"Test {chart_type}",
                "answer": "Answer",
                "chart": {
                    "type": chart_type,
                    "title": f"{chart_type.title()} Chart",
                    "data": [{"label": "Test", "value": 10}],
                },
                "recommendations": [],
                "sql_used": "SELECT 1",
            }

            with (
                patch("app.routes.insights.run_insight_query", return_value=mock_result),
                patch("app.routes.insights.assert_text_is_safe"),
            ):
                response = await client.post("/insights/query", json={"question": f"Test {chart_type}"})

            assert response.status_code == 200
            data = response.json()
            assert data["chart"]["type"] == chart_type
