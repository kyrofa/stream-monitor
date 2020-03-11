class StreamMonitorError(Exception):
    """Base class for all exceptions in stream monitor."""


class EndOfStreamError(StreamMonitorError):
    def __init__(self, stream_name: str) -> None:
        self.stream_name = stream_name
        super().__init__(f"Stream with name {stream_name!r} ended unexpectedly")


class NoStreamsConfiguredError(StreamMonitorError):
    def __init__(self) -> None:
        super().__init__("No streams configured, check config file")


class PlottingNotAvailableError(StreamMonitorError):
    def __init__(self) -> None:
        super().__init__("matplotlib is not installed; plotting is not available")


class EmailAttachmentMimeTypeError(StreamMonitorError):
    def __init__(self, attachment) -> None:
        self.attachment = attachment
        super().__init__(f"Unable to detect mime type of '{attachment!s}'")
