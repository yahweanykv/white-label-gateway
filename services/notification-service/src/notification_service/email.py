"""Email delivery via SMTP."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import aiosmtplib
from shared.utils.logger import setup_logger

logger = setup_logger(__name__)


async def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    use_tls: bool = True,
) -> tuple[bool, Optional[str]]:
    """
    Send email via SMTP.

    Args:
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
        from_email: From email address
        to_email: To email address
        subject: Email subject
        body: Email body
        use_tls: Use TLS encryption

    Returns:
        Tuple of (success, error_message)
    """
    try:
        message = MIMEMultipart("alternative")
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = subject

        # Add body
        text_part = MIMEText(body, "plain")
        message.attach(text_part)

        # Send email
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user if smtp_user else None,
            password=smtp_password if smtp_password else None,
            use_tls=use_tls,
            start_tls=use_tls,
        )

        logger.info(f"Email sent successfully to {to_email}")
        return True, None

    except aiosmtplib.SMTPException as e:
        error_msg = f"SMTP error sending email to {to_email}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error sending email to {to_email}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
