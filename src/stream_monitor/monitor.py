import argparse
import functools
import logging
import pathlib
import sys
import traceback
from typing import List

try:
    from matplotlib import pyplot
except ImportError:
    pyplot = None

from . import _config, _errors, _stream, _matchers, _notifier

logger = logging.getLogger(__name__)


def _exception_handler(exception_type, exception, exception_traceback, *, debug=False):
    if isinstance(exception, _errors.StreamMonitorError):
        logger.error(str(exception))

    if debug or not isinstance(exception, _errors.StreamMonitorError):
        traceback.print_exception(exception_type, exception, exception_traceback)

    sys.exit(1)


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
    level = logging.WARNING
    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)

    config = _config.Config(args.config)
    _run(config, args.plot)


def _run(config, plot: bool):
    streams: List[_stream.Stream] = list()

    if plot:
        if not pyplot:
            raise _errors.PlottingNotAvailableError()

        pyplot.ion()
        pyplot.style.use("fivethirtyeight")

    notifier = _notifier.Notifier(config)

    try:
        # Open all configured streams
        for stream_name in config.stream_names():
            stream_config = config.stream_config(stream_name)

            figure = None
            if plot:
                figure = pyplot.figure(num=stream_name)

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
                figure=figure,
            )
            streams.append(stream)

        if not streams:
            raise _errors.NoStreamsConfiguredError()

        logging.info("Monitoring the following streams:")
        for stream in streams:
            logging.info(stream)

        # These are internet streams; they never end. Loop forever.
        while True:
            for stream in streams:
                stream.process_hop()
    finally:
        for stream in streams:
            stream.close()
