import abc
from typing import List, Tuple

import aubio

from .. import _config


class Matcher(abc.ABC):
    def __init__(self, stream_config: _config.StreamConfig):
        self._config = stream_config
        self.reset()

    def reset(self) -> None:
        self._match_sample_count = 0
        self._match_samples: List[aubio.fvec] = list()

    def match_sample_count(self) -> float:
        return self._match_sample_count

    def match_samples(self) -> List[aubio.fvec]:
        return self._match_samples

    def process_samples(
        self, samples: aubio.fvec, sample_count: int
    ) -> Tuple[float, bool]:
        value, match = self._process_samples(samples, sample_count)
        if match:
            self._match_sample_count += sample_count
            self._match_samples.append(samples.copy())
        else:
            self.reset()

        return value, match

    @abc.abstractmethod
    def _process_samples(
        self, samples: aubio.fvec, sample_count: int
    ) -> Tuple[float, bool]:
        pass

    @abc.abstractproperty
    def name(self) -> str:
        pass
