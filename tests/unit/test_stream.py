import textwrap

import mock
import pytest

from stream_monitor import _errors, _matchers, _stream


class _TestFalseMatcher(_matchers.Matcher):
    name = "test false matcher"

    def _process_samples(self, samples, sample_count):
        return 1, False


class _TestTrueMatcher(_matchers.Matcher):
    name = "test true matcher"

    def _process_samples(self, samples, sample_count):
        return 2, True


def test_stream_good(test_data_normal_path, stream_config):
    config = stream_config(
        textwrap.dedent(
            f"""\
            [stream]
            url = {str(test_data_normal_path)}
            timeout = 10
            """
        ),
        stream_name="stream",
    )

    callback = mock.MagicMock()
    stream = _stream.Stream(
        name="stream",
        config=config,
        problem_callback=callback,
        matchers=[_TestFalseMatcher(config)],
    )

    with pytest.raises(_errors.EndOfStreamError):
        while True:
            stream.process_hop()

    stream.close()
    callback.assert_not_called()


def test_stream_bad(test_data_normal_path, stream_config):
    config = stream_config(
        textwrap.dedent(
            f"""\
            [stream]
            url = {str(test_data_normal_path)}
            timeout = 1
            """
        ),
        stream_name="stream",
    )

    callback = mock.MagicMock()
    stream = _stream.Stream(
        name="stream",
        config=config,
        problem_callback=callback,
        matchers=[_TestTrueMatcher(config)],
    )

    with pytest.raises(_errors.EndOfStreamError):
        while True:
            stream.process_hop()

    stream.close()
    callback.assert_called_once_with("stream", _TestTrueMatcher.name, mock.ANY)


def test_stream_bad_short_cooldown(test_data_normal_path, stream_config):
    config = stream_config(
        textwrap.dedent(
            f"""\
            [stream]
            url = {str(test_data_normal_path)}
            timeout = 5
            cooldown = 5
            """
        ),
        stream_name="stream",
    )

    callback = mock.MagicMock()
    stream = _stream.Stream(
        name="stream",
        config=config,
        problem_callback=callback,
        matchers=[_TestTrueMatcher(config)],
    )

    with pytest.raises(_errors.EndOfStreamError):
        while True:
            stream.process_hop()

    stream.close()
    callback.assert_has_calls(
        [
            mock.call("stream", _TestTrueMatcher.name, mock.ANY),
            mock.call("stream", _TestTrueMatcher.name, mock.ANY),
        ]
    )
