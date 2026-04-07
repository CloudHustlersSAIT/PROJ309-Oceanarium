import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.exceptions import ValidationError
from app.services.insights import (
    _enrich_unassigned_schedules,
    _guard_sql,
    run_insight_query,
)


class TestGuardSQL:
    def test_guard_sql_allows_select(self):
        """Should allow SELECT queries"""
        _guard_sql("SELECT * FROM customers")
        _guard_sql("select id from guides where is_active = true")

    def test_guard_sql_allows_with(self):
        """Should allow WITH queries (CTEs)"""
        _guard_sql("WITH cte AS (SELECT 1) SELECT * FROM cte")

    def test_guard_sql_blocks_non_select(self):
        """Should block non-SELECT statements"""
        with pytest.raises(ValidationError, match="not a SELECT statement"):
            _guard_sql("DELETE FROM customers")

        with pytest.raises(ValidationError, match="not a SELECT statement"):
            _guard_sql("UPDATE guides SET is_active = false")

    def test_guard_sql_blocks_dangerous_keywords(self):
        """Should block dangerous SQL keywords"""
        dangerous = [
            "INSERT INTO customers VALUES (1)",
            "DROP TABLE guides",
            "CREATE TABLE test (id INT)",
            "ALTER TABLE guides ADD COLUMN test VARCHAR",
            "TRUNCATE TABLE customers",
            "GRANT ALL ON guides TO user",
            "EXEC sp_test",
        ]

        for sql in dangerous:
            with pytest.raises(ValidationError):
                _guard_sql(sql)

    def test_guard_sql_blocks_dangerous_keywords_in_select(self):
        """Should block dangerous keywords even in SELECT queries"""
        with pytest.raises(ValidationError, match="disallowed keywords"):
            _guard_sql("SELECT * FROM customers; DROP TABLE guides")

    def test_guard_sql_case_insensitive(self):
        """Should detect blocked keywords regardless of case"""
        with pytest.raises(ValidationError, match="disallowed keywords"):
            _guard_sql("select * from guides; DeLeTe FROM customers")


class TestEnrichUnassignedSchedules:
    def test_no_enrichment_for_non_unassigned_question(self, mock_conn):
        """Should skip enrichment if question is not about unassigned schedules"""
        rows = [{"id": 1}]
        question = "How many guides do we have?"

        result = _enrich_unassigned_schedules(mock_conn, rows, question)

        assert result == {}

    def test_no_enrichment_when_no_schedule_ids(self, mock_conn):
        """Should skip enrichment if no schedule IDs found in results"""
        rows = [{"count": 5}]
        question = "How many unassigned schedules?"

        result = _enrich_unassigned_schedules(mock_conn, rows, question)

        assert result == {}

    @patch("app.services.insights.guide_assignment.find_eligible_guides")
    def test_enrichment_with_eligible_guides(self, mock_find_eligible, mock_conn):
        """Should enrich unassigned schedules with eligible guide data"""
        rows = [{"id": 10}, {"id": 20}]
        question = "Show me unassigned schedules"

        mock_find_eligible.side_effect = [
            (
                [
                    {"id": 1, "first_name": "Maria", "last_name": "Silva", "guide_rating": 4.5},
                    {"id": 2, "first_name": "João", "last_name": "Costa", "guide_rating": 4.8},
                ],
                [],
            ),
            ([], ["NO_EXPERTISE_MATCH"]),
        ]

        result = _enrich_unassigned_schedules(mock_conn, rows, question)

        assert "schedules" in result
        assert len(result["schedules"]) == 2
        assert result["schedules"][0]["schedule_id"] == 10
        assert result["schedules"][0]["eligible_count"] == 2
        assert result["schedules"][0]["eligible_guides"][0]["name"] == "Maria Silva"
        assert result["schedules"][1]["schedule_id"] == 20
        assert result["schedules"][1]["eligible_count"] == 0
        assert "1 schedules have eligible guides" in result["enrichment_summary"]
        assert "1 blocked by missing expertise" in result["enrichment_summary"]

    @patch("app.services.insights.guide_assignment.find_eligible_guides")
    def test_enrichment_handles_exceptions(self, mock_find_eligible, mock_conn):
        """Should handle exceptions during eligibility checks"""
        rows = [{"id": 10}]
        question = "Show unassigned schedules"

        mock_find_eligible.side_effect = RuntimeError("DB error")

        result = _enrich_unassigned_schedules(mock_conn, rows, question)

        assert "schedules" in result
        assert len(result["schedules"]) == 0

    @patch("app.services.insights.guide_assignment.find_eligible_guides")
    def test_enrichment_limits_to_10_schedules(self, mock_find_eligible, mock_conn):
        """Should only enrich up to 10 schedules"""
        rows = [{"id": i} for i in range(1, 20)]
        question = "Show all unassigned schedules"

        mock_find_eligible.return_value = ([], [])

        result = _enrich_unassigned_schedules(mock_conn, rows, question)

        assert len(result["schedules"]) == 10
        assert mock_find_eligible.call_count == 10

    @patch("app.services.insights.guide_assignment.find_eligible_guides")
    def test_enrichment_limits_guides_to_3(self, mock_find_eligible, mock_conn):
        """Should only include top 3 eligible guides per schedule"""
        rows = [{"id": 10}]
        question = "unassigned schedules"

        eligible = [{"id": i, "first_name": f"Guide{i}", "last_name": "Test", "guide_rating": 5.0} for i in range(1, 6)]
        mock_find_eligible.return_value = (eligible, [])

        result = _enrich_unassigned_schedules(mock_conn, rows, question)

        assert len(result["schedules"][0]["eligible_guides"]) == 3

    @patch("app.services.insights.guide_assignment.find_eligible_guides")
    def test_enrichment_tracks_blocking_reasons(self, mock_find_eligible, mock_conn):
        """Should track and summarize all blocking reasons"""
        rows = [{"id": i} for i in range(1, 5)]
        question = "unassigned schedules"

        mock_find_eligible.side_effect = [
            ([], ["NO_EXPERTISE_MATCH"]),
            ([], ["NO_LANGUAGE_MATCH"]),
            ([], ["NO_AVAILABILITY_MATCH"]),
            ([{"id": 1, "first_name": "Test", "last_name": "Guide", "guide_rating": 5.0}], []),
        ]

        result = _enrich_unassigned_schedules(mock_conn, rows, question)

        summary = result["enrichment_summary"]
        assert "1 schedules have eligible guides" in summary
        assert "1 blocked by missing expertise" in summary
        assert "1 blocked by language mismatch" in summary
        assert "1 blocked by guide availability conflicts" in summary

    def test_enrichment_uses_schedule_id_column(self, mock_conn):
        """Should work with schedule_id column name instead of id"""
        rows = [{"schedule_id": 100}]
        question = "unassigned schedules"

        with patch("app.services.insights.guide_assignment.find_eligible_guides") as mock_find:
            mock_find.return_value = ([], [])
            result = _enrich_unassigned_schedules(mock_conn, rows, question)

            assert result["schedules"][0]["schedule_id"] == 100


