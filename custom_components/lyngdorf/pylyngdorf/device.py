#!/usr/bin/env python3
"""
Module implements the device class for Lyngdorf processors.

:license: MIT, see LICENSE for more details.
"""

import logging
import math
from collections.abc import Callable, Coroutine, Mapping
from functools import wraps
from typing import Any, Final

import attr

from .api import LyngdorfApi
from .const import (
    DEFAULT_MAX_LIPSYNC,
    DEFAULT_MAX_VOLUME_DB,
    DEFAULT_MIN_LIPSYNC,
    DEFAULT_PROTOCOL,
    DEVICE_PROTOCOLS,
    MIN_VOLUME_DB,
    DeviceModel,
)

_MIN_VOLUME_LINEAR: Final = 0.02
_MAX_VOLUME_LINEAR: Final = 1.0

# Curve shaping factor
_CURVE_EXPONENT = 1.6

_LOGGER = logging.getLogger(__name__)


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
    """Convert the key to int and return value from the lookup dict, or None if invalid."""
    try:
        key = int(key_str)
    except ValueError:
        return None
    return lookup.get(key)


def notify_callback(
    func: Callable[..., Coroutine[Any, Any, Any]],
) -> Callable[..., Coroutine[Any, Any, Any]]:
    """Decorator for async instance methods with self."""

    @wraps(func)
    async def wrapper(self: "LyngdorfDevice", *args: Any, **kwargs: Any) -> Any:
        result = await func(self, *args, **kwargs)
        self.run_notify_callback()
        return result

    return wrapper


