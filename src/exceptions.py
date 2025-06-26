"""
exceptions.py

Custom exceptions for the Final Engine.
"""


class RetryException(Exception):
    """
    Exception raised when a guard detects an issue that requires retry.

    Contains information about which flags were triggered and details
    about the issue for retry logic.

    Attributes
    ----------
    message : str
        Human-readable error message
    flags : dict
        Dictionary of flag names and their values/details
    guard_name : str
        Name of the guard that raised the exception
    """

    def __init__(self, message: str, flags: dict = None, guard_name: str = None):
        """
        Initialize RetryException.

        Parameters
        ----------
        message : str
            Human-readable error message
        flags : dict, optional
            Dictionary of flag names and their values/details
        guard_name : str, optional
            Name of the guard that raised the exception
        """
        super().__init__(message)
        self.flags = flags or {}
        self.guard_name = guard_name

    def __str__(self):
        """Return string representation of the exception."""
        base_msg = super().__str__()
        if self.guard_name:
            base_msg = f"[{self.guard_name}] {base_msg}"
        if self.flags:
            flag_info = ", ".join(f"{k}={v}" for k, v in self.flags.items())
            base_msg += f" (flags: {flag_info})"
        return base_msg
