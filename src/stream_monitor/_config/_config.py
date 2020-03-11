import configparser
import pathlib
from typing import Dict, Set

from . import _errors
from . import _stream_config


def _load_config(
    config_file_path: pathlib.Path,
) -> Dict[str, _stream_config.StreamConfig]:
    config = configparser.ConfigParser()

    try:
        config.read(str(config_file_path))
    except configparser.Error as e:
        raise _errors.ConfigFileParsingError(config_file_path, e) from e

    stream_configs: Dict[str, _stream_config.StreamConfig] = dict()
    for stream_name in config.sections():
        try:
            stream_configs[stream_name] = _stream_config.StreamConfig(
                config[stream_name]
            )
        except _errors.ConfigurationError as e:
            raise _errors.InvalidStreamConfigError(
                config_file_path, stream_name, str(e)
            ) from e

    return stream_configs


class Config:
    def __init__(self, config_file_path: pathlib.Path) -> None:
        if not config_file_path.is_file():
            raise _errors.NoSuchConfigurationFileError(config_file_path)

        self._stream_configs = _load_config(config_file_path)

    def stream_names(self) -> Set[str]:
        return set(self._stream_configs.keys())

    def stream_config(self, stream_name: str) -> _stream_config.StreamConfig:
        try:
            return self._stream_configs[stream_name]
        except KeyError as e:
            raise _errors.NoSuchStreamError(stream_name) from e
