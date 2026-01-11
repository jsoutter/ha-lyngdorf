#!/usr/bin/env python3
"""
Module implements the device class for Lyngdorf devices.

:license: MIT, see LICENSE for more details.
"""

import logging
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

import attr

from .api import LyngdorfApi
from .config import DEFAULT_PROTOCOL, DEVICE_PROTOCOLS
from .const import (
    DEFAULT_MAX_LIPSYNC,
    DEFAULT_MAX_VOLUME_DB,
    DEFAULT_MIN_LIPSYNC,
    LYNGDORF_ATTR_SETATTR,
    DeviceModel,
    LyngdorfQuery,
)
from .utils import (
    FixedSizeDict,
    compute_alpha,
    convert_on_off_bool,
    convert_volume,
    db_to_linear_flattened,
    linear_to_db_flattened,
    lookup_description,
)

_LOGGER = logging.getLogger(__name__)

_CALLBACK_MAP: dict[str, str] = {
    # Device information
    "DEVICE": "_async_model_callback",
    # Power
    "POWER": "_async_power_callback",
    "PWR": "_async_power_callback",
    # Volume / Mute
    "VOL": "_async_volume_callback",
    "MUTE": "_async_mute_callback",
    "MUTEON": "_async_mute_callback",
    "MUTEOFF": "_async_mute_callback",
    "MAXVOL": "_async_max_volume_callback",
    # Source selection
    "SRCCOUNT": "_async_source_count_callback",
    "SRC": "_async_source_callback",
    "SRCNAME": "_async_source_callback",
    "STREAMTYPE": "_async_stream_type_callback",
    # RoomPerfect: Voicings
    "RPVOICOUNT": "_async_voicing_count_callback",
    "RPVOI": "_async_voicing_callback",
    "VOICOUNT": "_async_voicing_count_callback",
    "VOINAME": "_async_voicing_callback",
    "VOI": "_async_voicing_callback",
    # RoomPerfect: Focus positions
    "RPFOCCOUNT": "_async_focus_position_count_callback",
    "RPFOC": "_async_focus_position_callback",
    "RPCOUNT": "_async_focus_position_count_callback",
    "RPNAME": "_async_focus_position_callback",
    "RP": "_async_focus_position_callback",
    # Audio status (TDAI models)
    "AUDIOSTATUS": "_async_audio_type_callback",
    # Multichannel: Audio modes
    "AUDMODECOUNT": "_async_audio_mode_count_callback",
    "AUDMODE": "_async_audio_mode_callback",
    # Audio/Video IO
    "AUDIN": "_async_audio_input_callback",
    "AUDTYPE": "_async_audio_type_callback",
    "VIDIN": "_async_video_input_callback",
    "VIDTYPE": "_async_video_type_callback",
    "HDMIMAINOUT": "_async_video_output_callback",
    # Lip sync
    "LIPSYNCRANGE": "_async_lipsync_range_callback",
    "LIPSYNC": "_async_lipsync_callback",
    # DTS Dialog Control
    "DTSDIALOGAVAILABLE": "_async_dts_dialog_available_callback",
    "DTSDIALOG": "_async_dts_dialog_callback",
    # Loudness / Tone controls
    "LOUDNESS": "_async_loudness_callback",
    "TRIMBASS": "_async_bass_trim_callback",
    "TRIMTREBLE": "_async_treble_trim_callback",
    "TRIMCENTER": "_async_center_trim_callback",
    "TRIMHEIGHT": "_async_heights_trim_callback",
    "TRIMLFE": "_async_lfe_trim_callback",
    "TRIMSURRS": "_async_surrounds_trim_callback",
}


def notify_callback(
    event: LyngdorfQuery,
    attr_getter: Callable[["LyngdorfDevice"], Any] | None = None,
):
    """Run notification callback, optionally when value has changed."""

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, None]]:
        @wraps(func)
        async def wrapper(self: "LyngdorfDevice", *args: Any, **kwargs: Any) -> Any:
            old_value = attr_getter(self) if attr_getter else None
            result = await func(self, *args, **kwargs)
            if attr_getter:
                new_value = attr_getter(self)
                if old_value != new_value:
                    self.run_notify_callback(event)
            else:
                self.run_notify_callback(event)
            return result

        return wrapper

    return decorator


