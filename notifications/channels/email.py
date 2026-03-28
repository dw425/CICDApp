"""Email notification channel — sends alerts via SMTP."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def send_email(smtp_host: str, smtp_port: int, sender: str, recipients: list[str],
               subject: str, body: str, password: str = "",
               use_tls: bool = True) -> bool:
    """Send an email notification via SMTP.

    Args:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port (587 for TLS, 465 for SSL)
        sender: From email address
        recipients: List of recipient email addresses
        subject: Email subject
        body: Email body (HTML supported)
        password: SMTP password (if authentication required)
        use_tls: Whether to use STARTTLS

    Returns: True if sent successfully
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4B7BF5;">CI/CD Maturity Intelligence</h2>
            <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 4px solid #4B7BF5;">
                {body}
            </div>
            <p style="color: #999; font-size: 12px; margin-top: 20px;">
                This is an automated notification from CI/CD Maturity Intelligence.
            </p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            if use_tls:
                server.starttls()

        if password:
            server.login(sender, password)

        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