class TestRunInsightQuery:
    @patch("app.services.insights.OpenAI")
    def test_missing_openai_key(self, mock_openai_class, mock_conn):
        """Should raise error if OPENAI_API_KEY not configured"""
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": ""}),
            pytest.raises(RuntimeError, match="OPENAI_API_KEY is not configured"),
        ):
            run_insight_query(mock_conn, "test question")

    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_phase1_invalid_json(self, mock_openai_class, mock_conn):
        """Should raise error if Phase 1 returns invalid JSON"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "not valid json"
        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(RuntimeError, match="Phase 1 returned invalid JSON"):
            run_insight_query(mock_conn, "test question")

    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_phase1_missing_sql(self, mock_openai_class, mock_conn):
        """Should raise error if Phase 1 returns no SQL"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"other": "field"}'
        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(ValidationError, match="did not return a SQL query"):
            run_insight_query(mock_conn, "test question")

    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_phase1_unsafe_sql(self, mock_openai_class, mock_conn):
        """Should raise error if Phase 1 returns unsafe SQL"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"sql": "DELETE FROM customers"}'
        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(ValidationError, match="not a SELECT statement"):
            run_insight_query(mock_conn, "test question")

    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_database_query_error(self, mock_openai_class, mock_conn):
        """Should raise error if database query fails"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"sql": "SELECT * FROM nonexistent"}'
        mock_client.chat.completions.create.return_value = mock_response

        mock_conn.execute.side_effect = RuntimeError("Table does not exist")

        with pytest.raises(RuntimeError, match="Database query failed"):
            run_insight_query(mock_conn, "test question")

    @patch("app.services.insights._enrich_unassigned_schedules")
    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_successful_query_without_enrichment(self, mock_openai_class, mock_enrich, mock_conn):
        """Should successfully execute query and return results"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        phase1_response = MagicMock()
        phase1_response.choices[0].message.content = '{"sql": "SELECT COUNT(*) as count FROM guides"}'

        phase2_response = MagicMock()
        phase2_response.choices[0].message.content = json.dumps(
            {
                "answer": "There are 10 guides",
                "chart": {"type": "number", "title": "Total Guides", "data": [{"label": "Guides", "value": 10}]},
                "recommendations": [{"title": "Hire more", "description": "Consider hiring", "action_type": "hire"}],
            }
        )

        mock_client.chat.completions.create.side_effect = [phase1_response, phase2_response]

        mock_result = MagicMock()
        mock_result.keys.return_value = ["count"]
        mock_result.fetchmany.return_value = [(10,)]
        mock_conn.execute.return_value = mock_result

        mock_enrich.return_value = {}

        result = run_insight_query(mock_conn, "How many guides?")

        assert result["question"] == "How many guides?"
        assert result["answer"] == "There are 10 guides"
        assert result["chart"]["type"] == "number"
        assert len(result["recommendations"]) == 1
        assert result["sql_used"] == "SELECT COUNT(*) as count FROM guides"

    @patch("app.services.insights._enrich_unassigned_schedules")
    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_successful_query_with_enrichment(self, mock_openai_class, mock_enrich, mock_conn):
        """Should include enrichment context in Phase 2 prompt"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        phase1_response = MagicMock()
        phase1_response.choices[0].message.content = '{"sql": "SELECT * FROM schedule WHERE guide_id IS NULL"}'

        phase2_response = MagicMock()
        phase2_response.choices[0].message.content = json.dumps(
            {
                "answer": "5 schedules are unassigned",
                "chart": {"type": "number", "title": "Unassigned", "data": [{"label": "Count", "value": 5}]},
                "recommendations": [],
            }
        )

        mock_client.chat.completions.create.side_effect = [phase1_response, phase2_response]

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id"]
        mock_result.fetchmany.return_value = [(10,), (20,)]
        mock_conn.execute.return_value = mock_result

        mock_enrich.return_value = {
            "schedules": [{"schedule_id": 10, "eligible_count": 2}],
            "enrichment_summary": "1 schedules have eligible guides",
        }

        result = run_insight_query(mock_conn, "Show unassigned schedules")

        assert result["question"] == "Show unassigned schedules"
        assert mock_enrich.called
        assert mock_client.chat.completions.create.call_count == 2

        phase2_call = mock_client.chat.completions.create.call_args_list[1]
        phase2_user_message = phase2_call[1]["messages"][1]["content"]
        assert "ENRICHED CONTEXT" in phase2_user_message

    @patch("app.services.insights._enrich_unassigned_schedules")
    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_phase2_invalid_json(self, mock_openai_class, mock_enrich, mock_conn):
        """Should raise error if Phase 2 returns invalid JSON"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        phase1_response = MagicMock()
        phase1_response.choices[0].message.content = '{"sql": "SELECT 1"}'

        phase2_response = MagicMock()
        phase2_response.choices[0].message.content = "invalid json"

        mock_client.chat.completions.create.side_effect = [phase1_response, phase2_response]

        mock_result = MagicMock()
        mock_result.keys.return_value = ["col"]
        mock_result.fetchmany.return_value = [(1,)]
        mock_conn.execute.return_value = mock_result

        mock_enrich.return_value = {}

        with pytest.raises(RuntimeError, match="Phase 2 returned invalid JSON"):
            run_insight_query(mock_conn, "test")

    @patch("app.services.insights._enrich_unassigned_schedules")
    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_handles_empty_result_set(self, mock_openai_class, mock_enrich, mock_conn):
        """Should handle empty query results"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        phase1_response = MagicMock()
        phase1_response.choices[0].message.content = '{"sql": "SELECT * FROM guides WHERE id = 999"}'

        phase2_response = MagicMock()
        phase2_response.choices[0].message.content = json.dumps(
            {
                "answer": "No guides found",
                "chart": {"type": "number", "title": "Guides", "data": [{"label": "Count", "value": 0}]},
                "recommendations": [],
            }
        )

        mock_client.chat.completions.create.side_effect = [phase1_response, phase2_response]

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchmany.return_value = []
        mock_conn.execute.return_value = mock_result

        mock_enrich.return_value = {}

        result = run_insight_query(mock_conn, "Find guide 999")

        assert result["answer"] == "No guides found"

    @patch("app.services.insights._enrich_unassigned_schedules")
    @patch("app.services.insights.OpenAI")
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_respects_max_rows_limit(self, mock_openai_class, mock_enrich, mock_conn):
        """Should limit query results to 100 rows"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        phase1_response = MagicMock()
        phase1_response.choices[0].message.content = '{"sql": "SELECT * FROM guides"}'

        phase2_response = MagicMock()
        phase2_response.choices[0].message.content = json.dumps(
            {"answer": "100 guides", "chart": {"type": "list", "title": "Guides", "data": []}, "recommendations": []}
        )

        mock_client.chat.completions.create.side_effect = [phase1_response, phase2_response]

        mock_result = MagicMock()
        mock_result.keys.return_value = ["id"]
        mock_result.fetchmany.return_value = [(i,) for i in range(100)]
        mock_conn.execute.return_value = mock_result

        mock_enrich.return_value = {}

        run_insight_query(mock_conn, "List all guides")

        mock_result.fetchmany.assert_called_once_with(100)
