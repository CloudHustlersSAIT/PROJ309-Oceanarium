"""Enhanced notification routes with authentication, preferences, and detail view."""

import json
import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from ..db import get_db
from ..dependencies.auth import require_resolved_user
from ..services import notification as notification_service
from ..services.error_handlers import handle_domain_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# Pydantic models for v3.0 trigger endpoints
class GuideAssignedRequest(BaseModel):
    schedule_id: int = Field(..., description="Schedule ID")
    guide_id: int = Field(..., description="Guide ID who was assigned")
    assignment_type: str = Field(..., pattern="^(AUTO|MANUAL)$", description="Assignment type: AUTO or MANUAL")


class GuideUnassignedRequest(BaseModel):
    schedule_id: int = Field(..., description="Schedule ID")
    guide_id: int = Field(..., description="Guide ID who was unassigned")
    reason: str = Field(..., description="Reason for unassignment")
    replacement_guide_id: int | None = Field(None, description="Replacement guide ID if applicable")


class ScheduleUnassignableRequest(BaseModel):
    schedule_id: int = Field(..., description="Schedule ID")
    reasons: list[str] = Field(..., description="List of constraint failures")
    attempted_guides_count: int = Field(0, description="Number of guides checked")


class ScheduleChangedRequest(BaseModel):
    schedule_id: int = Field(..., description="Schedule ID")
    change_type: str = Field(..., description="Type of change (e.g., RESERVATION_CANCELLED, RESERVATION_MOVED)")
    change_details: str = Field(..., description="Description of the change")
    affected_guide_id: int | None = Field(None, description="Guide affected by the change")
    old_state: dict | None = Field(None, description="Previous state before change")
    new_state: dict | None = Field(None, description="New state after change")


@router.get("")
def read_notifications(
    status: str = Query(None),
    channel: str = Query(None),
    event_type: str = Query(None),
    unread_only: bool = Query(False),
    priority: str = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """List notifications for the authenticated user with enhanced filtering.

    Admins see all notifications. Guides see only their notifications.
    """
    try:
        filters = {
            "status": status,
            "channel": channel,
            "event_type": event_type,
            "unread_only": unread_only,
            "priority": priority,
            "limit": limit,
            "offset": offset,
        }

        # Determine if user is admin or guide
        user_role = current_user.get("role", "guide")

        if user_role == "admin":
            # Admin sees notifications for their user_id
            user_id = current_user.get("user_id")
            notifications = notification_service.list_notifications(conn, user_id=user_id, filters=filters)
        else:
            # Guide sees their guide-specific notifications
            # Assuming guide_id is stored in current_user
            guide_id = current_user.get("guide_id")
            if not guide_id:
                return {
                    "notifications": [],
                    "pagination": {"total": 0, "limit": limit, "offset": offset, "has_more": False},
                    "summary": {"unread_count": 0, "urgent_count": 0, "action_required_count": 0},
                }

            notifications = notification_service.list_notifications(conn, guide_id=guide_id, filters=filters)

        # Calculate summary
        total = len(notifications)  # Note: This is limited by pagination
        unread_count = sum(1 for n in notifications if n.get("read_at") is None)
        urgent_count = sum(1 for n in notifications if n.get("priority") == "urgent")
        action_required_count = sum(1 for n in notifications if n.get("action_required"))

        # Extract primary action from actions_json
        for notif in notifications:
            if notif.get("actions_json"):
                try:
                    actions = (
                        json.loads(notif["actions_json"])
                        if isinstance(notif["actions_json"], str)
                        else notif["actions_json"]
                    )
                    primary = next((a for a in actions if a.get("primary")), None)
                    notif["primary_action"] = primary
                except Exception:
                    notif["primary_action"] = None

        return {
            "notifications": notifications,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": total == limit,  # Simple approximation
            },
            "summary": {
                "unread_count": unread_count,
                "urgent_count": urgent_count,
                "action_required_count": action_required_count,
            },
        }

    except Exception as e:
        return handle_domain_exception(e)


