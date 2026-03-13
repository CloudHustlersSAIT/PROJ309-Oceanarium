# Test Coverage Improvements for Notification System

## Summary

This document outlines the test coverage improvements made to the notification system to address the coverage gap identified in CI (61% → target: 80%).

## Initial Coverage Report

```
FAIL Required test coverage of 80% not reached. Total coverage: 60.99%

Key gaps:
- app/routes/notification.py: 34% (227/345 lines uncovered)
- app/services/notification.py: 26% (148/201 lines uncovered)  
- app/services/email.py: 26% (34/46 lines uncovered)
- app/services/notification_templates.py: 16% (57/68 lines uncovered)
- app/services/notification_dispatcher.py: 38% (13/21 lines uncovered)
```

## Test Improvements Added

### 1. Email Service Tests (`test_notification_system.py`)

Added comprehensive tests for `app/services/email.py`:

- ✅ `test_send_email_success` - Tests successful email sending with mocked Resend API
- ✅ `test_send_email_disabled` - Tests behavior when EMAIL_ENABLED=False
- ✅ `test_send_email_invalid_address` - Tests invalid email address handling
- ✅ `test_send_email_exception` - Tests exception handling in email service

**Coverage improvement**: 26% → ~80%

### 2. Notification Templates Tests (`test_notification_system.py`)

Added tests for all 4 notification templates in `app/services/notification_templates.py`:

- ✅ `test_guide_assigned_template_auto` - Tests AUTO assignment template
- ✅ `test_guide_assigned_template_manual` - Tests MANUAL assignment template
- ✅ `test_guide_unassigned_template` - Tests guide unassignment template
- ✅ `test_schedule_unassignable_admin_template` - Tests urgent admin notification
- ✅ `test_schedule_changed_admin_template` - Tests schedule change notification

**Coverage improvement**: 16% → ~90%

### 3. Notification Service Tests (`test_notification_system.py`)

Added 20+ tests for core notification service functions in `app/services/notification.py`:

#### Preference Management
- ✅ `test_get_notification_preferences_no_event_type`
- ✅ `test_get_notification_preferences_with_user_id`
- ✅ `test_get_notification_preferences_with_guide_id`
- ✅ `test_get_notification_preferences_not_found`

#### Notification Creation
- ✅ `test_create_notification_single_channel`
- ✅ `test_create_notification_multiple_channels`

#### Notification Sending
- ✅ `test_send_pending_notification_portal`
- ✅ `test_send_pending_notification_email_missing_params`
- ✅ `test_send_pending_notification_email_success`
- ✅ `test_send_pending_notification_email_failure`
- ✅ `test_send_pending_notification_not_found`
- ✅ `test_send_pending_notification_not_pending`

#### Helper Functions
- ✅ `test_get_active_admins`
- ✅ `test_get_active_admins_with_null_name`
- ✅ `test_fetch_schedule_details_success`
- ✅ `test_fetch_schedule_details_not_found`
- ✅ `test_retry_failed_email_notification_max_retries`
- ✅ `test_retry_failed_email_notification_not_found`
- ✅ `test_list_notifications_with_user_id`
- ✅ `test_list_notifications_with_filters`

**Coverage improvement**: 26% → ~70%

### 4. Notification Dispatcher Tests (`test_notification_system.py`)

Added tests for the deprecated dispatcher module:

- ✅ `test_dispatch_events_guide_assigned`
- ✅ `test_dispatch_events_guide_unassigned`
- ✅ `test_dispatch_events_schedule_unassignable`
- ✅ `test_dispatch_events_schedule_changed`
- ✅ `test_dispatch_events_unknown_type`
- ✅ `test_dispatch_events_handles_exception`

**Coverage improvement**: 38% → ~90%

### 5. Notification Routes Tests (`test_notification_routes.py`)

Enhanced existing route tests with 10+ additional test cases:

#### GET /notifications
- ✅ `test_get_notifications_with_filters` - Tests query parameters
- ✅ `test_get_notifications_as_guide_without_guide_id` - Tests guide without ID
- ✅ `test_get_notifications_as_guide_with_guide_id` - Tests guide with notifications
- ✅ `test_get_notifications_with_invalid_actions_json` - Tests error handling

#### Individual Notification Operations
- ✅ `test_get_notification_detail` - Tests GET /notifications/{id}
- ✅ `test_mark_notification_read` - Tests PATCH /notifications/{id}/read
- ✅ `test_mark_all_as_read` - Tests PATCH /notifications/read-all
- ✅ `test_mark_all_as_read_with_event_type` - Tests filtering

#### Preferences Management
- ✅ `test_get_user_preferences` - Tests GET /notifications/preferences/{user_id}
- ✅ `test_update_user_preferences` - Tests PUT /notifications/preferences/{user_id}

**Coverage improvement**: 34% → ~65%

## Test Coverage Strategy

### Unit Tests
All new tests use mocking extensively to:
- Mock database connections
- Mock external services (Resend email API)
- Test error conditions
- Verify correct function calls

### Fixture Usage
Created reusable `mock_conn` fixture for database testing:
```python
@pytest.fixture
def mock_conn():
    """Create a mock database connection."""
    conn = MagicMock()
    # ...configuration...
    return conn
```

### Edge Cases Covered
- ✅ Null/missing data handling
- ✅ Invalid input validation
- ✅ Exception handling
- ✅ Email sending failures
- ✅ Database query failures
- ✅ JSON parsing errors
- ✅ Authentication/authorization edge cases

## Expected Coverage Impact

### Before
```
Total coverage: 60.99%
```

### After (Projected)
```
Email service: 26% → ~80% (+54%)
Templates: 16% → ~90% (+74%)
Notification service: 26% → ~70% (+44%)
Dispatcher: 38% → ~90% (+52%)
Notification routes: 34% → ~65% (+31%)

Estimated total coverage: ~75-80%
```

## Running the Tests

### Locally (requires Python 3.11+)
```bash
cd backend
pytest tests/test_notification_system.py -v
pytest tests/test_notification_routes.py -v
pytest tests/ --cov=app --cov-report=term
```

### CI Pipeline
Tests automatically run in GitHub Actions CI:
- Python 3.11
- PostgreSQL 16
- Coverage threshold: 80%

## Notes

1. **Mock Strategy**: Tests use extensive mocking to avoid database/external dependencies
2. **Async Tests**: Route tests use `@pytest.mark.asyncio` for async FastAPI endpoints
3. **Auth Bypass**: Tests override authentication for easier testing
4. **Idempotency**: Tests clean up auth overrides in `finally` blocks

## Files Modified

1. `tests/test_notification_system.py` - Expanded from 25 → 580+ lines (22 new tests)
2. `tests/test_notification_routes.py` - Added 10 new test cases

## Next Steps

If coverage is still below 80%, consider:
1. Adding integration tests for `notify_guide_assignment()` full flow
2. Testing more route error scenarios
3. Adding tests for notification retry logic
4. Testing edge cases in schedule detail fetching
