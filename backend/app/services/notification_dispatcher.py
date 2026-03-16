"""DEPRECATED: Utility for dispatching notification events.

⚠️ DEPRECATION NOTICE (v3.0 - 2026-03-13) ⚠️

This module is deprecated as of v3.0 (2026-03-13).

Notifications are now triggered via direct service calls or dedicated API endpoints.
See FDR-003 v3.0 for the new architecture.

Instead of using dispatch_events(), use one of:
1. Direct service calls:
   - notification_service.notify_guide_assignment(conn, schedule_id, guide_id, assignment_type)
   - notification_service.notify_guide_unassignment(conn, schedule_id, guide_id, reason)
   - notification_service.notify_schedule_unassignable(conn, schedule_id, reasons)
   - notification_service.notify_schedule_change(conn, schedule_id, change_type, details, guide_id)

2. Dedicated API endpoints:
   - POST /notifications/guide-assigned
   - POST /notifications/guide-unassigned
   - POST /notifications/schedule-unassignable
   - POST /notifications/schedule-changed

This file will be removed in a future version.
"""

from __future__ import annotations

import logging
import warnings

from . import notification as notification_service

logger = logging.getLogger(__name__)

# Issue deprecation warning when this module is imported
warnings.warn(
    "notification_dispatcher is deprecated. Use direct notification service calls "
    "or POST /notifications/* API endpoints. See FDR-003 v3.0 for details.",
    DeprecationWarning,
    stacklevel=2,
)


def dispatch_events(conn, events: list[dict], *, commit: bool = True) -> None:
    """Dispatch a list of notification events.

    Args:
        conn: Database connection
        events: List of notification event dictionaries with 'type' field
    """
    for event in events:
        event_type = event.get("type")

        try:
            if event_type == "GUIDE_ASSIGNED":
                if commit:
                    notification_service.notify_guide_assignment(
                        conn,
                        event["schedule_id"],
                        event["guide_id"],
                        event["assignment_type"],
                    )
                else:
                    notification_service.notify_guide_assignment(
                        conn,
                        event["schedule_id"],
                        event["guide_id"],
                        event["assignment_type"],
                        commit=False,
                    )
            elif event_type == "GUIDE_UNASSIGNED":
                if commit:
                    notification_service.notify_guide_unassignment(
                        conn,
                        event["schedule_id"],
                        event["guide_id"],
                        event["reason"],
                    )
                else:
                    notification_service.notify_guide_unassignment(
                        conn,
                        event["schedule_id"],
                        event["guide_id"],
                        event["reason"],
                        commit=False,
                    )
            elif event_type == "SCHEDULE_UNASSIGNABLE":
                if commit:
                    notification_service.notify_schedule_unassignable(
                        conn,
                        event["schedule_id"],
                        event["reasons"],
                    )
                else:
                    notification_service.notify_schedule_unassignable(
                        conn,
                        event["schedule_id"],
                        event["reasons"],
                        commit=False,
                    )
            elif event_type == "SCHEDULE_CHANGED":
                if commit:
                    notification_service.notify_schedule_change(
                        conn,
                        event["schedule_id"],
                        event["event_type"],
                        event["reason"],
                        affected_guide_id=event.get("affected_guide_id"),
                    )
                else:
                    notification_service.notify_schedule_change(
                        conn,
                        event["schedule_id"],
                        event["event_type"],
                        event["reason"],
                        affected_guide_id=event.get("affected_guide_id"),
                        commit=False,
                    )
            else:
                logger.warning(f"Unknown notification event type: {event_type}")
        except Exception as e:
            logger.error(f"Failed to dispatch notification event {event_type}: {e}")
            # Don't re-raise - notification failures shouldn't break the main flow
