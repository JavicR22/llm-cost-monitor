"""
Email sender via Resend REST API.

Uses httpx (already a dependency) — no extra SDK needed.
If RESEND_API_KEY is empty, send() is a no-op (safe in dev/test).
"""
from __future__ import annotations

import structlog
import httpx

from app.core.config import settings

log = structlog.get_logger()

_RESEND_URL = "https://api.resend.com/emails"


async def send_email(
    *,
    to: str,
    subject: str,
    html: str,
) -> bool:
    """
    Send an email via Resend.

    Returns True on success, False on failure (never raises).
    No-op if RESEND_API_KEY is not configured.
    """
    if not settings.RESEND_API_KEY:
        log.debug("email_skipped_no_api_key", to=to, subject=subject)
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                _RESEND_URL,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.NOTIFICATIONS_FROM_EMAIL,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            response.raise_for_status()
            log.info("email_sent", to=to, subject=subject)
            return True

    except httpx.HTTPStatusError as exc:
        log.error(
            "email_send_failed",
            to=to,
            subject=subject,
            status_code=exc.response.status_code,
            body=exc.response.text[:200],
        )
        return False
    except Exception:
        log.exception("email_send_error", to=to, subject=subject)
        return False


def build_alert_email(*, severity: str, alert_type: str, message: str) -> tuple[str, str]:
    """
    Build subject + HTML body for an alert event email.
    Returns (subject, html).
    """
    severity_label = severity.upper()
    subject = f"[LLM Cost Monitor] {severity_label}: {alert_type.replace('_', ' ').title()}"

    color = {"critical": "#dc2626", "warning": "#d97706", "info": "#2563eb"}.get(severity, "#6b7280")

    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
      <div style="background:{color};padding:16px 24px;border-radius:8px 8px 0 0">
        <h2 style="color:#fff;margin:0">{severity_label} Alert</h2>
      </div>
      <div style="border:1px solid #e5e7eb;border-top:none;padding:24px;border-radius:0 0 8px 8px">
        <p style="font-size:16px;color:#111">{message}</p>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0">
        <p style="color:#6b7280;font-size:13px">
          Log in to your dashboard to review and manage alerts.
        </p>
      </div>
    </div>
    """
    return subject, html