@attr.define(kw_only=True)
class LyngdorfDevice:
    """Implements a class with device information of the processor."""

    _api: LyngdorfApi = attr.field(
        factory=lambda: LyngdorfApi(device_protocol=DEFAULT_PROTOCOL),
        validator=attr.validators.instance_of(LyngdorfApi),
    )
    _notification_callback: Callable[[], None] | None = attr.field(default=None)
    # Common properties
    _model: DeviceModel | None = attr.field(default=None)
    _multichannel: bool = attr.field(default=False)
    _power: bool | None = attr.field(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _volume: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _volume_percent: float | None = attr.field(default=None)
    _muted: bool = attr.field(
        converter=attr.converters.optional(convert_on_off_bool), default=True
    )
    _max_volume: float = attr.field(
        converter=attr.converters.optional(convert_volume),
        default=DEFAULT_MAX_VOLUME_DB * 10,
    )

    # Sources properties
    _sources: FixedSizeDict = attr.field(factory=FixedSizeDict)
    _source: str | None = attr.field(default=None)
    _stream_type: str | None = attr.field(default=None)

    # Room Perfect properties
    _voicings: FixedSizeDict = attr.field(factory=FixedSizeDict)
    _voicing: str | None = attr.field(default=None)
    _focus_positions: FixedSizeDict = attr.field(factory=FixedSizeDict)
    _focus_position: str | None = attr.field(default=None)

    # Multichannel device properties
    _audio_modes: FixedSizeDict = attr.field(factory=FixedSizeDict)
    _audio_mode: str | None = attr.field(default=None)
    _audio_input: str | None = attr.field(default=None)
    _audio_type: str | None = attr.field(default=None)
    _video_input: str | None = attr.field(default=None)
    _video_type: str | None = attr.field(default=None)
    _video_output: str | None = attr.field(default=None)
    _lipsync: int = attr.field(converter=attr.converters.optional(int), default=None)
    _min_lipsync: int = attr.field(converter=int, default=DEFAULT_MIN_LIPSYNC)
    _max_lipsync: int = attr.field(converter=int, default=DEFAULT_MAX_LIPSYNC)
    _dts_dialog_available: bool | None = attr.field(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _dts_dialog: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _loudness: bool | None = attr.field(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )

    def set_notification_callback(self, callback: Callable[[], None]):
        self._notification_callback = callback

    def run_notify_callback(self):
        if self._notification_callback:
            self._notification_callback()

    @notify_callback
    async def _async_model_callback(self, event: str, params: list[str]) -> None:
        """Handle a device model event."""
        self._model = (
            DeviceModel(params[0])
            if params and params[0] in DeviceModel._value2member_map_
            else None
        )

        if self._model and self._api.device_protocol is DEFAULT_PROTOCOL:
            self._api.device_protocol = DEVICE_PROTOCOLS[self._model]

    @notify_callback
    async def _async_power_callback(self, event: str, params: list[str]) -> None:
        """Handle a power change event."""
        self._power = params[0] if params else None

    @notify_callback
    async def _async_volume_callback(self, event: str, params: list[str]) -> None:
        """Handle a volume change event."""
        self._volume = params[0] if params else None
        volume = self._volume
        self._volume_percent = (
            self._db_to_linear_interpolated(volume) if volume else None
        )

    @notify_callback
    async def _async_mute_callback(self, event: str, params: list[str]) -> None:
        """Handle a muting change event."""
        self._muted = params[0] if params else event[4:]

    @notify_callback
    async def _async_max_volume_callback(self, event: str, params: list[str]) -> None:
        """Handle a max volume event."""
        if params:
            self._max_volume = params[0]

    @notify_callback
    async def _async_source_count_callback(self, event: str, params: list[str]) -> None:
        """Handle a source count event."""
        if params:
            self._sources.set_size(int(params[0]))

    @notify_callback
    async def _async_source_callback(self, event: str, params: list[str]) -> None:
        """Handle a source event."""
        if params:
            source_id = int(params[0])
            self._source = (
                self._sources.get_by_id(source_id)
                if self._sources.is_full()
                else self._sources.add(source_id, params[1])
            )

    @notify_callback
    async def _async_stream_type_callback(self, event: str, params: list[str]) -> None:
        """Handle a stream type change event."""
        self._stream_type = (
            lookup_description(params[0], self._api.device_protocol.streaming_types)
            if params
            else None
        )

    @notify_callback
    async def _async_voicing_count_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a voicing count event."""
        if params:
            self._voicings.set_size(int(params[0]))

    @notify_callback
    async def _async_voicing_callback(self, event: str, params: list[str]) -> None:
        """Handle a voicing event."""
        if params:
            voicing_id = int(params[0])
            self._voicing = (
                self._voicings.get_by_id(voicing_id)
                if self._voicings.is_full()
                else self._voicings.add(voicing_id, params[1])
            )

    @notify_callback
    async def _async_focus_position_count_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a focus position count event."""
        if params:
            self._focus_positions.set_size(int(params[0]))

    @notify_callback
    async def _async_focus_position_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a focus position event."""
        if params:
            focus_position_id = int(params[0])
            self._focus_position = (
                self._focus_positions.get_by_id(focus_position_id)
                if self._focus_positions.is_full()
                else self._focus_positions.add(focus_position_id, params[1])
            )

    @notify_callback
    async def _async_audio_mode_count_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a audio mode count event."""
        if params:
            self._audio_modes.set_size(int(params[0]))

    @notify_callback
    async def _async_audio_mode_callback(self, event: str, params: list[str]) -> None:
        """Handle a audio mode event."""
        if params:
            audio_mode_id = int(params[0])
            self._audio_mode = (
                self._audio_modes.get_by_id(audio_mode_id)
                if self._audio_modes.is_full()
                else self._audio_modes.add(audio_mode_id, params[1])
            )

    @notify_callback
    async def _async_audio_input_callback(self, event: str, params: list[str]) -> None:
        """Handle a audio input change event."""
        self._audio_input = (
            lookup_description(params[0], self._api.device_protocol.audio_inputs)
            if params
            else None
        )

    @notify_callback
    async def _async_audio_type_callback(self, event: str, params: list[str]) -> None:
        """Handle a audio type change event."""
        self._audio_type = ", ".join(params) if params else None

    @notify_callback
    async def _async_video_input_callback(self, event: str, params: list[str]) -> None:
        """Handle a video input event."""
        self._video_input = (
            lookup_description(params[0], self._api.device_protocol.video_inputs)
            if params
            else None
        )

    @notify_callback
    async def _async_video_type_callback(self, event: str, params: list[str]) -> None:
        """Handle a video type change event."""
        self._video_type = params[0] if params else None

    @notify_callback
    async def _async_video_output_callback(self, event: str, params: list[str]) -> None:
        """Handle a video output event."""
        self._video_output = (
            lookup_description(params[0], self._api.device_protocol.video_outputs)
            if params
            else None
        )

    @notify_callback
    async def _async_lipsync_range_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a lipsync range event."""
        if len(params) == 2:
            self._min_lipsync = params[0]
            self._max_lipsync = params[1]

    @notify_callback
    async def _async_lipsync_callback(self, event: str, params: list[str]) -> None:
        """Handle a lipsync event."""
        self._lipsync = params[0] if params else None

    @notify_callback
    async def _async_dts_dialog_available_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a dts dialog available event."""
        self._dts_dialog_available = params[0] if params else None

    @notify_callback
    async def _async_dts_dialog_callback(self, event: str, params: list[str]) -> None:
        """Handle a dts dialog event."""
        self._dts_dialog = params[0] if params else None

    @notify_callback
    async def _async_loudness_callback(self, event: str, params: list[str]) -> None:
        """Handle a loudness event."""
        self._loudness = params[0] if params else None

    async def register_callbacks(self) -> None:
        """Ensure that configuration is loaded from processor asynchronously."""
        _LOGGER.debug("Starting device setup")
        self._api.register_callback("DEVICE", self._async_model_callback)

        # Power callbacks
        self._api.register_callback("POWER", self._async_power_callback)
        self._api.register_callback("PWR", self._async_power_callback)

        # Volume callbacks
        self._api.register_callback("VOL", self._async_volume_callback)
        self._api.register_callback("MUTE", self._async_mute_callback)
        self._api.register_callback("MUTEON", self._async_mute_callback)
        self._api.register_callback("MUTEOFF", self._async_mute_callback)
        self._api.register_callback("MAXVOL", self._async_max_volume_callback)

        # Source callbacks
        self._api.register_callback("SRCCOUNT", self._async_source_count_callback)
        self._api.register_callback("SRC", self._async_source_callback)
        self._api.register_callback("SRCNAME", self._async_source_callback)
        self._api.register_callback("STREAMTYPE", self._async_stream_type_callback)

        # Room Perfect callbacks
        self._api.register_callback("RPVOICOUNT", self._async_voicing_count_callback)
        self._api.register_callback("RPVOI", self._async_voicing_callback)
        self._api.register_callback("VOICOUNT", self._async_voicing_count_callback)
        self._api.register_callback("VOINAME", self._async_voicing_callback)
        self._api.register_callback("VOI", self._async_voicing_callback)
        self._api.register_callback(
            "RPFOCCOUNT", self._async_focus_position_count_callback
        )
        self._api.register_callback("RPFOC", self._async_focus_position_callback)
        self._api.register_callback(
            "RPCOUNT", self._async_focus_position_count_callback
        )
        self._api.register_callback("RPNAME", self._async_focus_position_callback)
        self._api.register_callback("RP", self._async_focus_position_callback)

        # TDAI models
        self._api.register_callback("AUDIOSTATUS", self._async_audio_type_callback)

        # Multichannel device callbacks
        self._api.register_callback(
            "AUDMODECOUNT", self._async_audio_mode_count_callback
        )
        self._api.register_callback("AUDMODE", self._async_audio_mode_callback)
        self._api.register_callback("AUDIN", self._async_audio_input_callback)
        self._api.register_callback("AUDTYPE", self._async_audio_type_callback)
        self._api.register_callback("VIDIN", self._async_video_input_callback)
        self._api.register_callback("VIDTYPE", self._async_video_type_callback)
        self._api.register_callback("HDMIMAINOUT", self._async_video_output_callback)
        self._api.register_callback("LIPSYNCRANGE", self._async_lipsync_range_callback)
        self._api.register_callback("LIPSYNC", self._async_lipsync_callback)
        self._api.register_callback(
            "DTSDIALOGAVAILABLE", self._async_dts_dialog_available_callback
        )
        self._api.register_callback("DTSDIALOG", self._async_dts_dialog_callback)
        self._api.register_callback("LOUDNESS", self._async_loudness_callback)

    def _linear_to_log_interpolated_db(self, value: float) -> float:
        """Convert a linear float [0-1] to dB (0.5 decimal), using log-scale interpolation."""
        # Clamp input
        value = max(min(value, _MAX_VOLUME_LINEAR), _MIN_VOLUME_LINEAR)

        # Log scale interpolation
        log_min = math.log10(_MIN_VOLUME_LINEAR)
        log_max = math.log10(_MAX_VOLUME_LINEAR)
        log_value = math.log10(value)
        t = (log_value - log_min) / (log_max - log_min)

        # Apply curve exponent to flatten low end
        t_flat = t**_CURVE_EXPONENT

        db = MIN_VOLUME_DB + t_flat * (self._max_volume - MIN_VOLUME_DB)

        # Round to 0.5 dB steps if within range
        if MIN_VOLUME_DB < db < self._max_volume:
            db = round(db * 2) / 2
        return db

    def _db_to_linear_interpolated(self, db: float):
        """Convert dB value to a float linear value [0-1] (rounded to 2 decimals)."""
        # Clamp dB
        db = round(max(min(db, self._max_volume), MIN_VOLUME_DB), 1)

        # Compute normalized position in [0,1]
        t_flat = (db - MIN_VOLUME_DB) / (self._max_volume - MIN_VOLUME_DB)

        # Inverse of curve exponent
        t = t_flat ** (1 / _CURVE_EXPONENT)

        # Compute log-scale linear value
        log_min = math.log10(_MIN_VOLUME_LINEAR)
        log_max = math.log10(_MAX_VOLUME_LINEAR)
        log_value = log_min + t * (log_max - log_min)

        linear_value = 10**log_value
        return round(linear_value, 3)
