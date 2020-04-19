from email.message import EmailMessage
import logging
import mimetypes
import pathlib
import smtplib
import ssl
from typing import List, Optional, Union

from . import _config, _errors

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, config: _config.Config) -> None:
        self._config = config

    def problem_detected_callback(
        self, stream_name: str, matcher_name: str, sample_path: pathlib.Path
    ) -> None:
        stream_config = self._config.stream_config(stream_name)
        logger.warning(
            f"Stream '{stream_name!s}' has been flagged by {matcher_name} for "
            f"{stream_config.timeout()} second(s)"
        )

        _send_notification_sms(stream_name, stream_config)
        _send_notification_email(stream_name, stream_config, sample_path)


def _send_notification_email(
    stream_name: str, stream_config: _config.StreamConfig, sample_path: pathlib.Path
) -> None:
    subject = f"Stream Monitor: problem detected on {stream_name}"

    timeout = stream_config.timeout()
    message = (
        f"Hello,\n\n"
        f"Stream Monitor has detected an issue on stream '{stream_name!s}' "
        f"for {timeout} second(s). Please listen to the attached audio sample "
        f"to confirm and take appropriate action. "
    )

    preceding_duration = stream_config.preceding_duration()
    if preceding_duration > 0:
        message += (
            f"Note that the sample begins with the last {preceding_duration} "
            f"seconds of audio before the problem was detected, followed by "
            f"the {timeout} seconds of audio considered problematic. "
        )

    message += (
        f"You won't be notified again for {stream_config.cooldown()} "
        f"second(s).\n\n"
        f"Thanks for using Stream Monitor!"
    )

    _send_email(
        stream_config.smtp_server(),
        stream_config.smtp_server_port(),
        stream_config.smtp_login(),
        stream_config.smtp_password(),
        stream_config.from_email(),
        stream_config.to_emails(),
        subject,
        message,
        sample_path,
    )


def _send_notification_sms(
    stream_name: str, stream_config: _config.StreamConfig
) -> None:
    if not stream_config.to_sms_emails():
        return

    message = (
        f"Stream Monitor has detected an issue on stream '{stream_name!s}' "
        f"for {stream_config.timeout()} second(s). Check your email for more "
        "information."
    )

    _send_email(
        stream_config.smtp_server(),
        stream_config.smtp_server_port(),
        stream_config.smtp_login(),
        stream_config.smtp_password(),
        stream_config.from_email(),
        stream_config.to_sms_emails(),
        None,
        message,
        None,
    )


def _send_email(
    smtp_server: str,
    smtp_server_port: int,
    smtp_login: str,
    smtp_password: str,
    from_email: str,
    to_emails: List[str],
    subject: Optional[str],
    message: str,
    attachment: Optional[pathlib.Path],
) -> None:
    email_message = EmailMessage()
    email_message["Subject"] = subject
    email_message["From"] = from_email
    email_message["To"] = ", ".join(to_emails)
    email_message.set_content(message)

    if attachment:
        mime_type = mimetypes.guess_type(str(attachment))
        if not mime_type or len(mime_type) != 2 or mime_type[0] is None:
            raise _errors.EmailAttachmentMimeTypeError(attachment)
        maintype, subtype = str(mime_type[0]).split("/")
        if not maintype or not subtype:
            raise _errors.EmailAttachmentMimeTypeError(attachment)

        with open(attachment, "rb") as f:
            email_message.add_attachment(
                f.read(), filename=attachment.name, maintype=maintype, subtype=subtype
            )

    try:
        server: Union[smtplib.SMTP_SSL, smtplib.SMTP] = smtplib.SMTP_SSL(
            smtp_server, smtp_server_port
        )
    except ssl.SSLError as e:
        if getattr(e, "reason", None) != "WRONG_VERSION_NUMBER":
            raise

        # Fall back to SSLv2 and SSLv3 (some servers still require this, sadly)
        server = smtplib.SMTP(smtp_server, smtp_server_port)
        server.ehlo()
        server.starttls(context=ssl.SSLContext(ssl.PROTOCOL_SSLv23))
        server.ehlo()

    server.login(smtp_login, smtp_password)
    server.send_message(email_message)
    server.quit()
