from unittest.mock import MagicMock, patch

import app.main as main_module


class TestRunListener:
    def test_success_with_processed_rows(self):
        main_module._last_poller_warning_at = None

        with (
            patch.object(main_module, "engine") as mock_engine,
            patch.object(main_module, "process_staging_rows", return_value=3),
        ):
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

            main_module.run_listener()

        assert main_module._last_poller_warning_at is None

    def test_success_with_zero_rows(self):
        main_module._last_poller_warning_at = 100.0

        with (
            patch.object(main_module, "engine") as mock_engine,
            patch.object(main_module, "process_staging_rows", return_value=0),
        ):
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

            main_module.run_listener()

        assert main_module._last_poller_warning_at is None

    def test_logs_warning_on_first_error(self):
        main_module._last_poller_warning_at = None

        with (
            patch.object(main_module, "engine") as mock_engine,
            patch.object(main_module, "logger") as mock_logger,
            patch("time.monotonic", return_value=1000.0),
        ):
            mock_engine.begin.side_effect = Exception("connection refused")

            main_module.run_listener()

        mock_logger.warning.assert_called_once()
        assert main_module._last_poller_warning_at == 1000.0

    def test_throttles_repeated_warnings(self):
        main_module._last_poller_warning_at = 999.0

        with (
            patch.object(main_module, "engine") as mock_engine,
            patch.object(main_module, "logger") as mock_logger,
            patch("time.monotonic", return_value=1005.0),
        ):
            mock_engine.begin.side_effect = Exception("connection refused")

            main_module.run_listener()

        mock_logger.warning.assert_not_called()

    def test_logs_after_throttle_window(self):
        main_module._last_poller_warning_at = 900.0

        with (
            patch.object(main_module, "engine") as mock_engine,
            patch.object(main_module, "logger") as mock_logger,
            patch("time.monotonic", return_value=961.0),
        ):
            mock_engine.begin.side_effect = Exception("connection refused")

            main_module.run_listener()

        mock_logger.warning.assert_called_once()
        assert main_module._last_poller_warning_at == 961.0
