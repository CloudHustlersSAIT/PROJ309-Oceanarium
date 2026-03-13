"""Notification message templates for schedule events.

Following 2026 best practices: actionable, transparent, and value-first design.
"""

from __future__ import annotations

import os
from datetime import datetime

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _format_datetime(dt: datetime) -> str:
    """Format datetime in human-readable format."""
    return dt.strftime("%B %d, %Y at %I:%M %p")


def _format_date(dt: datetime) -> str:
    """Format date only."""
    return dt.strftime("%B %d, %Y")


def _format_time(dt: datetime) -> str:
    """Format time only."""
    return dt.strftime("%I:%M %p")


def guide_assigned_template(schedule: dict, guide_name: str, assignment_type: str) -> tuple[str, str, str, str, dict]:
    """Template for GUIDE_ASSIGNED event.

    Returns: (subject, text_body, html_body, portal_message, notification_detail)
    """
    tour_name = schedule.get("tour_name", "Unknown Tour")
    language = schedule.get("language_code", "").upper()
    date = _format_date(schedule["event_start_datetime"])
    time = _format_time(schedule["event_start_datetime"])
    ticket_count = schedule.get("ticket_count", 0)
    schedule_id = schedule["id"]

    assignment_note = "automatically assigned" if assignment_type == "AUTO" else "manually assigned by admin"
    assigned_by = "System" if assignment_type == "AUTO" else "Admin"

    # Portal message (short, actionable)
    portal_message = (
        f"New assignment: {tour_name} on {date} at {time} - {ticket_count} {language}-speaking guests confirmed"
    )

    # Email subject
    subject = f"New Assignment: {tour_name} on {date}"

    # Email text body
    text = f"""Hi {guide_name},

You have been {assignment_note} to:

Tour: {tour_name}
Date: {date}
Time: {time}
Language: {language}
Guests: {ticket_count}

View your schedule: {FRONTEND_URL}/schedule/{schedule_id}

This is an automated notification from the Oceanarium Scheduling System.
"""

    # Email HTML body
    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #1C1C1C; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #0077B6;">New Tour Assignment</h2>
      <p>Hi {guide_name},</p>
      <p>You have been <strong>{assignment_note}</strong> to the following tour:</p>
      
      <div style="background-color: #EAF6FD; border-left: 4px solid #0077B6; padding: 15px; margin: 20px 0;">
        <p style="margin: 5px 0;"><strong>Tour:</strong> {tour_name}</p>
        <p style="margin: 5px 0;"><strong>Date:</strong> {date}</p>
        <p style="margin: 5px 0;"><strong>Time:</strong> {time}</p>
        <p style="margin: 5px 0;"><strong>Language:</strong> {language}</p>
        <p style="margin: 5px 0;"><strong>Guests:</strong> {ticket_count}</p>
      </div>
      
      <p>
        <a href="{FRONTEND_URL}/schedule/{schedule_id}" 
           style="display: inline-block; background-color: #0077B6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
          View Schedule
        </a>
      </p>
      
      <p style="color: #666; font-size: 14px; margin-top: 30px;">
        This is an automated notification from the Oceanarium Scheduling System.
      </p>
    </div>
  </body>
</html>
"""

    # Notification detail (full context)
    detail = {
        "title": "New Tour Assignment",
        "tour_name": tour_name,
        "date": date,
        "time": time,
        "language": language,
        "ticket_count": ticket_count,
        "assignment_type": assignment_type,
        "assigned_by": assigned_by,
        "reason": "Matched availability and expertise" if assignment_type == "AUTO" else "Admin manual assignment",
    }

    return subject, text, html, portal_message, detail


def guide_unassigned_template(
    schedule: dict, guide_name: str, reason: str, replacement_guide_name: str = None
) -> tuple[str, str, str, str, dict]:
    """Template for GUIDE_REASSIGNED (unassignment) event.

    Returns: (subject, text_body, html_body, portal_message, notification_detail)
    """
    tour_name = schedule.get("tour_name", "Unknown Tour")
    date = _format_date(schedule["event_start_datetime"])
    time = _format_time(schedule["event_start_datetime"])
    schedule_id = schedule["id"]

    replacement_note = (
        f"Replacement: {replacement_guide_name}" if replacement_guide_name else "Replacement being assigned"
    )

    # Portal message
    portal_message = f"Tour assignment removed: {tour_name} on {date} at {time}. Reason: {reason}. {replacement_note}"

    # Email subject
    subject = f"Assignment Change: {tour_name} on {date}"

    # Email text body
    text = f"""Hi {guide_name},

You have been removed from a tour assignment.

Tour: {tour_name}
Date: {date}
Time: {time}
Reason: {reason}