@router.get("/summary")
def get_notification_summary(
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Get notification counts and summary for current user."""
    try:
        user_id = current_user.get("user_id")
        guide_id = current_user.get("guide_id")

        where_clause = "(user_id = :user_id OR guide_id = :guide_id) AND channel = 'PORTAL'"
        params = {"user_id": user_id, "guide_id": guide_id}

        result = conn.execute(
            text(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN read_at IS NULL THEN 1 END) as unread,
                    COUNT(CASE WHEN priority = 'urgent' THEN 1 END) as urgent,
                    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
                    COUNT(CASE WHEN priority = 'normal' THEN 1 END) as normal,
                    COUNT(CASE WHEN priority = 'low' THEN 1 END) as low,
                    COUNT(CASE WHEN action_required = true THEN 1 END) as action_required
                FROM notifications
                WHERE {where_clause}
            """),
            params,
        ).fetchone()

        summary = dict(result._mapping)

        event_counts = conn.execute(
            text(f"""
                SELECT event_type, COUNT(*) as count
                FROM notifications
                WHERE {where_clause}
                GROUP BY event_type
            """),
            params,
        ).fetchall()

        summary["by_event_type"] = {row[0]: row[1] for row in event_counts}
        summary["by_priority"] = {
            "urgent": summary.pop("urgent"),
            "high": summary.pop("high"),
            "normal": summary.pop("normal"),
            "low": summary.pop("low"),
        }

        return summary

    except Exception as e:
        return handle_domain_exception(e)