@attr.define(kw_only=True, on_setattr=LYNGDORF_ATTR_SETATTR)
class LyngdorfDevice:
    """Implements a class with device information."""

    _api: LyngdorfApi = attr.field(
        factory=lambda: LyngdorfApi(device_protocol=DEFAULT_PROTOCOL),
        validator=attr.validators.instance_of(LyngdorfApi),
    )
    _notification_callback: Callable[[LyngdorfQuery], None] | None = attr.field(
        default=None
    )
    # Common properties
    _model: DeviceModel | None = attr.field(default=None)
    _multichannel: bool = attr.field(default=False)
    _power: bool | None = attr.field(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _volume: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _volume_level: float | None = attr.field(default=None)
    _muted: bool = attr.field(
        converter=attr.converters.optional(convert_on_off_bool), default=True
    )
    _max_volume: float = attr.field(
        converter=attr.converters.optional(convert_volume),
        default=DEFAULT_MAX_VOLUME_DB * 10,
    )
    _alpha: float = attr.field(default=1.0)

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
    _bass_trim: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _treble_trim: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _center_trim: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _heights_trim: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _lfe_trim: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _surrounds_trim: float | None = attr.field(
        converter=attr.converters.optional(convert_volume), default=None
    )

    def __attrs_post_init__(self) -> None:
        """Initialise attributes."""
        self._alpha = compute_alpha(self._max_volume)

    def _register_callbacks(self) -> None:
        """Register all known event callbacks."""
        _LOGGER.debug("Register event callbacks")
        for event, callback_name in _CALLBACK_MAP.items():
            callback_fn = getattr(self, callback_name)
            self._api.register_callback(event, callback_fn)

    def set_notification_callback(self, callback: Callable[[LyngdorfQuery], None]):
        self._notification_callback = callback

    def run_notify_callback(self, event: LyngdorfQuery):
        if self._notification_callback:
            self._notification_callback(event)

    async def wait_while_connected(self) -> None:
        """Block while the connection is enabled."""
        await self._api.wait_while_connected()

    @notify_callback(LyngdorfQuery.DEVICE)
    async def _async_model_callback(self, event: str, params: list[str]) -> None:
        """Handle a device model event."""
        self._model = (
            DeviceModel(params[0])
            if params and params[0] in DeviceModel._value2member_map_
            else None
        )

        if self._model and self._api.device_protocol is DEFAULT_PROTOCOL:
            self._api.device_protocol = DEVICE_PROTOCOLS[self._model]

    @notify_callback(LyngdorfQuery.POWER)
    async def _async_power_callback(self, event: str, params: list[str]) -> None:
        """Handle a power change event."""
        self._power = params[0] if params else None

    @notify_callback(LyngdorfQuery.VOLUME)
    async def _async_volume_callback(self, event: str, params: list[str]) -> None:
        """Handle a volume change event."""
        self._volume = params[0] if params else None
        volume = self._volume
        self._volume_level = self._db_to_linear_flattened(volume) if volume else None

    @notify_callback(LyngdorfQuery.MUTE)
    async def _async_mute_callback(self, event: str, params: list[str]) -> None:
        """Handle a muting change event."""
        self._muted = params[0] if params else event[4:]

    @notify_callback(LyngdorfQuery.MAX_VOLUME)
    async def _async_max_volume_callback(self, event: str, params: list[str]) -> None:
        """Handle a max volume event."""
        if params:
            self._max_volume = params[0]
            self._alpha = compute_alpha(self._max_volume)

    async def _async_source_count_callback(self, event: str, params: list[str]) -> None:
        """Handle a source count event."""
        if params:
            self._sources.set_size(int(params[0]))

    @notify_callback(LyngdorfQuery.SOURCE, lambda self: self._source)
    async def _async_source_callback(self, event: str, params: list[str]) -> None:
        """Handle a source event."""
        if params:
            source_id = int(params[0])
            if self._sources.is_full():
                self._source = self._sources.get_by_id(source_id)
            else:
                self._sources.add(source_id, params[1])
                if self._sources.is_full():
                    self.run_notify_callback(LyngdorfQuery.SOURCE_LIST)

    @notify_callback(LyngdorfQuery.STREAM_TYPE, lambda self: self._stream_type)
    async def _async_stream_type_callback(self, event: str, params: list[str]) -> None:
        """Handle a stream type change event."""
        self._stream_type = (
            lookup_description(params[0], self._api.device_protocol.stream_types)
            if params
            else None
        )

    async def _async_voicing_count_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a voicing count event."""
        if params:
            self._voicings.set_size(int(params[0]))

    @notify_callback(LyngdorfQuery.VOICING, lambda self: self._voicing)
    async def _async_voicing_callback(self, event: str, params: list[str]) -> None:
        """Handle a voicing event."""
        if params:
            voicing_id = int(params[0])
            if self._voicings.is_full():
                self._voicing = self._voicings.get_by_id(voicing_id)
            else:
                self._voicings.add(voicing_id, params[1])
                if self._voicings.is_full():
                    self.run_notify_callback(LyngdorfQuery.VOICING_LIST)

    async def _async_focus_position_count_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a focus position count event."""
        if params:
            self._focus_positions.set_size(int(params[0]))

    @notify_callback(LyngdorfQuery.FOCUS_POSITION, lambda self: self._focus_position)
    async def _async_focus_position_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a focus position event."""
        if params:
            focus_position_id = int(params[0])
            if self._focus_positions.is_full():
                self._focus_position = self._focus_positions.get_by_id(
                    focus_position_id
                )
            else:
                self._focus_positions.add(focus_position_id, params[1])
                if self._focus_positions.is_full():
                    self.run_notify_callback(LyngdorfQuery.FOCUS_POSITION_LIST)

    async def _async_audio_mode_count_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a audio mode count event."""
        if params:
            self._audio_modes.set_size(int(params[0]))

    @notify_callback(LyngdorfQuery.AUDIO_MODE, lambda self: self._audio_mode)
    async def _async_audio_mode_callback(self, event: str, params: list[str]) -> None:
        """Handle a audio mode event."""
        if params:
            audio_mode_id = int(params[0])
            if self._audio_modes.is_full():
                self._audio_mode = self._audio_modes.get_by_id(audio_mode_id)
            else:
                self._audio_modes.add(audio_mode_id, params[1])
                if self._audio_modes.is_full():
                    self.run_notify_callback(LyngdorfQuery.AUDIO_MODE_LIST)

    @notify_callback(LyngdorfQuery.AUDIO_INPUT, lambda self: self._audio_input)
    async def _async_audio_input_callback(self, event: str, params: list[str]) -> None:
        """Handle a audio input change event."""
        self._audio_input = (
            lookup_description(params[0], self._api.device_protocol.audio_inputs)
            if params
            else None
        )

    @notify_callback(LyngdorfQuery.AUDIO_TYPE, lambda self: self._audio_type)
    async def _async_audio_type_callback(self, event: str, params: list[str]) -> None:
        """Handle a audio type change event."""
        self._audio_type = ", ".join(params) if params else None

    @notify_callback(LyngdorfQuery.VIDEO_INPUT, lambda self: self._video_input)
    async def _async_video_input_callback(self, event: str, params: list[str]) -> None:
        """Handle a video input event."""
        self._video_input = (
            lookup_description(params[0], self._api.device_protocol.video_inputs)
            if params
            else None
        )

    @notify_callback(LyngdorfQuery.VIDEO_TYPE, lambda self: self._video_type)
    async def _async_video_type_callback(self, event: str, params: list[str]) -> None:
        """Handle a video type change event."""
        self._video_type = params[0] if params else None

    @notify_callback(LyngdorfQuery.VIDEO_OUTPUT, lambda self: self._video_output)
    async def _async_video_output_callback(self, event: str, params: list[str]) -> None:
        """Handle a video output event."""
        self._video_output = (
            lookup_description(params[0], self._api.device_protocol.video_outputs)
            if params
            else None
        )

    @notify_callback(LyngdorfQuery.LIPSYNC_RANGE)
    async def _async_lipsync_range_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a lipsync range event."""
        if len(params) == 2:
            self._min_lipsync = params[0]
            self._max_lipsync = params[1]

    @notify_callback(LyngdorfQuery.LIPSYNC)
    async def _async_lipsync_callback(self, event: str, params: list[str]) -> None:
        """Handle a lipsync event."""
        self._lipsync = params[0] if params else None

    @notify_callback(LyngdorfQuery.DTS_DIALOG_AVAILABLE)
    async def _async_dts_dialog_available_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a dts dialog available event."""
        self._dts_dialog_available = params[0] if params else None

    @notify_callback(LyngdorfQuery.DTS_DIALOG)
    async def _async_dts_dialog_callback(self, event: str, params: list[str]) -> None:
        """Handle a dts dialog event."""
        self._dts_dialog = params[0] if params else None

    @notify_callback(LyngdorfQuery.LOUDNESS)
    async def _async_loudness_callback(self, event: str, params: list[str]) -> None:
        """Handle a loudness event."""
        self._loudness = params[0] if params else None

    @notify_callback(LyngdorfQuery.BASS_TRIM)
    async def _async_bass_trim_callback(self, event: str, params: list[str]) -> None:
        """Handle a bass trim event."""
        self._bass_trim = params[0] if params else None

    @notify_callback(LyngdorfQuery.TREBLE_TRIM)
    async def _async_treble_trim_callback(self, event: str, params: list[str]) -> None:
        """Handle a treble trim event."""
        self._treble_trim = params[0] if params else None

    @notify_callback(LyngdorfQuery.CENTER_TRIM)
    async def _async_center_trim_callback(self, event: str, params: list[str]) -> None:
        """Handle a center trim event."""
        self._center_trim = params[0] if params else None

    @notify_callback(LyngdorfQuery.HEIGHTS_TRIM)
    async def _async_heights_trim_callback(self, event: str, params: list[str]) -> None:
        """Handle a height trim event."""
        self._heights_trim = params[0] if params else None

    @notify_callback(LyngdorfQuery.LFE_TRIM)
    async def _async_lfe_trim_callback(self, event: str, params: list[str]) -> None:
        """Handle a lfe trim event."""
        self._lfe_trim = params[0] if params else None

    @notify_callback(LyngdorfQuery.SURROUNDS_TRIM)
    async def _async_surrounds_trim_callback(
        self, event: str, params: list[str]
    ) -> None:
        """Handle a surround trim event."""
        self._surrounds_trim = params[0] if params else None

    def _linear_to_db_flattened(self, value: float) -> float:
        """Convert a linear float [0-1] to dB (0.5 decimal)."""
        return linear_to_db_flattened(value, self._max_volume, self._alpha)

    def _db_to_linear_flattened(self, db: float) -> float:
        """Convert dB value to a float linear value [0-1] (rounded to 3 decimals)."""
        return db_to_linear_flattened(db, self._max_volume, self._alpha)
