"""Email service for sending verification and notification emails."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP or console logging."""

    def __init__(self):
        self.is_configured = settings.is_email_configured

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """
        Send an email. Falls back to console logging if SMTP not configured.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            html_body: HTML content of the email.
            text_body: Plain text fallback (optional).

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.is_configured:
            # Development mode: log to console
            logger.info("=" * 60)
            logger.info("EMAIL (dev mode - not sent)")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 60)
            logger.info(text_body or html_body)
            logger.info("=" * 60)
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg["To"] = to_email

            # Attach plain text version
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))

            # Attach HTML version
            msg.attach(MIMEText(html_body, "html"))

            # Send via SMTP
            if settings.smtp_use_tls:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)

            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_verification_email(
        self,
        to_email: str,
        verification_url: str,
        display_name: str | None = None,
    ) -> bool:
        """
        Send email verification link.

        Args:
            to_email: Recipient email address.
            verification_url: Full URL to verify email.
            display_name: User's display name (optional).

        Returns:
            True if sent successfully.
        """
        name = display_name or to_email.split("@")[0]

        subject = "Verify your email - Stupid Chat Bot"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #4f46e5;
            color: white !important;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
        }}
        .button:hover {{ background-color: #4338ca; }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }}
        .link {{ word-break: break-all; color: #4f46e5; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Verify Your Email</h1>
        </div>

        <p>Hi {name},</p>

        <p>Thanks for signing up for Stupid Chat Bot!
           Please verify your email address by clicking the button below:</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" class="button">Verify Email</a>
        </p>

        <p>Or copy and paste this link into your browser:</p>
        <p class="link">{verification_url}</p>

        <p>This link will expire in {settings.email_verification_token_expire_hours} hours.</p>

        <p>If you didn't create an account, you can safely ignore this email.</p>

        <div class="footer">
            <p>Stupid Chat Bot - A simple, straightforward chat</p>
        </div>
    </div>
</body>
</html>
"""

        text_body = f"""
Hi {name},

Thanks for signing up for Stupid Chat Bot!
Please verify your email address by clicking the link below:

{verification_url}

This link will expire in {settings.email_verification_token_expire_hours} hours.

If you didn't create an account, you can safely ignore this email.

---
Stupid Chat Bot - A simple, straightforward chat
"""

        return await self.send_email(to_email, subject, html_body, text_body)


# Global service instance
email_service = EmailService()
