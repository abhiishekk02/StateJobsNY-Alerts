"""Application-specific exceptions with actionable messages."""


class JobAlertError(Exception):
    """Base error for expected application failures."""


class ConfigurationError(JobAlertError):
    """Configuration is missing or invalid."""


class FetchError(JobAlertError):
    """A remote page could not be fetched."""


class ParserError(JobAlertError):
    """The remote markup no longer contains required data."""


class NotificationError(JobAlertError):
    """An email could not be delivered."""


class StorageError(JobAlertError):
    """Persistent state could not be read or written."""

