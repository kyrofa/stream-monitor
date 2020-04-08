import configparser
import pathlib
import textwrap

from stream_monitor import _config

import pytest


def _data_files(subdir: str):
    data_dir = pathlib.Path(__file__).parent.joinpath(f"data/{subdir}")
    return [d for d in data_dir.iterdir()]


@pytest.fixture("session", params=_data_files("normal"))
def test_data_normal_path(request):
    return request.param


@pytest.fixture("session", params=_data_files("bad"))
def test_data_bad_path(request):
    return request.param


@pytest.fixture
def config_file(tmp_path_factory):
    def _create_config_file(contents, *, smtp_settings=True):
        file_path = tmp_path_factory.mktemp("test") / "test.conf"
        with open(file_path, "w") as f:
            if smtp_settings:
                f.write(
                    textwrap.dedent(
                        """\
                        [DEFAULT]
                        smtp_server = smtp.example.com
                        smtp_server_port = 25
                        smtp_login = login
                        smtp_password = password
                        from_email = from@example.com
                        to_emails = ["to@example.com"]
                        """
                    )
                )
            f.write(contents)
        return file_path

    return _create_config_file


@pytest.fixture
def stream_config():
    def _create_stream_config(contents, *, stream_name: str):
        config = configparser.ConfigParser()
        config.read_string(
            textwrap.dedent(
                """\
                [DEFAULT]
                smtp_server = smtp.example.com
                smtp_server_port = 25
                smtp_login = login
                smtp_password = password
                from_email = from@example.com
                to_emails = ["to@example.com"]
                """
            )
            + contents
        )

        return _config.StreamConfig(config[stream_name])

    return _create_stream_config


@pytest.fixture
def config(config_file):
    def _create_config(contents, *, smtp_settings=True):
        config = configparser.ConfigParser()
        config.read_string(
            textwrap.dedent(
                """\
                [DEFAULT]
                smtp_server = smtp.example.com
                smtp_server_port = 25
                smtp_login = login
                smtp_password = password
                from_email = from@example.com
                to_email = to@example.com
                """
            )
            + contents
        )

        return _config.Config(config_file(contents, smtp_settings=smtp_settings))

    return _create_config
