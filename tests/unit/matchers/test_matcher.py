import textwrap

import aubio

import pytest

from stream_monitor import _matchers


class _TestFalseMatcher(_matchers.Matcher):
    name = "test false matcher"

    def _process_samples(self, samples, sample_count):
        return 42, False


class _TestTrueMatcher(_matchers.Matcher):
    name = "test true matcher"

    def _process_samples(self, samples, sample_count):
        return 42, True


def test_matcher_is_abstract(config):
    config = config(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            """
        )
    )

    # Should not be able to instantiate abstract class
    with pytest.raises(TypeError):
        _matchers.Matcher(config.stream_config("stream"))


def test_matcher_false(config):
    config = config(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            """
        )
    )
    matcher = _TestFalseMatcher(config.stream_config("stream"))

    sample_count = 256
    samples = aubio.fvec(sample_count)
    assert matcher.process_samples(samples, sample_count) == (42, False)


def test_matcher_true(config):
    config = config(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            """
        )
    )
    matcher = _TestTrueMatcher(config.stream_config("stream"))

    sample_count = 256
    samples = aubio.fvec(sample_count)
    assert matcher.process_samples(samples, sample_count) == (42, True)
