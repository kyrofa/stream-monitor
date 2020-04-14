import abc
from typing import Tuple

import aubio

from .. import _config


class Matcher(abc.ABC):
    def __init__(self, stream_config: _config.StreamConfig):
        self._config = stream_config

    def process_samples(
        self, samples: aubio.fvec, sample_count: int
    ) -> Tuple[float, bool]:
        return self._process_samples(samples, sample_count)

    @abc.abstractmethod
    def _process_samples(
        self, samples: aubio.fvec, sample_count: int
    ) -> Tuple[float, bool]:
        pass

    @abc.abstractproperty
    def name(self) -> str:
        pass
