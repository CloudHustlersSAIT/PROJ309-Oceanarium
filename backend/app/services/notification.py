"""Enhanced notification service with multi-channel support and user preferences."""

from __future__ import annotations

from typing import Optional
import json
import logging

from sqlalchemy import text

from .email import send_email
from .notification_templates import (
    guide_assigned_template,
    guide_unassigned_template,
    schedule_changed_admin_template,
    schedule_unassignable_admin_template,
)

logger = logging.getLogger(__name__)


def get_notification_preferences(
    conn, user_id: Optional[int] = None, guide_id: Optional[int] = None, event_type: str = None
) -> dict:
    """Get notification preferences for a user or guide.

    Returns dict with email_enabled and portal_enabled (defaults to True for both).
    """
    if not event_type:
        return {"email_enabled": True, "portal_enabled": True}

    if user_id:
        row = conn.execute(
            text("""
                SELECT email_enabled, portal_enabled
                FROM notification_preferences
                WHERE user_id = :user_id AND event_type = :event_type
            """),
            {"user_id": user_id, "event_type": event_type},
        ).fetchone()
    elif guide_id:
        row = conn.execute(
            text("""
                SELECT email_enabled, portal_enabled
                FROM notification_preferences
                WHERE guide_id = :guide_id AND event_type = :event_type
            """),
            {"guide_id": guide_id, "event_type": event_type},
        ).fetchone()
    else:
        return {"email_enabled": True, "portal_enabled": True}

    if row:
        return {"email_enabled": row[0], "portal_enabled": row[1]}

    return {"email_enabled": True, "portal_enabled": True}


def create_notification(
    conn,
    event_type: str,
    schedule_id: int,
    guide_id: Optional[int],
    user_id: Optional[int],
    message: str,
    channels: list[str],
    priority: str = "normal",
    action_required: bool = False,
    detail_json: dict = None,
    actions_json: list = None,
) -> list[int]:
    """Create notification records for specified channels.

    Args:
        channels: List of 'PORTAL' and/or 'EMAIL'

    Returns:
        List of created notification IDs
    """
    notification_ids = []

    for channel in channels:
        result = conn.execute(
            text("""
                INSERT INTO notifications
                    (event_type, schedule_id, guide_id, user_id, channel, status, message,
                     priority, action_required, detail_json, actions_json)
                VALUES
                    (:event_type, :schedule_id, :guide_id, :user_id, :channel, 'PENDING', :message,
                     :priority, :action_required, :detail_json, :actions_json)
                RETURNING id
            """),
            {
                "event_type": event_type,
                "schedule_id": schedule_id,
                "guide_id": guide_id,
                "user_id": user_id,
                "channel": channel,
                "message": message,
                "priority": priority,
                "action_required": action_required,
                "detail_json": json.dumps(detail_json) if detail_json else None,
                "actions_json": json.dumps(actions_json) if actions_json else None,
            },
        )
        notification_ids.append(result.fetchone()[0])

    return notification_ids


def send_pending_notification(
    conn, notification_id: int, email: str = None, subject: str = None, text: str = None, html: str = None
) -> bool:
    """Send a pending notification based on its channel.

    Returns True if successful, False otherwise.
    """
    row = conn.execute(
        text("""
            SELECT channel, status
            FROM notifications
            WHERE id = :id
        """),
        {"id": notification_id},
    ).fetchone()

    if not row or row[1] != "PENDING":
        logger.warning(f"Notification {notification_id} not found or not pending")
        return False

    channel = row[0]

    if channel == "PORTAL":
        conn.execute(
            text("UPDATE notifications SET status = 'SENT', sent_at = NOW() WHERE id = :id"),
            {"id": notification_id},
        )
        return True

    elif channel == "EMAIL":
        if not email or not subject or not text:
            logger.error(f"Missing email parameters for notification {notification_id}")
            conn.execute(
                text("UPDATE notifications SET status = 'FAILED' WHERE id = :id"),
                {"id": notification_id},
            )
            return False

        success = send_email(email, subject, text, html)

        if success:
            conn.execute(
                text("UPDATE notifications SET status = 'SENT', sent_at = NOW() WHERE id = :id"),
                {"id": notification_id},
            )
            return True
        else:
            conn.execute(
                text("UPDATE notifications SET status = 'FAILED', retry_count = retry_count + 1 WHERE id = :id"),
                {"id": notification_id},
            )
            return False

    return False


