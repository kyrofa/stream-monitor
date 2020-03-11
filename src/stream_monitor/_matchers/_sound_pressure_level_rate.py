from typing import Tuple

import aubio

from . import _matcher
from .. import _config


class SoundPressureLevelRateOfChangeMatcher(_matcher.Matcher):
    name = "SPL rate of change"

    def __init__(self, stream_config: _config.StreamConfig):
        super().__init__(stream_config)

        self._threshold = self._config.threshold()
        self._previous_value = None

    def _process_samples(
        self, samples: aubio.fvec, sample_count: int
    ) -> Tuple[float, bool]:
        db = aubio.db_spl(samples)

        if self._previous_value is None:
            self._previous_value = db
            return float("NaN"), False

        output = db - self._previous_value
        self._previous_value = db

        return output, abs(output) < self._threshold