{f"Replacement Guide: {replacement_guide_name}" if replacement_guide_name else "A replacement guide is being assigned."}

View updated schedule: {FRONTEND_URL}/schedule

This is an automated notification from the Oceanarium Scheduling System.
"""

    # Email HTML body
    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #1C1C1C; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #E63946;">Tour Assignment Change</h2>
      <p>Hi {guide_name},</p>
      <p>You have been <strong>removed</strong> from the following tour assignment:</p>
      
      <div style="background-color: #FFF1F2; border-left: 4px solid #E63946; padding: 15px; margin: 20px 0;">
        <p style="margin: 5px 0;"><strong>Tour:</strong> {tour_name}</p>
        <p style="margin: 5px 0;"><strong>Date:</strong> {date}</p>
        <p style="margin: 5px 0;"><strong>Time:</strong> {time}</p>
        <p style="margin: 5px 0;"><strong>Reason:</strong> {reason}</p>
        {f'<p style="margin: 5px 0;"><strong>Replacement:</strong> {replacement_guide_name}</p>' if replacement_guide_name else ""}
      </div>
      
      <p>
        <a href="{FRONTEND_URL}/schedule" 
           style="display: inline-block; background-color: #0077B6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
          View Your Schedule
        </a>
      </p>
      
      <p style="color: #666; font-size: 14px; margin-top: 30px;">
        This is an automated notification from the Oceanarium Scheduling System.
      </p>
    </div>
  </body>
</html>
"""

    # Notification detail
    detail = {
        "title": "Tour Assignment Removed",
        "tour_name": tour_name,
        "date": date,
        "time": time,
        "removal_reason": reason,
        "replacement_guide": replacement_guide_name or "Being assigned",
    }

    return subject, text, html, portal_message, detail


def schedule_unassignable_admin_template(
    schedule: dict, reasons: list[str], attempted_guides_count: int = 0
) -> tuple[str, str, str, str, dict]:
    """Template for SCHEDULE_UNASSIGNABLE event (admin-only, urgent).

    Returns: (subject, text_body, html_body, portal_message, notification_detail)
    """
    tour_name = schedule.get("tour_name", "Unknown Tour")
    language = schedule.get("language_code", "").upper()
    date = _format_date(schedule["event_start_datetime"])
    time = _format_time(schedule["event_start_datetime"])
    schedule_id = schedule["id"]
    ticket_count = schedule.get("ticket_count", 0)
    reasons_list = ", ".join(reasons)

    # Portal message
    portal_message = f"🚨 Action required: Schedule #{schedule_id} ({tour_name}, {date}) has no available guide. Checked {attempted_guides_count} guides - Constraints failed: {reasons_list}. Manual assignment needed."

    # Email subject
    subject = f"🚨 URGENT: No Guide Available - {tour_name} ({date})"

    # Email text body
    text = f"""URGENT: Manual assignment required!

Schedule #{schedule_id} has no eligible guides.

Tour: {tour_name}
Date: {date}
Time: {time}
Language: {language}
Guests: {ticket_count}
Constraints Failed: {reasons_list}

Action Required: Please manually assign a guide to this schedule.

View schedule: {FRONTEND_URL}/schedule/{schedule_id}
"""

    # Email HTML body
    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #1C1C1C; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #E63946; border-left: 5px solid #E63946; padding-left: 15px;">
        🚨 URGENT: No Guide Available
      </h2>
      <p><strong>Schedule #{schedule_id} requires immediate attention.</strong></p>
      <p>The system was unable to automatically assign a guide to this tour due to constraint failures.</p>
      
      <div style="background-color: #FFF1F2; border: 2px solid #E63946; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 5px 0;"><strong>Tour:</strong> {tour_name}</p>
        <p style="margin: 5px 0;"><strong>Date:</strong> {date}</p>
        <p style="margin: 5px 0;"><strong>Time:</strong> {time}</p>
        <p style="margin: 5px 0;"><strong>Language:</strong> {language}</p>
        <p style="margin: 5px 0;"><strong>Guests:</strong> {ticket_count}</p>
        <p style="margin: 5px 0; color: #E63946;"><strong>Constraints Failed:</strong> {reasons_list}</p>
      </div>
      
      <p style="background-color: #FFF9E6; border-left: 4px solid #FFA500; padding: 10px; margin: 20px 0;">
        <strong>⚠️ Action Required:</strong> Please manually assign a guide to this schedule.
      </p>
      
      <p>
        <a href="{FRONTEND_URL}/schedule/{schedule_id}" 
           style="display: inline-block; background-color: #E63946; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
          Assign Guide Now
        </a>
      </p>
      
      <p style="color: #666; font-size: 14px; margin-top: 30px;">
        This is an automated urgent notification from the Oceanarium Scheduling System.
      </p>
    </div>
  </body>
