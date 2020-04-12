from typing import Tuple

import aubio

from . import _matcher
from .. import _config


_WINDOW_SIZE = 4096
_HOP_SIZE = 2048


class PitchConfidenceMatcher(_matcher.Matcher):
    name = "Pitch confidence"

    def __init__(self, stream_config: _config.StreamConfig):
        super().__init__(stream_config)

        self._pitch = aubio.pitch("yin", _WINDOW_SIZE, _HOP_SIZE)
        self._threshold = self._config.threshold()

    def _process_samples(
        self, samples: aubio.fvec, sample_count: int
    ) -> Tuple[float, bool]:
        # Process some samples and then retrieve confidence
        self._pitch(samples)
        confidence = self._pitch.get_confidence()

        return confidence, confidence < self._threshold
