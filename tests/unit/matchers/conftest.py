from stream_monitor import _config

import pytest


@pytest.fixture
def config(config_file):
    def _create_config(contents):
        return _config.Config(config_file(contents))

    return _create_config