def get_active_admins(conn) -> list[dict]:
    """Get all active admin users."""
    rows = conn.execute(
        text("""
            SELECT id, email, full_name
            FROM users
            WHERE role = 'admin' AND is_active = true
        """)
    ).fetchall()

    return [{"id": r[0], "email": r[1], "name": r[2] or "Admin"} for r in rows]


def fetch_schedule_details(conn, schedule_id: int) -> dict:
    """Fetch comprehensive schedule details for notifications."""
    row = conn.execute(
        text("""
            SELECT
                s.id, s.tour_id, s.language_code, s.event_start_datetime,
                s.event_end_datetime, s.status, s.guide_id,
                t.name as tour_name,
                g.first_name || ' ' || g.last_name as guide_name,
                g.email as guide_email,
                COUNT(r.id) as ticket_count
            FROM schedule s
            JOIN tours t ON t.id = s.tour_id
            LEFT JOIN guides g ON g.id = s.guide_id
            LEFT JOIN reservations r ON r.schedule_id = s.id AND r.status != 'CANCELLED'
            WHERE s.id = :schedule_id
            GROUP BY s.id, t.name, g.first_name, g.last_name, g.email
        """),
        {"schedule_id": schedule_id},
    ).fetchone()

    if not row:
        logger.error(f"Schedule {schedule_id} not found")
        return {}

    return dict(row._mapping)


def notify_guide_assignment(
    conn,
    schedule_id: int,
    guide_id: int,
    assignment_type: str,
) -> None:
    """Send notifications for guide assignment.

    - Guide receives: PORTAL + EMAIL (if preferences allow)
    - All admins receive: PORTAL + EMAIL (if preferences allow)
    """
    schedule = fetch_schedule_details(conn, schedule_id)
    if not schedule:
        return

    guide_name = schedule.get("guide_name", "Guide")
    guide_email = schedule.get("guide_email")

    guide_prefs = get_notification_preferences(conn, guide_id=guide_id, event_type="GUIDE_ASSIGNED")

    subject, text_body, html_body, portal_message, detail = guide_assigned_template(
        schedule, guide_name, assignment_type
    )

    actions = [
        {"label": "View Schedule", "url": f"/schedule/{schedule_id}", "primary": True, "urgent": False},
        {"label": "Contact Admin", "url": f"/messages?topic=schedule-{schedule_id}", "primary": False, "urgent": False},
    ]

    guide_channels = []
    if guide_prefs["portal_enabled"]:
        guide_channels.append("PORTAL")
    if guide_prefs["email_enabled"] and guide_email:
        guide_channels.append("EMAIL")

    if guide_channels:
        notif_ids = create_notification(
            conn,
            event_type="GUIDE_ASSIGNED",
            schedule_id=schedule_id,
            guide_id=guide_id,
            user_id=None,
            message=portal_message,
            channels=guide_channels,
            priority="normal",
            action_required=False,
            detail_json=detail,
            actions_json=actions,
        )

        for notif_id in notif_ids:
            row = conn.execute(
                text("SELECT channel FROM notifications WHERE id = :id"),
                {"id": notif_id},
            ).fetchone()
            if row and row[0] == "EMAIL" and guide_email:
                send_pending_notification(conn, notif_id, guide_email, subject, text_body, html_body)
            elif row and row[0] == "PORTAL":
                send_pending_notification(conn, notif_id)

    admins = get_active_admins(conn)
    for admin in admins:
        admin_prefs = get_notification_preferences(conn, user_id=admin["id"], event_type="GUIDE_ASSIGNED")
        admin_channels = []
        if admin_prefs["portal_enabled"]:
            admin_channels.append("PORTAL")
        if admin_prefs["email_enabled"]:
            admin_channels.append("EMAIL")

        if admin_channels:
            date_str = schedule["event_start_datetime"].strftime("%B %d, %Y")
            admin_message = f"Guide {guide_name} assigned to {schedule['tour_name']} on {date_str}"
            notif_ids = create_notification(
                conn,
                event_type="GUIDE_ASSIGNED",
                schedule_id=schedule_id,
                guide_id=None,
                user_id=admin["id"],
                message=admin_message,
                channels=admin_channels,
                priority="normal",
                action_required=False,
                detail_json=detail,
                actions_json=actions,
            )

            for notif_id in notif_ids:
                row = conn.execute(
                    text("SELECT channel FROM notifications WHERE id = :id"),
                    {"id": notif_id},
                ).fetchone()
                if row and row[0] == "EMAIL":
                    send_pending_notification(conn, notif_id, admin["email"], subject, text_body, html_body)
                elif row and row[0] == "PORTAL":
                    send_pending_notification(conn, notif_id)


