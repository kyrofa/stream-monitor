import collections
import datetime
import math
import pathlib
import tempfile
from typing import Callable, Deque, Dict, Iterable

import aubio

from . import _config, _errors, _matchers

_HOP_SIZE = 2048


class Stream:
    def __init__(
        self,
        name: str,
        config: _config.StreamConfig,
        matchers: Iterable[_matchers.Matcher],
        problem_callback: Callable[[str, str, pathlib.Path], None],
    ) -> None:
        self._name = name
        self._url = config.url()
        self._timeout = config.timeout()
        self._cooldown = config.cooldown()
        self._preceding_duration = config.preceding_duration()

        self._problem_callback = problem_callback
        self._matchers = list(matchers)

        # Open stream
        self._open()

        self._required_cooldown_sample_count = self._cooldown * self._source.samplerate
        self._cooldown_sample_count = 0
        self._in_cooldown = False

        self._match_sample_count = 0
        window_sample_count = (
            self._preceding_duration + self._timeout
        ) * self._source.samplerate
        self._window_samples: Deque[aubio.fvec] = collections.deque(
            maxlen=math.ceil(window_sample_count / _HOP_SIZE)
        )

    def close(self) -> None:
        self._source.close()

    def _open(self) -> None:
        self._source = aubio.source(self._url, hop_size=_HOP_SIZE)

    def process_hop(self):
        try:
            samples, sample_count = self._source()
        except RuntimeError:
            # Got an error of some sort... try reloading the source
            self.close()
            self._open()
            samples, sample_count = self._source()

        self._window_samples.append(samples.copy())

        data = self._process_samples(samples, sample_count)

        if sample_count < self._source.hop_size:
            raise _errors.EndOfStreamError(self._name)

        return data

    def _process_samples(self, samples: aubio.fvec, sample_count: int):
        # Skip this set of samples if we're in cooldown
        if self._in_cooldown:
            current_count = self._cooldown_sample_count
            self._cooldown_sample_count += sample_count
            if current_count < self._required_cooldown_sample_count:
                return

        self._in_cooldown = False
        self._cooldown_sample_count = 0
        data: Dict[str, float] = dict()
        for matcher in self._matchers:
            value, match = matcher.process_samples(samples, sample_count)
            data[matcher.name] = value

            if match:
                self._match_sample_count += sample_count
                seconds = self._match_sample_count / self._source.samplerate
                if seconds > self._timeout:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                    path = pathlib.Path(
                        f"{tempfile.gettempdir()}/{self._name}_{timestamp}.wav"
                    )

                    with aubio.sink(str(path), self._source.samplerate) as output:
                        for match_samples in self._window_samples:
                            output(match_samples, self._source.hop_size)

                    self._problem_callback(self._name, matcher.name, path)

                    # Trigger cooldown period
                    self._in_cooldown = True
                    self._match_sample_count = 0
            else:
                self._match_sample_count = 0

        return (sample_count / self._source.samplerate, data)
