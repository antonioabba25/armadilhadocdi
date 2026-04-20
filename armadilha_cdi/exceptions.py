class ArmadilhaCDIError(Exception):
    """Base exception for the project."""


class DomainValidationError(ArmadilhaCDIError):
    """Raised when business inputs are invalid."""


class MarketDataError(ArmadilhaCDIError):
    """Raised when market data cannot be obtained or validated."""


class DataUnavailableError(MarketDataError):
    """Raised when the required series are missing in the selected window."""
