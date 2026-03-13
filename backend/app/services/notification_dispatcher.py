"""Utility for dispatching notification events.

This module provides a helper function to dispatch notification events
returned by services. It can be used by routes or other services that
need to trigger notifications based on events.
"""

from __future__ import annotations

import logging

from . import notification as notification_service

logger = logging.getLogger(__name__)


def dispatch_events(conn, events: list[dict]) -> None:
    """Dispatch a list of notification events.

    Args:
        conn: Database connection
        events: List of notification event dictionaries with 'type' field
    """
    for event in events:
        event_type = event.get("type")

        try:
            if event_type == "GUIDE_ASSIGNED":
                notification_service.notify_guide_assignment(
                    conn, event["schedule_id"], event["guide_id"], event["assignment_type"]
                )
            elif event_type == "GUIDE_UNASSIGNED":
                notification_service.notify_guide_unassignment(
                    conn, event["schedule_id"], event["guide_id"], event["reason"]
                )
            elif event_type == "SCHEDULE_UNASSIGNABLE":
                notification_service.notify_schedule_unassignable(conn, event["schedule_id"], event["reasons"])
            elif event_type == "SCHEDULE_CHANGED":
                notification_service.notify_schedule_change(
                    conn,
                    event["schedule_id"],
                    event["event_type"],
                    event["reason"],
                    affected_guide_id=event.get("affected_guide_id"),
                )
            else:
                logger.warning(f"Unknown notification event type: {event_type}")
        except Exception as e:
            logger.error(f"Failed to dispatch notification event {event_type}: {e}")
            # Don't re-raise - notification failures shouldn't break the main flow
