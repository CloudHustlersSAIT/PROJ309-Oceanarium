"""Email service using Resend.com for transactional emails."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Initialize Resend (lazy import to avoid errors if not installed)
try:
    import resend

    resend.api_key = os.getenv("RESEND_API_KEY")
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
except ImportError:
    logger.warning("Resend not installed - email functionality disabled")
    EMAIL_ENABLED = False

EMAIL_FROM = os.getenv("EMAIL_FROM", "notifications@oceanarium.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Oceanarium Scheduling")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> bool:
    """Send an email using Resend.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body_text: Plain text email body (fallback)
        body_html: HTML email body (optional, recommended)

    Returns:
        True if email sent successfully, False otherwise
    """
    logger.info(f"📧 send_email() called - To: {to_email}, Subject: {subject}")
    logger.info(f"   EMAIL_ENABLED: {EMAIL_ENABLED}")
    logger.info(f"   EMAIL_FROM: {EMAIL_FROM}")
    logger.info(f"   EMAIL_FROM_NAME: {EMAIL_FROM_NAME}")
    logger.info(f"   Has HTML: {body_html is not None}")
    
    if not EMAIL_ENABLED:
        logger.warning(f"⚠️  Email disabled - would have sent to {to_email}: {subject}")
        return True  # Consider it successful for testing

    if not to_email or "@" not in to_email:
        logger.error(f"❌ Invalid email address: {to_email}")
        return False

    try:
        params = {
            "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
            "to": [to_email],
            "subject": subject,
            "text": body_text,
        }

        if body_html:
            params["html"] = body_html
            logger.info(f"   HTML body length: {len(body_html)} chars")

        logger.info(f"🚀 Sending email via Resend API...")
        response = resend.Emails.send(params)
        email_id = response.get('id', 'unknown')
        logger.info(f"✅ Email sent successfully!")
        logger.info(f"   Resend Email ID: {email_id}")
        logger.info(f"   To: {to_email}")
        logger.info(f"   Subject: {subject}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}")
        logger.error(f"   Error: {e}")
        logger.error(f"   Subject: {subject}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return False
