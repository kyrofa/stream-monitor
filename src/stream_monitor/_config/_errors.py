import configparser
import pathlib
from typing import Collection, Iterable

from .. import _errors


class ConfigurationError(_errors.StreamMonitorError):
    """Base class for configuration errors."""


class InvalidConfigError(ConfigurationError):
    def __init__(self, config_file_path: pathlib.Path, message: str) -> None:
        self.config_file_path = config_file_path
        super().__init__(
            f"Error processing config file '{config_file_path!s}': {message}"
        )


class InvalidStreamConfigError(InvalidConfigError):
    def __init__(
        self, config_file_path: pathlib.Path, stream_name: str, message: str
    ) -> None:
        self.config_file_path = config_file_path
        super().__init__(
            config_file_path,
            f"improper configuration detected for stream {stream_name!r}: {message}",
        )


class NoSuchConfigurationFileError(InvalidConfigError):
    def __init__(self, config_file_path: pathlib.Path) -> None:
        super().__init__(config_file_path, "no such file exists")


class StreamConfigMissingKeysError(ConfigurationError):
    def __init__(self, keys: Collection[str]) -> None:
        self.keys = keys

        phrase = "key is"
        if len(keys) > 1:
            phrase = "keys are"
        super().__init__(
            f"the following {phrase} missing: {_humanize_iterable(keys, 'and')}"
        )


class StreamConfigUnexpectedKeysError(ConfigurationError):
    def __init__(self, keys: Collection[str]) -> None:
        self.keys = keys

        phrase = "key is"
        if len(keys) > 1:
            phrase = "keys are"
        super().__init__(
            f"the following {phrase} unexpected: {_humanize_iterable(keys, 'and')}"
        )


class StreamConfigEmailsFormatError(ConfigurationError):
    def __init__(self, key: str, to_emails: str) -> None:
        self.key = key
        self.to_emails = to_emails

        super().__init__(
            f"invalid '{key}': {to_emails}. It should be a list with quoted "
            'items, e.g. ["email@example.com"]'
        )


class StreamConfigToEmailsFormatError(StreamConfigEmailsFormatError):
    def __init__(self, to_emails: str) -> None:
        super().__init__("to_emails", to_emails)


class StreamConfigToSmsEmailsFormatError(StreamConfigEmailsFormatError):
    def __init__(self, to_sms_emails: str) -> None:
        super().__init__("to_sms_emails", to_sms_emails)


class ConfigFileParsingError(InvalidConfigError):
    def __init__(
        self, config_file_path: pathlib.Path, error: configparser.Error
    ) -> None:
        self.error = error
        super().__init__(config_file_path, str(error))


class NoSuchStreamError(ConfigurationError):
    def __init__(self, stream_name: str) -> None:
        self.stream_name = stream_name
        super().__init__(f"Stream with name {stream_name!r} does not exist")


def _humanize_iterable(items: Iterable[str], conjunction: str) -> str:
    if not items:
        return ""

    quoted_items = [f"'{item!s}'" for item in sorted(items)]
    if len(quoted_items) == 1:
        return quoted_items[0]

    humanized = ", ".join(quoted_items[:-1])

    if len(quoted_items) > 2:
        humanized += ","

    return f"{humanized} {conjunction} {quoted_items[-1]}"