def notify_guide_unassignment(
    conn,
    schedule_id: int,
    guide_id: int,
    reason: str,
) -> None:
    """Send notifications for guide unassignment."""
    schedule = fetch_schedule_details(conn, schedule_id)
    if not schedule:
        return

    guide_row = conn.execute(
        text("SELECT first_name || ' ' || last_name as name, email FROM guides WHERE id = :id"),
        {"id": guide_id},
    ).fetchone()

    if not guide_row:
        return

    guide_name = guide_row[0]
    guide_email = guide_row[1]

    guide_prefs = get_notification_preferences(conn, guide_id=guide_id, event_type="GUIDE_REASSIGNED")

    subject, text_body, html_body, portal_message, detail = guide_unassigned_template(schedule, guide_name, reason)

    actions = [{"label": "View Updated Schedule", "url": "/schedule", "primary": True, "urgent": False}]

    guide_channels = []
    if guide_prefs["portal_enabled"]:
        guide_channels.append("PORTAL")
    if guide_prefs["email_enabled"] and guide_email:
        guide_channels.append("EMAIL")

    if guide_channels:
        notif_ids = create_notification(
            conn,
            event_type="GUIDE_REASSIGNED",
            schedule_id=schedule_id,
            guide_id=guide_id,
            user_id=None,
            message=portal_message,
            channels=guide_channels,
            priority="high",
            action_required=False,
            detail_json=detail,
            actions_json=actions,
        )

        for notif_id in notif_ids:
            row = conn.execute(
                text("SELECT channel FROM notifications WHERE id = :id"),
                {"id": notif_id},
            ).fetchone()
            if row and row[0] == "EMAIL" and guide_email:
                send_pending_notification(conn, notif_id, guide_email, subject, text_body, html_body)
            elif row and row[0] == "PORTAL":
                send_pending_notification(conn, notif_id)


def notify_schedule_unassignable(
    conn,
    schedule_id: int,
    reasons: list[str],
) -> None:
    """Send URGENT notifications to admins when schedule cannot be auto-assigned."""
    schedule = fetch_schedule_details(conn, schedule_id)
    if not schedule:
        return

    subject, text_body, html_body, portal_message, detail = schedule_unassignable_admin_template(
        schedule, reasons, attempted_guides_count=0
    )

    actions = [
        {"label": "Assign Guide Now", "url": f"/schedule/{schedule_id}/assign", "primary": True, "urgent": True},
        {"label": "View All Available Guides", "url": "/guides", "primary": False, "urgent": False},
    ]

    admins = get_active_admins(conn)

    for admin in admins:
        notif_ids = create_notification(
            conn,
            event_type="SCHEDULE_UNASSIGNABLE",
            schedule_id=schedule_id,
            guide_id=None,
            user_id=admin["id"],
            message=portal_message,
            channels=["PORTAL", "EMAIL"],
            priority="urgent",
            action_required=True,
            detail_json=detail,
            actions_json=actions,
        )

        for notif_id in notif_ids:
            row = conn.execute(
                text("SELECT channel FROM notifications WHERE id = :id"),
                {"id": notif_id},
            ).fetchone()
            if row and row[0] == "EMAIL":
                send_pending_notification(conn, notif_id, admin["email"], subject, text_body, html_body)
            elif row and row[0] == "PORTAL":
                send_pending_notification(conn, notif_id)