@router.get("/preferences")
def get_preferences(
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Get notification preferences for current user."""
    try:
        user_role = current_user.get("role", "guide")
        user_id = current_user.get("user_id") if user_role == "admin" else None
        guide_id = current_user.get("guide_id") if user_role != "admin" else None

        if user_id:
            rows = conn.execute(
                text(
                    "SELECT event_type, email_enabled, portal_enabled FROM notification_preferences WHERE user_id = :id"
                ),
                {"id": user_id},
            ).fetchall()
        elif guide_id:
            rows = conn.execute(
                text(
                    "SELECT event_type, email_enabled, portal_enabled "
                    "FROM notification_preferences WHERE guide_id = :id"
                ),
                {"id": guide_id},
            ).fetchall()
        else:
            return []

        return [
            {
                "event_type": r[0],
                "email_enabled": r[1],
                "portal_enabled": r[2],
            }
            for r in rows
        ]

    except Exception as e:
        return handle_domain_exception(e)


@router.patch("/read-all")
def mark_all_as_read(
    event_type: str = Query(None),
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Mark all unread notifications as read for current user."""
    try:
        user_id = current_user.get("user_id")
        guide_id = current_user.get("guide_id")

        where_clauses = ["read_at IS NULL"]
        params = {"user_id": user_id, "guide_id": guide_id}

        where_clauses.append("(user_id = :user_id OR guide_id = :guide_id)")

        if event_type:
            where_clauses.append("event_type = :event_type")
            params["event_type"] = event_type

        where_sql = " AND ".join(where_clauses)

        result = conn.execute(
            text(f"UPDATE notifications SET read_at = NOW() WHERE {where_sql} RETURNING id"),
            params,
        )
        count = len(result.fetchall())
        conn.commit()

        return {"success": True, "count": count}

    except Exception as e:
        return handle_domain_exception(e)


@router.get("/{notification_id}")
def get_notification_detail(
    notification_id: int,
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Get full notification detail and mark as read."""
    try:
        # Fetch notification with ownership verification
        user_id = current_user.get("user_id")
        guide_id = current_user.get("guide_id")

        row = conn.execute(
            text("""
                SELECT n.*,
                       s.event_start_datetime as schedule_date,
                       t.name as tour_name,
                       email_n.status as email_status,
                       email_n.sent_at as email_sent_at
                FROM notifications n
                LEFT JOIN schedule s ON s.id = n.schedule_id
                LEFT JOIN tours t ON t.id = s.tour_id
                LEFT JOIN notifications email_n
                    ON email_n.group_id = n.group_id
                    AND email_n.channel = 'EMAIL'
                WHERE n.id = :id
                  AND (n.user_id = :user_id OR n.guide_id = :guide_id)
            """),
            {"id": notification_id, "user_id": user_id, "guide_id": guide_id},
        ).fetchone()

        if not row:
            return {"error": "Notification not found"}, 404

        notification = dict(row._mapping)

        # Parse JSON fields
        if notification.get("detail_json"):
            notification["detail"] = (
                json.loads(notification["detail_json"])
                if isinstance(notification["detail_json"], str)
                else notification["detail_json"]
            )

        if notification.get("actions_json"):
            notification["actions"] = (
                json.loads(notification["actions_json"])
                if isinstance(notification["actions_json"], str)
                else notification["actions_json"]
            )

        # Mark as read if not already
        if notification.get("read_at") is None:
            conn.execute(
                text("UPDATE notifications SET read_at = NOW() WHERE id = :id"),
                {"id": notification_id},
            )
            conn.commit()
            notification["read_at"] = "just now"

        # Fetch related notifications (same schedule)
        if notification.get("schedule_id"):
            related_rows = conn.execute(
                text("""
                    SELECT id, message, created_at
                    FROM notifications
                    WHERE schedule_id = :schedule_id
                      AND id != :id
                    ORDER BY created_at DESC
                    LIMIT 5
                """),
                {"schedule_id": notification["schedule_id"], "id": notification_id},
            ).fetchall()
            notification["related_notifications"] = [dict(r._mapping) for r in related_rows]

        return notification

    except Exception as e:
        return handle_domain_exception(e)


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Mark a notification as read."""
    try:
        user_id = current_user.get("user_id")
        guide_id = current_user.get("guide_id")

        # Verify notification belongs to current user
        row = conn.execute(
            text("""
                SELECT id FROM notifications
                WHERE id = :id
                  AND (user_id = :user_id OR guide_id = :guide_id)
                  AND read_at IS NULL
            """),
            {
                "id": notification_id,
                "user_id": user_id,
                "guide_id": guide_id,
            },
        ).fetchone()

        if not row:
            return {"error": "Notification not found or already read"}, 404

        conn.execute(
            text("UPDATE notifications SET read_at = NOW() WHERE id = :id"),
            {"id": notification_id},
        )
        conn.commit()

        return {"success": True, "notification_id": notification_id}

    except Exception as e:
        return handle_domain_exception(e)


@router.put("/preferences")
def update_preferences(
    preferences: list[dict],
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Update notification preferences for current user.

    Body: [{"event_type": "GUIDE_ASSIGNED", "email_enabled": true, "portal_enabled": true}, ...]
    """
    try:
        user_role = current_user.get("role", "guide")
        user_id = current_user.get("user_id") if user_role == "admin" else None
        guide_id = current_user.get("guide_id") if user_role != "admin" else None

        for pref in preferences:
            event_type = pref["event_type"]
            email_enabled = pref.get("email_enabled", True)
            portal_enabled = pref.get("portal_enabled", True)

            if user_id:
                conn.execute(
                    text("""
                        INSERT INTO notification_preferences
                            (user_id, event_type, email_enabled, portal_enabled, updated_at)
                        VALUES
                            (:user_id, :event_type, :email_enabled, :portal_enabled, NOW())
                        ON CONFLICT (user_id, event_type)
                        DO UPDATE SET
                            email_enabled = EXCLUDED.email_enabled,
                            portal_enabled = EXCLUDED.portal_enabled,
                            updated_at = NOW()
                    """),
                    {
                        "user_id": user_id,
                        "event_type": event_type,
                        "email_enabled": email_enabled,
                        "portal_enabled": portal_enabled,
                    },
                )
            elif guide_id:
                conn.execute(
                    text("""
                        INSERT INTO notification_preferences
                            (guide_id, event_type, email_enabled, portal_enabled, updated_at)
                        VALUES
                            (:guide_id, :event_type, :email_enabled, :portal_enabled, NOW())
                        ON CONFLICT (guide_id, event_type)
                        DO UPDATE SET
                            email_enabled = EXCLUDED.email_enabled,
                            portal_enabled = EXCLUDED.portal_enabled,
                            updated_at = NOW()
                    """),
                    {
                        "guide_id": guide_id,
                        "event_type": event_type,
                        "email_enabled": email_enabled,
                        "portal_enabled": portal_enabled,
                    },
                )

        conn.commit()
        return {"success": True, "updated": len(preferences)}

    except Exception as e:
        return handle_domain_exception(e)


@router.post("/retry-failed")
def retry_failed_notifications(
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Retry all failed email notifications (admin only)."""
    try:
        if current_user.get("role") != "admin":
            return {"error": "Admin access required"}, 403

        rows = conn.execute(
            text("""
                SELECT id FROM notifications
                WHERE status = 'FAILED'
                  AND channel = 'EMAIL'
                  AND retry_count < 3
                ORDER BY created_at ASC
                LIMIT 100
            """)
        ).fetchall()

        retried_count = 0
        for row in rows:
            if notification_service.retry_failed_email_notification(conn, row[0]):
                retried_count += 1

        conn.commit()

        return {
            "success": True,
            "total_failed": len(rows),
            "retried": retried_count,
        }

    except Exception as e:
        return handle_domain_exception(e)


@router.post("/test-email")
def test_email_endpoint(
    to_email: str = Query(..., description="Email address to send test to"),
    template_type: str = Query("system", description="Template type: system, guide_assignment, admin_alert"),
):
    """Test endpoint to send email notifications (development only).

    This endpoint helps verify email delivery and template rendering.
    """
    from datetime import datetime

    from ..services.email import send_email
    from ..services.notification_templates import (
        guide_assigned_template,
        schedule_unassignable_admin_template,
    )

    logger.info(f"🧪 Test email endpoint called: to={to_email}, template={template_type}")

    try:
        if template_type == "system":
            # Simple system test email
            subject = "✅ Oceanarium Notification System - Test Email"
            text_body = "This is a test email from the Oceanarium notification system."
            html_body = """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0077B6;">✅ System Test Email</h2>
    <p>This is a <strong>test email</strong> from the Oceanarium notification system.</p>
    <div style="background-color: #D4EDDA; border-left: 4px solid #28A745; padding: 15px; margin: 20px 0;">
      <p style="margin: 0; color: #155724;"><strong>✅ Email System:</strong> Operational</p>
    </div>
    <p>
      <a href="http://localhost:5173"
         style="display: inline-block; background-color: #0077B6; color: white;
                padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
        Open Portal
      </a>
    </p>
  </div>
</body>
</html>"""

        elif template_type == "guide_assignment":
            # Test guide assignment template
            schedule = {
                "id": 42,
                "tour_name": "Ocean Discovery Tour",
                "language_code": "en",
                "event_start_datetime": datetime(2026, 3, 15, 10, 0),
                "ticket_count": 8,
            }
            subject, text_body, html_body, _, _ = guide_assigned_template(
                schedule=schedule, guide_name="Test Guide", assignment_type="AUTO"
            )

        elif template_type == "admin_alert":
            # Test admin urgent alert template
            schedule = {
                "id": 99,
                "tour_name": "Deep Sea Adventure",
                "language_code": "es",
                "event_start_datetime": datetime(2026, 3, 20, 14, 30),
                "ticket_count": 12,
            }
            reasons = ["No guides available for Spanish", "All guides fully booked"]
            subject, text_body, html_body, _, _ = schedule_unassignable_admin_template(
                schedule=schedule, reasons=reasons, attempted_guides_count=5
            )

        else:
            return {"error": f"Unknown template type: {template_type}"}

        # Send the email
        logger.info(f"📧 Sending test email: {subject}")
        result = send_email(to_email=to_email, subject=subject, body_text=text_body, body_html=html_body)

        if result:
            logger.info(f"✅ Test email sent successfully to {to_email}")
            return {
                "success": True,
                "message": f"Test email sent to {to_email}",
                "subject": subject,
                "template_type": template_type,
            }
        else:
            logger.error(f"❌ Failed to send test email to {to_email}")
            return {"success": False, "error": "Failed to send email - check backend logs for details"}

    except Exception as e:
        logger.error(f"❌ Test email endpoint error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


@router.post("/guide-assigned")
def trigger_guide_assigned_notification(
    body: GuideAssignedRequest,
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Trigger guide assignment notification (FR-1).

    Sends notifications to assigned guide and all admins via EMAIL + PORTAL.
    Respects user notification preferences.
    """
    logger.info(
        f"🔔 Triggering guide assigned notification: schedule={body.schedule_id}, "
        f"guide={body.guide_id}, type={body.assignment_type}"
    )

    try:
        # Call existing notification service
        notification_service.notify_guide_assignment(conn, body.schedule_id, body.guide_id, body.assignment_type)
        conn.commit()

        logger.info("✅ Guide assigned notification triggered successfully")

        # Return success response
        return {
            "success": True,
            "event_type": "GUIDE_ASSIGNED",
            "schedule_id": body.schedule_id,
            "guide_id": body.guide_id,
            "assignment_type": body.assignment_type,
            "message": "Notification sent for guide assignment",
        }
    except Exception as e:
        logger.error(f"❌ Failed to trigger guide assigned notification: {e}")
        return handle_domain_exception(e)


@router.post("/guide-unassigned")
def trigger_guide_unassigned_notification(
    body: GuideUnassignedRequest,
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Trigger guide unassignment notification (FR-2).

    Sends notifications to unassigned guide and all admins.
    """
    logger.info(
        f"🔔 Triggering guide unassigned notification: schedule={body.schedule_id}, "
        f"guide={body.guide_id}, reason={body.reason}"
    )

    try:
        notification_service.notify_guide_unassignment(conn, body.schedule_id, body.guide_id, body.reason)
        conn.commit()

        logger.info("✅ Guide unassigned notification triggered successfully")

        return {
            "success": True,
            "event_type": "GUIDE_UNASSIGNED",
            "schedule_id": body.schedule_id,
            "guide_id": body.guide_id,
            "replacement_guide_id": body.replacement_guide_id,
            "reason": body.reason,
            "message": "Notification sent for guide unassignment",
        }
    except Exception as e:
        logger.error(f"❌ Failed to trigger guide unassigned notification: {e}")
        return handle_domain_exception(e)


@router.post("/schedule-unassignable")
def trigger_schedule_unassignable_notification(
    body: ScheduleUnassignableRequest,
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Trigger URGENT unassignable schedule notification (FR-5).

    Sends urgent notifications to all admins only.
    Priority: URGENT, Action Required: True
    """
    logger.info(f"🚨 Triggering URGENT unassignable notification: schedule={body.schedule_id}, reasons={body.reasons}")

    try:
        notification_service.notify_schedule_unassignable(conn, body.schedule_id, body.reasons)
        conn.commit()

        logger.info("✅ Schedule unassignable notification triggered successfully")

        return {
            "success": True,
            "event_type": "SCHEDULE_UNASSIGNABLE",
            "schedule_id": body.schedule_id,
            "priority": "urgent",
            "reasons": body.reasons,
            "attempted_guides_count": body.attempted_guides_count,
            "message": "Urgent notification sent to admins",
        }
    except Exception as e:
        logger.error(f"❌ Failed to trigger unassignable notification: {e}")
        return handle_domain_exception(e)


@router.post("/schedule-changed")
def trigger_schedule_changed_notification(
    body: ScheduleChangedRequest,
    conn=Depends(get_db),
    current_user=Depends(require_resolved_user),
):
    """Trigger schedule change notification (FR-3, FR-4).

    Covers:
    - Reservation cancellations (RESERVATION_CANCELLED)
    - Reservation moves (RESERVATION_MOVED)
    - Schedule modifications (SCHEDULE_MODIFIED)
    """
    logger.info(f"🔔 Triggering schedule changed notification: schedule={body.schedule_id}, type={body.change_type}")

    try:
        notification_service.notify_schedule_change(
            conn, body.schedule_id, body.change_type, body.change_details, body.affected_guide_id
        )
        conn.commit()

        logger.info("✅ Schedule changed notification triggered successfully")

        return {
            "success": True,
            "event_type": "SCHEDULE_CHANGED",
            "schedule_id": body.schedule_id,
            "change_type": body.change_type,
            "affected_guide_id": body.affected_guide_id,
            "message": "Notification sent for schedule change",
        }
    except Exception as e:
        logger.error(f"❌ Failed to trigger schedule changed notification: {e}")
        return handle_domain_exception(e)
