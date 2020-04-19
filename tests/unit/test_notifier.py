import ssl
import textwrap

from stream_monitor import _notifier

import mock


def test_notifier_sends_email(config, test_data_normal_path):
    notifier = _notifier.Notifier(
        config(
            textwrap.dedent(
                f"""\
                [stream]
                url = foo
                smtp_server = smtp.example.com
                smtp_server_port = 25
                smtp_login = login
                smtp_password = password
                from_email = from@example.com
                to_emails = ["to@example.com"]
                """
            ),
            smtp_settings=False,
        )
    )

    with mock.patch(
        "stream_monitor._notifier.EmailMessage", autospec=True
    ) as mock_email_message:
        with mock.patch(
            "stream_monitor._notifier.smtplib.SMTP_SSL", autospec=True
        ) as mock_smtp:
            notifier.problem_detected_callback("stream", "foo", test_data_normal_path)

    assert len(mock_email_message.mock_calls) == 6
    mock_email_message.assert_has_calls(
        [
            mock.call(),
            mock.call().__setitem__(
                "Subject", "Stream Monitor: problem detected on stream"
            ),
            mock.call().__setitem__("From", "from@example.com"),
            mock.call().__setitem__("To", "to@example.com"),
            mock.call().set_content(mock.ANY),
            mock.call().add_attachment(
                mock.ANY,
                filename=test_data_normal_path.name,
                maintype="audio",
                subtype="mpeg",
            ),
        ]
    )

    assert len(mock_smtp.mock_calls) == 4
    mock_smtp.assert_has_calls(
        [
            mock.call("smtp.example.com", 25),
            mock.call().login("login", "password"),
            mock.call().send_message(mock_email_message()),
            mock.call().quit(),
        ]
    )


def test_notifier_ssl_v3(config, test_data_normal_path):
    notifier = _notifier.Notifier(
        config(
            textwrap.dedent(
                f"""\
                [stream]
                url = foo
                smtp_server = smtp.example.com
                smtp_server_port = 25
                smtp_login = login
                smtp_password = password
                from_email = from@example.com
                to_emails = ["to@example.com"]
                """
            ),
            smtp_settings=False,
        )
    )

    error = ssl.SSLError()
    error.reason = "WRONG_VERSION_NUMBER"
    with mock.patch(
        "stream_monitor._notifier.EmailMessage", autospec=True
    ) as mock_email_message:
        with mock.patch(
            "stream_monitor._notifier.smtplib.SMTP_SSL",
            autospec=True,
            side_effect=error,
        ):
            with mock.patch(
                "stream_monitor._notifier.smtplib.SMTP", autospec=True
            ) as mock_smtp:
                notifier.problem_detected_callback(
                    "stream", "foo", test_data_normal_path
                )

    assert len(mock_email_message.mock_calls) == 6
    mock_email_message.assert_has_calls(
        [
            mock.call(),
            mock.call().__setitem__(
                "Subject", "Stream Monitor: problem detected on stream"
            ),
            mock.call().__setitem__("From", "from@example.com"),
            mock.call().__setitem__("To", "to@example.com"),
            mock.call().set_content(mock.ANY),
            mock.call().add_attachment(
                mock.ANY,
                filename=test_data_normal_path.name,
                maintype="audio",
                subtype="mpeg",
            ),
        ]
    )
    assert len(mock_smtp.mock_calls) == 7
    mock_smtp.assert_has_calls(
        [
            mock.call("smtp.example.com", 25),
            mock.call().ehlo(),
            mock.call().starttls(context=mock.ANY),
            mock.call().ehlo(),
            mock.call().login("login", "password"),
            mock.call().send_message(mock_email_message()),
            mock.call().quit(),
        ]
    )


def test_notifier_sends_sms(config, test_data_normal_path):
    notifier = _notifier.Notifier(
        config(
            textwrap.dedent(
                f"""\
                [stream]
                url = foo
                smtp_server = smtp.example.com
                smtp_server_port = 25
                smtp_login = login
                smtp_password = password
                from_email = from@example.com
                to_emails = ["to@example.com"]
                to_sms_emails = ["1234567890@example.com"]
                """
            ),
            smtp_settings=False,
        )
    )

    with mock.patch(
        "stream_monitor._notifier._send_email", autospec=True
    ) as mock_send_email:
        notifier.problem_detected_callback("stream", "foo", test_data_normal_path)

    mock_send_email.assert_has_calls(
        [
            mock.call(
                "smtp.example.com",
                25,
                "login",
                "password",
                "from@example.com",
                ["1234567890@example.com"],
                None,
                mock.ANY,
                None,
            ),
            mock.call(
                "smtp.example.com",
                25,
                "login",
                "password",
                "from@example.com",
                ["to@example.com"],
                "Stream Monitor: problem detected on stream",
                mock.ANY,
                mock.ANY,
            ),
        ],
        any_order=True,
    )
