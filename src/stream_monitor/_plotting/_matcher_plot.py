from typing import List


class MatcherPlot:
    def __init__(self, name: str, axes):
        self._y: List[float] = []
        self._axes = axes
        (self._data_line,) = self._axes.plot([], [], label=name)

    def update(self, x: List[float], new_y: float) -> None:
        self._y.append(new_y)
        self._data_line.set_data(x, self._y)

        self._axes.set_xlim(min(x) - 1, max(x) + 1)
        self._axes.set_ylim(min(self._y) - 1, max(self._y) + 1)
        self._axes.legend(loc="upper left")
