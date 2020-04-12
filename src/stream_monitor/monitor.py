import argparse
import collections
import contextlib
import functools
import logging
import os
import multiprocessing
import pathlib
import queue
import signal
import sys
import textwrap
import traceback
from typing import List

try:
    from matplotlib import pyplot
except ImportError:
    pyplot = None

from . import _config, _errors, _stream, _matchers, _notifier, _plotting

logger = logging.getLogger(__name__)

_StreamInfo = collections.namedtuple(
    "_StreamInfo", ("name", "config", "process", "queue", "figure", "plot")
)


def main(args=None):
    parser = argparse.ArgumentParser(description="Monitor audio streams.")
    parser.add_argument(
        "--config",
        "-c",
        type=pathlib.Path,
        default="/etc/stream-monitor/detector.config",
        help="path to config file",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="print verbose/debug output",
    )
    parser.add_argument(
        "--plot", action="store_true", help="plot all matchers for all streams",
    )

    args = parser.parse_args(args)

    sys.excepthook = functools.partial(_exception_handler, debug=args.verbose)
    level = logging.INFO
    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)

    config = _config.Config(args.config)
    return _run(config, args.plot)


def _run(config, plot: bool):
    if plot:
        if not pyplot:
            raise _errors.PlottingNotAvailableError()

        pyplot.ion()
        pyplot.style.use("fivethirtyeight")

    stream_names = config.stream_names()
    if not stream_names:
        raise _errors.NoStreamsConfiguredError()

    streams: List[_StreamInfo] = list()

    # Open all configured streams
    for stream_name in stream_names:
        stream_config = config.stream_config(stream_name)
        figure = None
        stream_plot = None
        q = None

        if plot:
            figure = pyplot.figure(num=stream_name)
            stream_plot = _plotting.Plot(figure)
            q = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=_run_one, args=(stream_name, config, stream_config, q)
        )

        streams.append(
            _StreamInfo(
                name=stream_name,
                config=stream_config,
                process=process,
                queue=q,
                figure=figure,
                plot=stream_plot,
            )
        )

    message = "Monitoring the following streams:\n"
    for stream in streams:
        message += textwrap.indent(
            textwrap.dedent(
                f"""\
            {stream.name}:
                url: {stream.config.url()}
                timeout: {stream.config.timeout()}
                cooldown: {stream.config.cooldown()}
            """
            ),
            "    ",
        )
    logger.info(message)

    run = True

    def _shutdown(signal_received, frame):
        nonlocal run
        run = False
        for stream in streams:
            if signal_received:
                logger.info(f"Shutting down monitor for stream '{stream.name}'")
            stream.process.join()

    for stream in streams:
        stream.process.start()

    signal.signal(signal.SIGINT, _shutdown)

    try:
        if stream.plot:
            while run:
                for stream in streams:
                    if stream.queue:
                        with contextlib.suppress(queue.Empty):
                            stream.plot.update(*stream.queue.get(timeout=1))
    finally:
        while run:
            for stream in streams:
                stream.process.join(1)
                if run and stream.process.exitcode is not None:
                    logger.critical(f"Monitor for stream '{stream.name}' has crashed")
                    for other_stream in streams:
                        if other_stream.process.pid != stream.process.pid:
                            os.kill(other_stream.process.pid, signal.SIGINT)
                            other_stream.process.join()

                    return 1
    return 0


def _run_one(
    stream_name: str,
    config: _config.Config,
    stream_config: _config.StreamConfig,
    queue: multiprocessing.Queue,
) -> None:
    notifier = _notifier.Notifier(config)

    stream = _stream.Stream(
        name=stream_name,
        config=stream_config,
        matchers=[
            # This one doesn't work for all tests
            # _matchers.SoundPressureLevelRateOfChangeMatcher(stream_config),
            # This one is a little too close for comfort
            # _matchers.VocoderMatcher(stream_config),
            _matchers.PitchConfidenceMatcher(stream_config),
        ],
        problem_callback=notifier.problem_detected_callback,
    )

    run = True

    def _shutdown(signal_received, frame) -> None:
        nonlocal run
        run = False

    signal.signal(signal.SIGINT, _shutdown)

    try:
        # These are internet streams; they never end. Loop forever.
        while run:
            data = stream.process_hop()
            if queue:
                queue.put(data)
    finally:
        stream.close()


def _exception_handler(exception_type, exception, exception_traceback, *, debug=False):
    if isinstance(exception, _errors.StreamMonitorError):
        logger.error(str(exception))

    if debug or not isinstance(exception, _errors.StreamMonitorError):
        traceback.print_exception(exception_type, exception, exception_traceback)

    print("exiting")
    sys.exit(1)