</html>
"""

    # Notification detail
    detail = {
        "title": "Urgent: Manual Assignment Required",
        "tour_name": tour_name,
        "date": date,
        "time": time,
        "language": language,
        "ticket_count": ticket_count,
        "attempted_guides_count": attempted_guides_count,
        "constraints_failed": reasons,
    }

    return subject, text, html, portal_message, detail


def schedule_changed_admin_template(
    schedule: dict, change_type: str, change_details: str, old_state: dict = None, new_state: dict = None
) -> tuple[str, str, str, str, dict]:
    """Template for general schedule change notifications (admin).

    Returns: (subject, text_body, html_body, portal_message, notification_detail)
    """
    tour_name = schedule.get("tour_name", "Unknown Tour")
    date = _format_date(schedule["event_start_datetime"])
    time = _format_time(schedule["event_start_datetime"])
    schedule_id = schedule["id"]
    guide_name = schedule.get("guide_name", "No guide assigned")
    ticket_count = schedule.get("ticket_count", 0)
    status = schedule.get("status", "UNKNOWN")

    # Portal message
    portal_message = f"Schedule change: {change_type} for {tour_name} on {date}. {change_details}. Current status: {status}, Guide: {guide_name}, Guests: {ticket_count}"

    # Email subject
    subject = f"Schedule Update: {tour_name} on {date}"

    # Email text body
    text = f"""Schedule #{schedule_id} has been updated.

Change Type: {change_type}
Details: {change_details}

Current Schedule State:
- Tour: {tour_name}
- Date: {date}
- Time: {time}
- Guide: {guide_name}
- Guests: {ticket_count}
- Status: {status}

View schedule: {FRONTEND_URL}/schedule/{schedule_id}
"""

    # Email HTML body
    before_after_html = ""
    if old_state and new_state:
        before_after_html = f"""
      <h3 style="color: #0077B6; font-size: 16px;">Before → After:</h3>
      <div style="background-color: #EAF6FD; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 5px; font-weight: bold;">Guide:</td>
            <td style="padding: 5px;">{old_state.get("guide", "N/A")}</td>
            <td style="padding: 5px;">→</td>
            <td style="padding: 5px;">{new_state.get("guide", "N/A")}</td>
          </tr>
          <tr>
            <td style="padding: 5px; font-weight: bold;">Guests:</td>
            <td style="padding: 5px;">{old_state.get("ticket_count", 0)}</td>
            <td style="padding: 5px;">→</td>
            <td style="padding: 5px;">{new_state.get("ticket_count", 0)}</td>
          </tr>
          <tr>
            <td style="padding: 5px; font-weight: bold;">Status:</td>
            <td style="padding: 5px;">{old_state.get("status", "N/A")}</td>
            <td style="padding: 5px;">→</td>
            <td style="padding: 5px;">{new_state.get("status", "N/A")}</td>
          </tr>
        </table>
      </div>
"""

    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #1C1C1C; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #0077B6;">Schedule Change Notification</h2>
      <p>Schedule #{schedule_id} has been updated.</p>
      
      <div style="background-color: #FFF9E6; border-left: 4px solid #FFA500; padding: 15px; margin: 20px 0;">
        <p style="margin: 5px 0;"><strong>Change Type:</strong> {change_type}</p>
        <p style="margin: 5px 0;"><strong>Details:</strong> {change_details}</p>
      </div>
      
      {before_after_html}
      
      <h3 style="color: #0077B6; font-size: 16px;">Current Schedule State:</h3>
      <div style="background-color: #EAF6FD; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 5px 0;"><strong>Tour:</strong> {tour_name}</p>
        <p style="margin: 5px 0;"><strong>Date:</strong> {date}</p>
        <p style="margin: 5px 0;"><strong>Time:</strong> {time}</p>
        <p style="margin: 5px 0;"><strong>Guide:</strong> {guide_name}</p>
        <p style="margin: 5px 0;"><strong>Guests:</strong> {ticket_count}</p>
        <p style="margin: 5px 0;"><strong>Status:</strong> {status}</p>
      </div>
      
      <p>
        <a href="{FRONTEND_URL}/schedule/{schedule_id}" 
           style="display: inline-block; background-color: #0077B6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
          View Schedule
        </a>
      </p>
      
      <p style="color: #666; font-size: 14px; margin-top: 30px;">
        This is an automated notification from the Oceanarium Scheduling System.
      </p>
    </div>
  </body>
</html>
"""

    # Notification detail
    detail = {
        "title": "Schedule Change",
        "tour_name": tour_name,
        "date": date,
        "time": time,
        "change_type": change_type,
        "change_details": change_details,
        "before_state": old_state,
        "after_state": new_state,
    }

    return subject, text, html, portal_message, detail
