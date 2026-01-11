#!/usr/bin/env python3
"""
Module implements the exception classes for Lyngdorf devices.

:license: MIT, see LICENSE for more details.
"""


class LyngdorfError(Exception):
    """Define an error for Lyngdorf processor."""


class LyngdorfProcessingError(LyngdorfError):
    """Define an error for process errors."""


class LyngdorfNetworkError(LyngdorfError):
    """Define a network error during a request for Lyngdorf processor."""


class LyngdorfTimoutError(LyngdorfError):
    """Define an error for timeouts during a request for Lyngdorf processor."""


class LyngdorfUnsupportedError(LyngdorfError):
    """Define an error for unsupported Lyngdorf processor."""
