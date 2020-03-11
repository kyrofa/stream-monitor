import datetime
import pathlib
import tempfile
import textwrap
from typing import Callable, Dict, Iterable

import aubio

from . import _config, _errors, _matchers, _plotting

_HOP_SIZE = 256


class Stream:
    def __init__(
        self,
        name: str,
        config: _config.StreamConfig,
        matchers: Iterable[_matchers.Matcher],
        problem_callback: Callable[[str, str, pathlib.Path], None],
        *,
        figure=None,
    ) -> None:
        self._name = name
        self._url = config.url()
        self._timeout = config.timeout()
        self._cooldown = config.cooldown()

        self._problem_callback = problem_callback
        self._matchers = list(matchers)

        # Open stream
        self._source = aubio.source(self._url, hop_size=_HOP_SIZE)

        self._required_cooldown_sample_count = self._cooldown * self._source.samplerate
        self._cooldown_sample_count = 0
        self._in_cooldown = False

        self._plot = None
        if figure:
            self._plot = _plotting.Plot(figure)

    def close(self) -> None:
        self._source.close()

    def __str__(self) -> str:
        return textwrap.dedent(
            f"""\
            {self._name}:
                url: {self._url}
                timeout: {self._timeout}
                cooldown: {self._cooldown}"""
        )

    def process_hop(self):
        samples, sample_count = self._source()

        self._process_samples(samples, sample_count)

        if sample_count < self._source.hop_size:
            raise _errors.EndOfStreamError(self._name)

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
                seconds = matcher.match_sample_count() / self._source.samplerate
                if seconds > self._timeout:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                    path = pathlib.Path(
                        f"{tempfile.gettempdir()}/{self._name}_{timestamp}.wav"
                    )

                    with aubio.sink(str(path), self._source.samplerate) as output:
                        for match_samples in matcher.match_samples():
                            output(match_samples, self._source.hop_size)
                    matcher.reset()

                    self._problem_callback(self._name, matcher.name, path)

                    # Trigger cooldown period
                    self._in_cooldown = True

        if self._plot:
            self._plot.update(sample_count / self._source.samplerate, data)
