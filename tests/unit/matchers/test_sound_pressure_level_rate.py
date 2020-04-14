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

    assert matcher.process_samples(samples, sample_count) == (0.0, True)

    samples = aubio.fvec(2 * numpy.ones(sample_count))
    value, match = matcher.process_samples(samples, sample_count)
    assert 6 <= value <= 7
    assert match

    samples = aubio.fvec(10 * numpy.ones(sample_count))
    value, match = matcher.process_samples(samples, sample_count)
    assert 13 <= value <= 14
    assert not match
