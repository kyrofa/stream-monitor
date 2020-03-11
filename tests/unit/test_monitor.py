import textwrap

from stream_monitor import monitor, _notifier, _matchers, _errors

import mock
import pytest


@pytest.fixture
def config_file(tmp_path_factory):
    def _create_config_file(contents):
        file_path = tmp_path_factory.mktemp("test") / "test.conf"
        with open(file_path, "w") as f:
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


def test_one_stream(config_file, test_data_normal_path):
    with mock.patch(
        "stream_monitor.monitor._stream.Stream", autospec=True
    ) as mock_stream:
        mock_stream.return_value.process_hop.side_effect = _errors.EndOfStreamError(
            "stream"
        )
        with pytest.raises(_errors.EndOfStreamError) as error:
            monitor.main(
                [
                    "-c",
                    str(
                        config_file(
                            textwrap.dedent(
                                f"""\
                                [stream]
                                url={str(test_data_normal_path)}
                                """
                            )
                        )
                    ),
                ]
            )
        assert error.value.stream_name == "stream"
    mock_stream.assert_called_once_with(
        name="stream",
        config=mock.ANY,
        matchers=mock.ANY,
        problem_callback=mock.ANY,
        figure=None,
    )
    mock_stream.return_value.close.assert_called_once_with()


def test_two_streams(config_file, test_data_normal_path):
    with mock.patch(
        "stream_monitor.monitor._stream.Stream", autospec=True
    ) as mock_stream:
        mock_stream.return_value.process_hop.side_effect = _errors.EndOfStreamError(
            "stream"
        )
        with pytest.raises(_errors.EndOfStreamError) as error:
            monitor.main(
                [
                    "-c",
                    str(
                        config_file(
                            textwrap.dedent(
                                f"""\
                                [stream1]
                                url={str(test_data_normal_path)}
                                [stream2]
                                url={str(test_data_normal_path)}
                                """
                            )
                        )
                    ),
                ]
            )
        assert error.value.stream_name == "stream"
    mock_stream.assert_has_calls(
        [
            mock.call(
                name="stream1",
                config=mock.ANY,
                matchers=mock.ANY,
                problem_callback=mock.ANY,
                figure=None,
            ),
            mock.call(
                name="stream2",
                config=mock.ANY,
                matchers=mock.ANY,
                problem_callback=mock.ANY,
                figure=None,
            ),
        ],
        any_order=True,
    )
    assert len(mock_stream.return_value.close.mock_calls) == 2


def test_plot(config_file, test_data_normal_path):
    with mock.patch("stream_monitor.monitor.pyplot") as mock_pyplot:
        with mock.patch(
            "stream_monitor.monitor._stream.Stream", autospec=True
        ) as mock_stream:
            mock_stream.return_value.process_hop.side_effect = _errors.EndOfStreamError(
                "stream"
            )
            with pytest.raises(_errors.EndOfStreamError) as error:
                monitor.main(
                    [
                        "-c",
                        str(
                            config_file(
                                textwrap.dedent(
                                    f"""\
                                    [stream]
                                    url={str(test_data_normal_path)}
                                    """
                                )
                            )
                        ),
                        "--plot",
                    ]
                )
            assert error.value.stream_name == "stream"

    mock_stream.assert_called_once_with(
        name="stream",
        config=mock.ANY,
        matchers=mock.ANY,
        problem_callback=mock.ANY,
        figure=mock_pyplot.figure(),
    )
    mock_stream.return_value.close.assert_called_once_with()


def test_no_streams_configured(config_file):
    with pytest.raises(_errors.NoStreamsConfiguredError):
        monitor.main(["-c", str(config_file(""))])


def test_monitor_normal(test_data_normal_path, config_file):
    with mock.patch.object(
        _notifier.Notifier, "problem_detected_callback", autospec=True,
    ) as mock_problem_detected_callback:
        with pytest.raises(_errors.EndOfStreamError) as error:
            monitor.main(
                [
                    "-c",
                    str(
                        config_file(
                            textwrap.dedent(
                                f"""\
                                [stream]
                                url = {str(test_data_normal_path)}
                                timeout = 10
                                """
                            )
                        )
                    ),
                ]
            )
        assert error.value.stream_name == "stream"

    mock_problem_detected_callback.assert_not_called()


def test_monitor_bad(test_data_bad_path, config_file):
    with mock.patch.object(
        _notifier.Notifier, "problem_detected_callback", autospec=True,
    ) as mock_problem_detected_callback:
        with pytest.raises(_errors.EndOfStreamError) as error:
            monitor.main(
                [
                    "-c",
                    str(
                        config_file(
                            textwrap.dedent(
                                f"""\
                                [stream]
                                url = {str(test_data_bad_path)}
                                timeout = 10
                                """
                            )
                        )
                    ),
                ]
            )
        assert error.value.stream_name == "stream"

    mock_problem_detected_callback.assert_called_once_with(
        mock.ANY,
        "stream",
        _matchers.SoundPressureLevelRateOfChangeMatcher.name,
        mock.ANY,
    )
