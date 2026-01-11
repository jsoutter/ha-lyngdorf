"""
Module implements the utilities to Lyngdorf devices.

:license: MIT, see LICENSE for more details.
"""

import math
from collections.abc import Mapping
from typing import Final

import attr

from .const import MIN_VOLUME_DB

_MIN_VOLUME_LINEAR: Final = 0.02
_MAX_VOLUME_LINEAR: Final = 1.0
_LINEAR_REF = 0.57  # Reference linear value
_FRACTION = 0.5  # Midpoint fraction for dB_ref


def compute_alpha(
    max_db: float,
    linear_ref: float = _LINEAR_REF,
    f: float = _FRACTION,
    min_linear: float = _MIN_VOLUME_LINEAR,
    max_linear: float = _MAX_VOLUME_LINEAR,
    min_db: float = MIN_VOLUME_DB,
) -> float:
    """
    Automatically compute the alpha based only on max_db.
    The reference dB is chosen as a fraction 'f' of the dB range.
    """
    # Compute reference dB
    dB_ref = min_db + f * (max_db - min_db)

    # Normalized log-linear position
    t = (math.log10(linear_ref) - math.log10(min_linear)) / (
        math.log10(max_linear) - math.log10(min_linear)
    )

    # Normalized dB fraction
    t_flat = (dB_ref - min_db) / (max_db - min_db)

    # Compute alpha
    alpha = math.log(t_flat) / math.log(t)
    return alpha


def linear_to_db_flattened(value: float, max_volume: float, alpha: float) -> float:
    """Convert a linear float [0-1] to dB (0.5 decimal)."""
    # Clamp input
    value = max(min(value, _MAX_VOLUME_LINEAR), _MIN_VOLUME_LINEAR)

    # Log scale interpolation
    log_min = math.log10(_MIN_VOLUME_LINEAR)
    log_max = math.log10(_MAX_VOLUME_LINEAR)
    log_value = math.log10(value)
    t = (log_value - log_min) / (log_max - log_min)

    # Apply curve exponent to flatten low end
    t_flat = t**alpha

    db = MIN_VOLUME_DB + t_flat * (max_volume - MIN_VOLUME_DB)

    # Round to 0.5 dB steps if within range
    if MIN_VOLUME_DB < db < max_volume:
        db = round(db * 2) / 2
    return db


def db_to_linear_flattened(db: float, max_volume: float, alpha: float) -> float:
    """Convert dB value to a float linear value [0-1] (rounded to 3 decimals)."""
    # Clamp dB
    db = round(max(min(db, max_volume), MIN_VOLUME_DB), 1)

    # Compute normalized position in [0,1]
    t_flat = (db - MIN_VOLUME_DB) / (max_volume - MIN_VOLUME_DB)

    # Inverse of curve exponent
    t = t_flat ** (1 / alpha)

    # Compute log-scale linear value
    log_min = math.log10(_MIN_VOLUME_LINEAR)
    log_max = math.log10(_MAX_VOLUME_LINEAR)
    log_value = log_min + t * (log_max - log_min)

    linear_value = 10**log_value
    return round(linear_value, 3)


@attr.define(auto_attribs=True)
class FixedSizeDict:
    max_size: int = 0
    _items: dict[int, str] = attr.ib(factory=dict[int, str], init=False)

    def set_size(self, size: int) -> None:
        """Set a new size limit and clear existing items."""
        if size < 0:
            raise ValueError("max_size must be >= 0")
        self.max_size = size
        self._items.clear()

    def add(self, item_id: int, value: str) -> None:
        """Add a new item if limit and uniqueness are respected."""
        if self.is_full():
            raise ValueError(f"Cannot add more than {self.max_size} items")
        if item_id in self._items:
            raise ValueError(f"Item with id '{item_id}' already exists")
        self._items[item_id] = value

    def get_all(self) -> list[str]:
        """Return all items."""
        return list(self._items.values())

    def get_by_id(self, item_id: int) -> str | None:
        """Lookup value by id."""
        return self._items.get(item_id)

    def get_by_value(self, value: str) -> int | None:
        """Lookup id by value."""
        for k, v in self._items.items():
            if v == value:
                return k
        return None

    def is_full(self) -> bool:
        """Check if max item count has been reached."""
        return len(self._items) >= self.max_size

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, item_id: int) -> bool:
        return item_id in self._items


def convert_on_off_bool(value: str) -> bool | None:
    """Convert a 1/0 and ON/OFF string to bool."""
    return {"1": True, "ON": True, "0": False, "OFF": False}.get(value)


def convert_volume(value: float | str) -> float | None:
    """Convert volume to float."""
    try:
        return float(value) / 10.0
    except (TypeError, ValueError):
        return None


def lookup_description(key_str: str, lookup: Mapping[int, str | None]) -> str | None:
    """Convert the key to int and return value from the lookup dict, or None."""
    try:
        key = int(key_str)
    except ValueError:
        return None
    return lookup.get(key)
