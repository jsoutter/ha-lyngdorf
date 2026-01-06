#!/usr/bin/env python3
"""
Module implements the interface to Lyngdorf devices.

:license: MIT, see LICENSE for more details.
"""

from typing import Any, TypeVar

import attr

from .config import DEVICE_PROTOCOLS
from .const import (
    DEFAULT_PORT,
    MIN_VOLUME_DB,
    TRIM_RANGE_BASS_TREBLE,
    TRIM_RANGE_CHANNEL,
    DeviceModel,
    LyngdorfCommand,
)
from .device import LyngdorfDevice

T = TypeVar("T", bound="Lyngdorf")


def validate_trim(trim: float, range_: float) -> None:
    """Validate trim value within dB range."""
    if abs(trim) > range_:
        raise ValueError(
            f"Invalid trim value {trim}. Must be between -{range_} and +{range_}."
        )


@attr.define()
class Lyngdorf(LyngdorfDevice):
    """Implements a class with device information."""

    _host: str = attr.field(converter=str)
    _port: int = attr.field(converter=int)
    _timeout: float = attr.field(converter=float)
    _device_model: DeviceModel | None = attr.field(default=None)

    def __new__(
        cls: type[T],
    ) -> T:
        raise RuntimeError("Use Lyngdorf.create() instead of direct instantiation")

    @classmethod
    def create(
        cls: type[T],
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = 2.0,
        device_model: DeviceModel | None = None,
    ) -> T:
        instance = object.__new__(cls)
        cls.__init__(instance, host, port, timeout, device_model)
        return instance

    def __attrs_post_init__(self) -> None:
        """Initialise attributes."""
        super().__attrs_post_init__()
        self._api.host = self._host
        self._api.port = self._port
        self._api.timeout = self._timeout

        if self._device_model is not None and self._device_model in DEVICE_PROTOCOLS:
            self._api.device_protocol = DEVICE_PROTOCOLS[self._device_model]

    async def async_connect(self) -> None:
        """Connect to the interface of the device."""
        self._register_callbacks()
        await self._api.async_connect()

    async def async_disconnect(self) -> None:
        """Disconnect from the interface of the device."""
        await self._api.async_disconnect()

    ##############
    # Properties #
    ##############
    @property
    def host(self) -> str:
        """Return the host of the device as string."""
        return self._host

    @property
    def model(self) -> DeviceModel | None:
        """Return the model of the device as string."""
        return self._model

    @property
    def multichannel(self) -> bool:
        """Return True if device is multichannel device."""
        return self._api.device_protocol.multichannel

    @property
    def power(self) -> bool:
        """Return True if device is currently on."""
        return self._power or False

    @property
    def available(self):
        """Return True if device is available."""
        return self._api.healthy

    @property
    def volume(self) -> float | None:
        """Return the volume of the device as float."""
        return self._volume

    @property
    def volume_level(self) -> float | None:
        """Return the volume level (0.0–1.0) of the device as float."""
        return self._volume_level

    @property
    def muted(self) -> bool | None:
        """Return True if volume is currently muted."""
        return self._muted

    @property
    def max_volume(self) -> float:
        """Return the maximum volume of the device as float."""
        return self._max_volume

    @property
    def sources(self) -> list[str]:
        """Return the sources of the device as list."""
        return self._sources.get_all()

    @property
    def source(self) -> str | None:
        """Return the current source of the device."""
        return self._source

    @property
    def stream_type(self) -> str | None:
        """Return the current stream type of the device as string."""
        return self._stream_type

    @property
    def voicings(self) -> list[str]:
        """Return the voicings of the device as list."""
        return self._voicings.get_all()

    @property
    def voicing(self) -> str | None:
        """Return the current voicing of the device."""
        return self._voicing

    @property
    def focus_positions(self) -> list[str]:
        """Return the focus positions of the device as list."""
        return self._focus_positions.get_all()

    @property
    def focus_position(self) -> str | None:
        """Return the current focus position of the device."""
        return self._focus_position

    @property
    def audio_modes(self) -> list[str]:
        """Return the audio modes of the device as list."""
        return self._audio_modes.get_all()

    @property
    def audio_mode(self) -> str | None:
        """Return the current audio mode of the device."""
        return self._audio_mode

    @property
    def audio_input(self) -> str | None:
        """Return the current audio input of the device as string."""
        return self._audio_input

    @property
    def audio_type(self) -> str | None:
        """Return the current audio type of the device as string."""
        return self._audio_type

    @property
    def video_input(self) -> str | None:
        """Return the current video input of the device as string."""
        return self._video_input

    @property
    def video_type(self) -> str | None:
        """Return the current video type of the device as string."""
        return self._video_type

    @property
    def video_output(self) -> str | None:
        """Return the main video output of the device as string."""
        return self._video_output

    @property
    def min_lipsync(self) -> int:
        """Return the minimum lipsync of the device as int."""
        return self._min_lipsync

    @property
    def max_lipsync(self) -> int:
        """Return the maximum lipsync of the device as int."""
        return self._max_lipsync

    @property
    def lipsync(self) -> int:
        """Return the lipsync of the device as int."""
        return self._lipsync

    @property
    def dts_dialog_available(self) -> bool | None:
        """Return True if dts dialog is available."""
        return self._dts_dialog_available

    @property
    def dts_dialog(self) -> float | None:
        """Return the dts dialog value of the device as float."""
        return self._dts_dialog

    @property
    def loudness(self) -> bool | None:
        """Return True if loudness is enabled."""
        return self._loudness

    @property
    def bass_trim(self) -> float | None:
        """Return the bass trim of the device as float."""
        return self._bass_trim

    @property
    def treble_trim(self) -> float | None:
        """Return the treble trim of the device as float."""
        return self._treble_trim

    @property
    def center_trim(self) -> float | None:
        """Return the center channel trim of the device as float."""
        return self._center_trim

    @property
    def heights_trim(self) -> float | None:
        """Return the height channels trim of the device as float."""
        return self._heights_trim

    @property
    def lfe_trim(self) -> float | None:
        """Return the lfe channel trim of the device as float."""
        return self._lfe_trim

    @property
    def surrounds_trim(self) -> float | None:
        """Return the surround channels trim of the device as float."""
        return self._surrounds_trim

    ##########
    # Setter #
    ##########
    async def async_send_command(
        self,
        command: str | LyngdorfCommand,
        arg: Any | None = None,
        skip_confirmation: bool = False,
    ) -> None:
        """Send command to the device."""
        cmd = (
            self._api.device_protocol.commands.get_command(command)
            if isinstance(command, LyngdorfCommand)
            else self._api.device_protocol.commands.get_command_by_name(command)
        )

        await self._api.async_send_commands(
            cmd.format(arg), skip_confirmation=skip_confirmation
        )

    async def async_power_on(self) -> None:
        """Turn on device."""
        await self.async_send_command(LyngdorfCommand.POWER_ON)

    async def async_power_off(self) -> None:
        """Turn off device."""
        await self.async_send_command(LyngdorfCommand.POWER_OFF)

    async def async_volume_up(self) -> None:
        """Increase volume."""
        await self.async_send_command(LyngdorfCommand.VOLUME_UP, skip_confirmation=True)

    async def async_volume_down(self) -> None:
        """Decrease volume."""
        await self.async_send_command(
            LyngdorfCommand.VOLUME_DOWN, skip_confirmation=True
        )

    async def async_set_volume(self, volume: float) -> None:
        """Set device volume."""
        if volume < MIN_VOLUME_DB or volume > self.max_volume:
            raise ValueError(f"Invalid volume: {volume}")

        await self.async_send_command(LyngdorfCommand.VOLUME, int(volume * 10))

    async def async_set_volume_level(self, volume: float) -> None:
        """Set device volume level (0.0–1.0)."""
        db = self._linear_to_db_flattened(volume)
        await self.async_set_volume(db)

    async def async_mute(self, mute: bool) -> None:
        """Mute or unmute the device."""
        await self.async_send_command(
            LyngdorfCommand.MUTE_ON if mute else LyngdorfCommand.MUTE_OFF
        )

    async def async_set_source(self, source: str) -> None:
        "Set input source of device."
        if (index := self._sources.get_by_value(source)) is not None:
            await self.async_send_command(LyngdorfCommand.SOURCE, index)

    async def async_set_voicing(self, voicing: str) -> None:
        """Set voicing of device."""
        if (index := self._voicings.get_by_value(voicing)) is not None:
            await self.async_send_command(LyngdorfCommand.VOICING, index)

    async def async_set_focus_position(self, focus_position: str) -> None:
        """Set focus position of device."""
        if (index := self._focus_positions.get_by_value(focus_position)) is not None:
            await self.async_send_command(LyngdorfCommand.FOCUS_POSITION, index)

    async def async_set_audio_mode(self, audio_mode: str) -> None:
        """Set audio mode of device."""
        if (index := self._audio_modes.get_by_value(audio_mode)) is not None:
            await self.async_send_command(LyngdorfCommand.AUDIO_MODE, index)

    async def async_set_lipsync(self, lipsync: int) -> None:
        """Set device lipsync."""
        if lipsync < self.min_lipsync or lipsync > self.max_lipsync:
            raise ValueError(f"Invalid lipsync: {lipsync}")

        await self.async_send_command(LyngdorfCommand.LIPSYNC, lipsync)

    async def async_play(self) -> None:
        """Send play command."""
        await self.async_send_command(LyngdorfCommand.PLAY)

    async def async_previous(self) -> None:
        """Send previous track command."""
        await self.async_send_command(LyngdorfCommand.PREVIOUS)

    async def async_next(self) -> None:
        """Send next track command."""
        await self.async_send_command(LyngdorfCommand.NEXT)

    async def _set_trim(
        self, command: LyngdorfCommand, trim: float, range_: float
    ) -> None:
        validate_trim(trim, range_)
        await self.async_send_command(command, int(trim * 10))

    async def async_set_bass_trim(self, trim: float) -> None:
        """Set bass trim."""
        await self._set_trim(LyngdorfCommand.BASS_TRIM, trim, TRIM_RANGE_BASS_TREBLE)

    async def async_set_treble_trim(self, trim: float) -> None:
        """Set treble trim."""
        await self._set_trim(LyngdorfCommand.TREBLE_TRIM, trim, TRIM_RANGE_BASS_TREBLE)

    async def async_set_center_trim(self, trim: float) -> None:
        """Set center channel trim."""
        await self._set_trim(LyngdorfCommand.CENTER_TRIM, trim, TRIM_RANGE_CHANNEL)

    async def async_set_heights_trim(self, trim: float) -> None:
        """Set height channels trim."""
        await self._set_trim(LyngdorfCommand.HEIGHTS_TRIM, trim, TRIM_RANGE_CHANNEL)

    async def async_set_lfe_trim(self, trim: float) -> None:
        """Set lfe channel trim."""
        await self._set_trim(LyngdorfCommand.LFE_TRIM, trim, TRIM_RANGE_CHANNEL)

    async def async_set_surrounds_trim(self, trim: float) -> None:
        """Set surround channels trim."""
        await self._set_trim(LyngdorfCommand.SURROUNDS_TRIM, trim, TRIM_RANGE_CHANNEL)
