"""
Mock poller module for testing purposes.
Endpoint: POST /mock/run

Behavior:
- Creates a run in santiago_tests.mock_poller_runs (The schema can be changed as needed).
- Generates mock records based on set parameters
- Inserts said mock records into santiago_tests.mock_clorian_staging (The schema can be changed as needed).


Additional Notes:
- This module is intended for testing purposes and should not be used in production environments.
- Uses JSONB payload storage to translate a python dict into a JSON
"""