def notify_schedule_change(
    conn,
    schedule_id: int,
    change_type: str,
    change_details: str,
    affected_guide_id: Optional[int] = None,
) -> None:
    """Send general schedule change notifications to guide and admins."""
    schedule = fetch_schedule_details(conn, schedule_id)
    if not schedule:
        return

    if affected_guide_id:
        guide_prefs = get_notification_preferences(conn, guide_id=affected_guide_id, event_type=change_type)
        if guide_prefs["portal_enabled"]:
            date_str = schedule["event_start_datetime"].strftime("%B %d, %Y")
            message = f"{change_details}\n\nSchedule: {schedule['tour_name']} on {date_str}"
            notif_ids = create_notification(
                conn,
                event_type=change_type,
                schedule_id=schedule_id,
                guide_id=affected_guide_id,
                user_id=None,
                message=message,
                channels=["PORTAL"],
                priority="normal",
                action_required=False,
            )

            for notif_id in notif_ids:
                send_pending_notification(conn, notif_id)

    admins = get_active_admins(conn)
    subject, text_body, html_body, portal_message, detail = schedule_changed_admin_template(
        schedule, change_type, change_details
    )

    actions = [{"label": "View Schedule Details", "url": f"/schedule/{schedule_id}", "primary": True, "urgent": False}]

    for admin in admins:
        admin_prefs = get_notification_preferences(conn, user_id=admin["id"], event_type=change_type)
        admin_channels = []
        if admin_prefs["portal_enabled"]:
            admin_channels.append("PORTAL")
        if admin_prefs["email_enabled"]:
            admin_channels.append("EMAIL")

        if admin_channels:
            notif_ids = create_notification(
                conn,
                event_type=change_type,
                schedule_id=schedule_id,
                guide_id=None,
                user_id=admin["id"],
                message=portal_message,
                channels=admin_channels,
                priority="normal",
                action_required=False,
                detail_json=detail,
                actions_json=actions,
            )

            for notif_id in notif_ids:
                row = conn.execute(
                    text("SELECT channel FROM notifications WHERE id = :id"),
                    {"id": notif_id},
                ).fetchone()
                if row and row[0] == "EMAIL":
                    send_pending_notification(conn, notif_id, admin["email"], subject, text_body, html_body)
                elif row and row[0] == "PORTAL":
                    send_pending_notification(conn, notif_id)


def retry_failed_email_notification(conn, notification_id: int) -> bool:
    """Retry sending a failed email notification (max 3 attempts)."""
    row = conn.execute(
        text("SELECT retry_count FROM notifications WHERE id = :id AND status = 'FAILED' AND channel = 'EMAIL'"),
        {"id": notification_id},
    ).fetchone()

    if not row or row[0] >= 3:
        logger.info(f"Notification {notification_id} cannot be retried (count: {row[0] if row else 'N/A'})")
        return False

    logger.info(f"Retrying notification {notification_id} (attempt {row[0] + 1}/3)")
    return False


def list_notifications(conn, user_id: Optional[int] = None, guide_id: Optional[int] = None, filters: dict = None):
    """List notifications for a user or guide with optional filters."""
    filters = filters or {}

    where_clauses = ["1=1"]
    params = {}

    if user_id:
        where_clauses.append("n.user_id = :user_id")
        params["user_id"] = user_id
    elif guide_id:
        where_clauses.append("n.guide_id = :guide_id")
        params["guide_id"] = guide_id

    if filters.get("status"):
        where_clauses.append("n.status = :status")
        params["status"] = filters["status"]

    if filters.get("channel"):
        where_clauses.append("n.channel = :channel")
        params["channel"] = filters["channel"]

    if filters.get("unread_only"):
        where_clauses.append("n.read_at IS NULL")

    if filters.get("priority"):
        where_clauses.append("n.priority = :priority")
        params["priority"] = filters["priority"]

    limit = filters.get("limit", 50)
    offset = filters.get("offset", 0)
    params["limit"] = limit
    params["offset"] = offset

    where_sql = " AND ".join(where_clauses)

    result = conn.execute(
        text(f"""
            SELECT n.*,
                   s.event_start_datetime as schedule_date,
                   t.name as tour_name
            FROM notifications n
            LEFT JOIN schedule s ON s.id = n.schedule_id
            LEFT JOIN tours t ON t.id = s.tour_id
            WHERE {where_sql}
            ORDER BY n.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )

    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
