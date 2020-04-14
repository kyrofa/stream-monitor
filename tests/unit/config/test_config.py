import pathlib
import textwrap

import pytest

from stream_monitor import _config
from stream_monitor._config import _errors


def test_config(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream1]
            url = foo
            [stream2]
            url = bar
            """
        )
    )

    config = _config.Config(file_path)
    stream_names = config.stream_names()
    assert len(stream_names) == 2
    assert set(stream_names) == {"stream1", "stream2"}

    stream1_config = config.stream_config("stream1")
    assert stream1_config.url() == "foo"

    stream2_config = config.stream_config("stream2")
    assert stream2_config.url() == "bar"


def test_config_threshold(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            """
        )
    )

    # Test default threshold
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.threshold() == 0.7

    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            threshold = 20.5
            """
        )
    )

    # Test configured threshold
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.threshold() == 20.5


def test_config_preceding_duration(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            """
        )
    )

    # Test default preceding_duration
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.preceding_duration() == 30.0

    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            preceding_duration = 20.5
            """
        )
    )

    # Test configured preceding_duration
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.preceding_duration() == 20.5


def test_config_timeout(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            """
        )
    )

    # Test default timeout
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.timeout() == 60.0

    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            timeout = 20.5
            """
        )
    )

    # Test configured timeout
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.timeout() == 20.5


def test_config_cooldown(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            """
        )
    )

    # Test default cooldown
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.cooldown() == 3600.0

    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            cooldown = 20.5
            """
        )
    )

    # Test configured cooldown
    config = _config.Config(file_path)
    stream_config = config.stream_config("stream")
    assert stream_config.cooldown() == 20.5


def test_config_missing_smtp_keys(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream1]
            url = bar
            """
        ),
        smtp_settings=False,
    )

    with pytest.raises(_errors.InvalidStreamConfigError) as error:
        _config.Config(file_path)

    assert (
        f"Error processing config file '{file_path!s}': improper configuration "
        "detected for stream 'stream1': the following keys are missing: "
        "'from_email', 'smtp_login', 'smtp_password', 'smtp_server', "
        "'smtp_server_port', and 'to_emails'" in str(error.value)
    )


def test_config_no_such_name(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream1]
            url = bar
            """
        )
    )

    config = _config.Config(file_path)
    with pytest.raises(_errors.NoSuchStreamError) as error:
        config.stream_config("stream2")

    assert f"Stream with name 'stream2' does not exist" in str(error.value)


def test_no_config_file(config_file):
    file_path = pathlib.Path("/foo/bar/baz/nonexistent")

    with pytest.raises(_errors.NoSuchConfigurationFileError) as error:
        _config.Config(file_path)

    assert f"Error processing config file '{file_path!s}': no such file exists" in str(
        error.value
    )


def test_invalid_config(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stre
            """
        ),
        smtp_settings=False,
    )

    with pytest.raises(_errors.ConfigFileParsingError) as error:
        _config.Config(file_path)

    assert (
        f"Error processing config file '{file_path!s}': File contains no section headers"
        in str(error.value)
    )


def test_invalid_config_no_url(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            """
        )
    )

    with pytest.raises(_errors.InvalidStreamConfigError) as error:
        _config.Config(file_path)

    assert (
        f"Error processing config file '{file_path!s}': improper configuration "
        "detected for stream 'stream': the following key is missing: 'url'"
        in str(error.value)
    )


def test_invalid_config_unexpected_key(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            bar = baz
            """
        )
    )

    with pytest.raises(_errors.InvalidStreamConfigError) as error:
        _config.Config(file_path)

    assert (
        f"Error processing config file '{file_path!s}': improper configuration "
        "detected for stream 'stream': the following key is unexpected: 'bar'"
        in str(error.value)
    )

    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            bar = baz
            qux = quux
            """
        )
    )

    with pytest.raises(_errors.InvalidStreamConfigError) as error:
        _config.Config(file_path)

    assert (
        f"Error processing config file '{file_path!s}': improper configuration "
        "detected for stream 'stream': the following keys are unexpected: 'bar' "
        "and 'qux'" in str(error.value)
    )


def test_multiple_to_email_addresses(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            to_emails = ["email1@example.com", "email2@example.com"]
            """
        )
    )

    config = _config.Config(file_path)
    assert set(config.stream_config("stream").to_emails()) == {
        "email1@example.com",
        "email2@example.com",
    }


def test_invalid_to_emails(config_file):
    file_path = config_file(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            to_emails = email1@example.com
            """
        )
    )

    with pytest.raises(_errors.InvalidStreamConfigError) as error:
        _config.Config(file_path)

    assert f"Error processing config file '{file_path!s}': improper configuration "
    "detected for stream 'stream': invalid 'to_emails': email1@example.com. It "
    'should be a list with quoted items, e.g. ["email@example.com"]' in str(error.value)
