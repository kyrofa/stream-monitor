from typing import Tuple

import aubio
import numpy

from . import _matcher
from .. import _config


_WINDOW_SIZE = 512
_HOP_SIZE = _WINDOW_SIZE // 2


class VocoderMatcher(_matcher.Matcher):
    name = "Frequency analysis"

    def __init__(self, stream_config: _config.StreamConfig):
        super().__init__(stream_config)

        self._vocoder = aubio.pvoc(_WINDOW_SIZE, _HOP_SIZE)
        self._previous_value = None

    def _process_samples(
        self, samples: aubio.fvec, sample_count: int
    ) -> Tuple[float, bool]:
        pv = self._vocoder(samples)
        std_dev = numpy.std(pv.norm)
        average = numpy.average(pv.norm)

        value = std_dev / average
        return value, False
