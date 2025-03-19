class DomainException(Exception):
    """Base exception for domain errors"""

    pass


class InvalidOrderException(DomainException):
    """Raised when order parameters are invalid"""

    pass


class MarketNotFoundException(DomainException):
    """Raised when market is not found"""

    pass
