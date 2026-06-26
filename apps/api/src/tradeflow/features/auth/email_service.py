from __future__ import annotations

import smtplib
from email.message import EmailMessage

from tradeflow.core.config import Settings
from tradeflow.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Sends transactional auth emails via SMTP or logs in development."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification_email(self, email: str, token: str) -> None:
        link = f"{self._settings.frontend_url}/verify-email?token={token}"
        subject = "Verify your TradeFlow AI email"
        body = (
            f"Welcome to TradeFlow AI.\n\n"
            f"Verify your email by visiting:\n{link}\n\n"
            f"This link expires in 24 hours."
        )
        await self._send(email, subject, body)

    async def send_password_reset_email(self, email: str, token: str) -> None:
        link = f"{self._settings.frontend_url}/reset-password?token={token}"
        subject = "Reset your TradeFlow AI password"
        body = (
            f"Reset your password by visiting:\n{link}\n\n"
            f"This link expires in 1 hour. If you did not request this, ignore this email."
        )
        await self._send(email, subject, body)

    async def _send(self, to_email: str, subject: str, body: str) -> None:
        if not self._settings.smtp_host:
            logger.info(
                "email_dev_mode",
                to=to_email,
                subject=subject,
                body=body,
            )
            return

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._settings.smtp_from_email
        message["To"] = to_email
        message.set_content(body)

        with smtplib.SMTP(
            self._settings.smtp_host,
            self._settings.smtp_port,
        ) as server:
            server.starttls()
            if self._settings.smtp_user and self._settings.smtp_password:
                server.login(self._settings.smtp_user, self._settings.smtp_password)
            server.send_message(message)

        logger.info("email_sent", to=to_email, subject=subject)
