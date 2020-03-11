import math
import textwrap

import aubio
import numpy

from stream_monitor import _matchers


def test_match(config):
    config = config(
        textwrap.dedent(
            """\
            [stream]
            url = foo
            threshold = 10.0
            """
        )
    )
    matcher = _matchers.SoundPressureLevelRateOfChangeMatcher(
        config.stream_config("stream")
    )

    sample_count = 256
    samples = aubio.fvec(numpy.ones(sample_count))

    value, match = matcher.process_samples(samples, sample_count)
    assert math.isnan(value)
    assert not match
    assert matcher.match_sample_count() == 0
    assert len(matcher.match_samples()) == 0

    assert matcher.process_samples(samples, sample_count) == (0.0, True)
    assert matcher.match_sample_count() == sample_count
    match_samples = matcher.match_samples()
    assert len(match_samples) == 1
    assert all(numpy.equal(match_samples[0], samples))

    assert matcher.match_sample_count() == sample_count
    match_samples = matcher.match_samples()
    assert len(match_samples) == 1
    assert all(numpy.equal(match_samples[0], samples))

    samples = aubio.fvec(2 * numpy.ones(sample_count))
    value, match = matcher.process_samples(samples, sample_count)
    assert 6 <= value <= 7
    assert match
    assert len(match_samples) == 2
    assert all(numpy.equal(match_samples[1], samples))

    samples = aubio.fvec(10 * numpy.ones(sample_count))
    value, match = matcher.process_samples(samples, sample_count)
    assert 13 <= value <= 14
    assert not match
    assert matcher.match_sample_count() == 0
    assert len(matcher.match_samples()) == 0
