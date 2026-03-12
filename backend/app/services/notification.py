from __future__ import annotations

from sqlalchemy import text


def list_notifications(conn):
    result = conn.execute(text("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10"))
    columns = result.keys()
    rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows


def create_notification(
    conn,
    event_type: str,
    schedule_id: int,
    guide_id: int | None,
    message: str,
) -> None:
    conn.execute(
        text(
            """
            INSERT INTO notifications
                (event_type, schedule_id, guide_id, channel, status, message)
            VALUES
                (:event_type, :schedule_id, :guide_id, 'PORTAL', 'SENT', :message)
            """
        ),
        {
            "event_type": event_type,
            "schedule_id": schedule_id,
            "guide_id": guide_id,
            "message": message,
        },
    )
