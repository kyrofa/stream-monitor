import contextlib
import datetime
import itertools
import math
from typing import Dict, List, Optional

from . import _matcher_plot


class Plot:
    def __init__(self, figure) -> None:
        self._figure = figure
        self._x: List[float] = []
        self._matcher_plots: Dict[str, _matcher_plot.MatcherPlot] = dict()
        self._update_timestamp: Optional[datetime.datetime] = None

    def _initialize_plots(self, data: Dict[str, float]) -> None:
        matcher_count = len(data)

        if matcher_count <= 4:
            rows = 1
            cols = matcher_count
        else:
            rows = math.ceil(matcher_count / 4)
            cols = 4

        index = itertools.count(1)
        for matcher_name in data.keys():
            self._matcher_plots[matcher_name] = _matcher_plot.MatcherPlot(
                matcher_name,
                self._figure.add_subplot(rows, cols, next(index), title=matcher_name),
            )

    def update(self, time_elapsed: float, data: Dict[str, float]) -> None:
        # Skip this update if any of them are infinity or nan
        for name in data.keys():
            if math.isinf(data[name]) or math.isnan(data[name]):
                return

        if not self._matcher_plots:
            self._initialize_plots(data)

        previous_x = 0.0
        with contextlib.suppress(IndexError):
            previous_x = self._x[-1]
        self._x.append(previous_x + time_elapsed)

        for name, matcher_plot in self._matcher_plots.items():
            matcher_plot.update(self._x, data[name])

        now = datetime.datetime.now()
        if not self._update_timestamp:
            self._update_timestamp = now

        if (now - self._update_timestamp).total_seconds() > 1:
            self._figure.canvas.draw()
            self._figure.canvas.flush_events()
            self._update_timestamp = now
