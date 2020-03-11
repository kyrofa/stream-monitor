from email.message import EmailMessage
import logging
import mimetypes
import pathlib
import smtplib
import ssl
from typing import List, Union

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

        message = (
            f"Hello,\n\n"
            f"Stream Monitor has detected an issue on stream '{stream_name!s}' "
            f"for {stream_config.timeout()} second(s). Please listen to the "
            f"attached audio sample to confirm and take appropriate action. "
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
            f"Stream Monitor: problem detected on {stream_name}",
            message,
            sample_path,
        )


def _send_email(
    smtp_server: str,
    smtp_server_port: int,
    smtp_login: str,
    smtp_password: str,
    from_email: str,
    to_emails: List[str],
    subject: str,
    message: str,
    attachment: pathlib.Path,
) -> None:
    email_message = EmailMessage()
    email_message["Subject"] = subject
    email_message["From"] = from_email
    email_message["To"] = ", ".join(to_emails)
    email_message.set_content(message)

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
