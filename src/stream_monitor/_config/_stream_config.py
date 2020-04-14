import configparser
import json
from typing import List

from . import _errors


_URL_KEY = "url"
_SMTP_SERVER_KEY = "smtp_server"
_SMTP_SERVER_PORT_KEY = "smtp_server_port"
_SMTP_LOGIN_KEY = "smtp_login"
_SMTP_PASSWORD_KEY = "smtp_password"
_FROM_EMAIL_KEY = "from_email"
_TO_EMAILS_KEY = "to_emails"

_THRESHOLD_KEY = "threshold"
_PRECEDING_DURATION_KEY = "preceding_duration"
_TIMEOUT_KEY = "timeout"
_COOLDOWN_KEY = "cooldown"

_DEFAULT_THRESHOLD = 0.7  # Pitch confidence
_DEFAULT_PRECEDING_DURATION = 30.0  # Thirty seconds
_DEFAULT_TIMEOUT = 60.0  # One minute
_DEFAULT_COOLDOWN = 3600.0  # One hour

_REQUIRED_KEYS = {
    _URL_KEY,
    _SMTP_SERVER_KEY,
    _SMTP_SERVER_PORT_KEY,
    _SMTP_LOGIN_KEY,
    _SMTP_PASSWORD_KEY,
    _FROM_EMAIL_KEY,
    _TO_EMAILS_KEY,
}
_OPTIONAL_KEYS = {_THRESHOLD_KEY, _PRECEDING_DURATION_KEY, _TIMEOUT_KEY, _COOLDOWN_KEY}


def _load_config(config_section: configparser.SectionProxy):
    supplied_keys = set(config_section.keys())
    missing_keys = _REQUIRED_KEYS - supplied_keys
    if missing_keys:
        raise _errors.StreamConfigMissingKeysError(missing_keys)

    unexpected_keys = supplied_keys - (_REQUIRED_KEYS | _OPTIONAL_KEYS)
    if unexpected_keys:
        raise _errors.StreamConfigUnexpectedKeysError(unexpected_keys)

    # Make sure to_emails is valid json
    try:
        to_emails = config_section[_TO_EMAILS_KEY]
        json.loads(to_emails)
    except json.decoder.JSONDecodeError as e:
        raise _errors.StreamConfigToEmailsFormatError(to_emails) from e

    return config_section


class StreamConfig:
    def __init__(self, config_section: configparser.SectionProxy) -> None:
        self._config = _load_config(config_section)

    def url(self) -> str:
        return self._config[_URL_KEY]

    def smtp_server(self) -> str:
        return self._config[_SMTP_SERVER_KEY]

    def smtp_server_port(self) -> int:
        return self._config.getint(_SMTP_SERVER_PORT_KEY)

    def smtp_login(self) -> str:
        return self._config[_SMTP_LOGIN_KEY]

    def smtp_password(self) -> str:
        return self._config[_SMTP_PASSWORD_KEY]

    def from_email(self) -> str:
        return self._config[_FROM_EMAIL_KEY]

    def to_emails(self) -> List[str]:
        return json.loads(self._config[_TO_EMAILS_KEY])

    def threshold(self) -> float:
        return self._config.getfloat(_THRESHOLD_KEY, _DEFAULT_THRESHOLD)

    def preceding_duration(self) -> float:
        return self._config.getfloat(
            _PRECEDING_DURATION_KEY, _DEFAULT_PRECEDING_DURATION
        )

    def timeout(self) -> float:
        return self._config.getfloat(_TIMEOUT_KEY, _DEFAULT_TIMEOUT)

    def cooldown(self) -> float:
        return self._config.getfloat(_COOLDOWN_KEY, _DEFAULT_COOLDOWN)
