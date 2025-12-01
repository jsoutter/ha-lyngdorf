#!/usr/bin/env python3
"""
Module implements the interface to Lyngdorf processors.

:license: MIT, see LICENSE for more details.
"""

from typing import TypeVar

import attr

from .const import (
    DEFAULT_PORT,
    DEVICE_PROTOCOLS,
    MIN_VOLUME_DB,
    DeviceModel,
    LyngdorfCommands,
)
from .device import LyngdorfDevice

T = TypeVar("T", bound="Lyngdorf")


@attr.define()
class Lyngdorf(LyngdorfDevice):
    """Implements a class with device information of the processor."""

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
        self._api.host = self._host
        self._api.port = self._port
        self._api.timeout = self._timeout

        if self._device_model is not None and self._device_model in DEVICE_PROTOCOLS:
            self._api.device_protocol = DEVICE_PROTOCOLS[self._device_model]

    async def async_send_commands(
        self, *commands: str, skip_confirmation: bool = False
    ) -> None:
        """Send commands to the processor."""
        await self._api.async_send_commands(
            *commands, skip_confirmation=skip_confirmation
        )

    def send_commands(self, *commands: str) -> None:
        """Send commands to the processor."""
        self._api.send_commands(*commands)

    async def async_connect(self) -> None:
        """Connect to the interface of the processor."""
        await self.register_callbacks()
        await self._api.async_connect()

    async def async_disconnect(self) -> None:
        """Disconnect from the interface of the processor."""
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
        """Boolean if device is multichannel processor."""
        return self._api.device_protocol.multichannel

    @property
    def power(self) -> bool | None:
        """Boolean if device is currently on."""
        return self._power

    @property
    def volume(self) -> float | None:
        """Return the volume of the device as float."""
        return self._volume

    @property
    def volume_percent(self) -> float | None:
        """Return the volume percent of the device as float."""
        return self._volume_percent

    @property
    def muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
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
    def dts_dialog_available(self) -> float | None:
        """Boolean if dts dialog is available."""
        return self._dts_dialog_available

    @property
    def dts_dialog(self) -> float | None:
        """Return the dts dialog value of the device as float."""
        return self._dts_dialog

    @property
    def loudness(self) -> float | None:
        """Boolean if loudness is enabled."""
        return self._loudness

    ##########
    # Setter #
    ##########
    async def async_power_on(self) -> None:
        """Turn on processor."""
        cmd = self._api.device_protocol.commands.get_command(LyngdorfCommands.POWER_ON)
        await self._api.async_send_commands(cmd)

    async def async_power_off(self) -> None:
        """Turn off processor."""
        cmd = self._api.device_protocol.commands.get_command(LyngdorfCommands.POWER_OFF)
        await self._api.async_send_commands(cmd)

    async def async_volume_up(self) -> None:
        """Increase volume."""
        cmd = self._api.device_protocol.commands.get_command(LyngdorfCommands.VOLUME_UP)
        await self._api.async_send_commands(cmd, skip_confirmation=True)

    async def async_volume_down(self) -> None:
        """Decrease volume."""
        cmd = self._api.device_protocol.commands.get_command(
            LyngdorfCommands.VOLUME_DOWN
        )
        await self._api.async_send_commands(cmd, skip_confirmation=True)

    async def async_set_volume(self, volume: float) -> None:
        """Set processor volume."""
        if volume < MIN_VOLUME_DB or volume > self.max_volume:
            raise ValueError(f"Invalid volume: {volume}")

        cmd = self._api.device_protocol.commands.get_command(
            LyngdorfCommands.VOLUME, volume * 10
        )
        await self._api.async_send_commands(cmd)

    async def async_set_volume_percent(self, volume: float) -> None:
        """Set processor volume percent."""
        db = self._linear_to_log_interpolated_db(volume)
        await self.async_set_volume(db)

    async def async_mute(self, mute: bool) -> None:
        """Mute processor."""
        cmd = self._api.device_protocol.commands.get_command(
            LyngdorfCommands.MUTE_ON if mute else LyngdorfCommands.MUTE_OFF
        )
        await self._api.async_send_commands(cmd)

    async def async_set_source(self, source: str) -> None:
        "Set input source of processor."
        if (index := self._sources.get_by_value(source)) is not None:
            cmd = self._api.device_protocol.commands.get_command(
                LyngdorfCommands.SOURCE, index
            )
            await self._api.async_send_commands(cmd)

    async def async_set_voicing(self, voicing: str) -> None:
        """Set voicing of processor."""
        if (index := self._voicings.get_by_value(voicing)) is not None:
            cmd = self._api.device_protocol.commands.get_command(
                LyngdorfCommands.VOICING, index
            )
            await self._api.async_send_commands(cmd)

    async def async_set_focus_position(self, focus_position: str) -> None:
        """Set focus position of processor."""
        if (index := self._focus_positions.get_by_value(focus_position)) is not None:
            cmd = self._api.device_protocol.commands.get_command(
                LyngdorfCommands.FOCUS_POSITION, index
            )
            await self._api.async_send_commands(cmd)

    async def async_set_audio_mode(self, audio_mode: str) -> None:
        """Set audio mode of processor."""
        if (index := self._audio_modes.get_by_value(audio_mode)) is not None:
            cmd = self._api.device_protocol.commands.get_command(
                LyngdorfCommands.AUDIO_MODE, index
            )
            await self._api.async_send_commands(cmd)

    async def async_set_lipsync(self, lipsync: float) -> None:
        """Set processor lipsync."""
        if lipsync < self.min_lipsync or lipsync > self.max_lipsync:
            raise ValueError(f"Invalid lipsync: {lipsync}")

        cmd = self._api.device_protocol.commands.get_command(
            LyngdorfCommands.LIPSYNC, lipsync
        )
        await self._api.async_send_commands(cmd)

    async def async_play(self) -> None:
        """Send play command."""
        cmd = self._api.device_protocol.commands.get_command(LyngdorfCommands.PLAY)
        await self._api.async_send_commands(cmd)

    async def async_previous(self) -> None:
        """Send previous track command."""
        cmd = self._api.device_protocol.commands.get_command(LyngdorfCommands.PREVIOUS)
        await self._api.async_send_commands(cmd)

    async def async_next(self) -> None:
        """Send next track command."""
        cmd = self._api.device_protocol.commands.get_command(LyngdorfCommands.NEXT)
        await self._api.async_send_commands(cmd)
