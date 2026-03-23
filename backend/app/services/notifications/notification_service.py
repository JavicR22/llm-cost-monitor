"""
Notification service — orchestrates sending alerts to configured channels.

Flow per alert event:
  1. Load active email channels for the org
  2. Decrypt config (Fernet) → {"email": "user@example.com"}
  3. Send via email_sender
  4. Mark AlertEvent.notification_sent = True
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionFactory
from app.models.alert import AlertEvent
from app.repositories.notification_channel_repo import get_active_channels
from app.services.notifications.email_sender import build_alert_email, send_email
from app.services.security.key_vault import get_key_vault

log = structlog.get_logger()


async def notify_alert_event(
    org_id: uuid.UUID,
    event: AlertEvent,
) -> None:
    """
    Background-safe: send notifications for a triggered alert event.
    Opens its own DB session. Swallows all errors — never blocks callers.
    """
    try:
        async with AsyncSessionFactory() as db:
            await _dispatch(db, org_id, event)
    except Exception:
        log.exception("notify_alert_event_failed", org_id=str(org_id), event_id=str(event.id))


async def _dispatch(
    db: AsyncSession,
    org_id: uuid.UUID,
    event: AlertEvent,
) -> None:
    email_channels = await get_active_channels(db, org_id, channel_type="email")
    if not email_channels:
        return

    vault = get_key_vault()
    subject, html = build_alert_email(
        severity=event.severity,
        alert_type=event.type,
        message=event.message,
    )

    sent_any = False
    for channel in email_channels:
        try:
            config = json.loads(vault.decrypt(channel.config_encrypted))
            to_email: str = config["email"]
        except Exception:
            log.error(
                "notification_channel_decrypt_failed",
                channel_id=str(channel.id),
                org_id=str(org_id),
            )
            continue

        ok = await send_email(to=to_email, subject=subject, html=html)
        if ok:
            sent_any = True

    if sent_any:
        event.notification_sent = True
        await db.commit()
