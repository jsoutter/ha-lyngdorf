"""Lyngdorf Media Player."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Final

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)

from .const import DOMAIN as LYNGDORF_DOMAIN
from .entity import LyngdorfEntity

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from lyngdorf.device import Receiver

_ATTR_VOLUME_NATIVE = "volume_native"
_DEFAULT_MIN_LINEAR: Final = 1e-2
_DEFAULT_MAX_LINEAR: Final = 1.0
_DEFAULT_MIN_DB: Final = -99.9
_DEFAULT_MAX_DB: Final = 24.0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    receiver: Receiver = hass.data[LYNGDORF_DOMAIN][entry.entry_id]

    async_add_entities([LyngdorfMediaPlayer(receiver, entry)], update_before_add=True)


class LyngdorfMediaPlayer(LyngdorfEntity, MediaPlayerEntity):
    """Implementation of the Lyngdorf Media Player."""

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )
    _attr_name = None

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if self._receiver.power_on:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    def turn_off(self) -> None:
        """Turn off media player."""
        self._receiver.power_on = False

    def turn_on(self) -> None:
        """Turn on media player."""
        self._receiver.power_on = True

    def volume_up(self) -> None:
        """Volume up media player."""
        self._receiver.volume_up()

    def volume_down(self) -> None:
        """Volume down media player."""
        self._receiver.volume_down()

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        self._receiver.volume = self.linear_to_log_interpolated_db(volume)

    def mute_volume(self, mute: bool) -> None:  # noqa: FBT001
        """Mute/unmute player volume."""
        self._receiver.mute_enabled = mute

    def select_source(self, source: str) -> None:
        """Select input source."""
        self._receiver.source = source

    def select_sound_mode(self, sound_mode: str) -> None:
        """Set Sound Mode for Receiver.."""
        self._receiver.sound_mode = sound_mode

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        return self.db_to_linear_interpolated(self._receiver.volume)

    @property
    def is_volume_muted(self) -> bool:
        """Return a boolean if volume is currently muted."""
        return self._receiver.mute_enabled

    @property
    def source(self) -> str | None:
        """Return name of the current input source."""
        return self._receiver.source

    @property
    def source_list(self) -> list[str] | None:
        """Return list of available input sources."""
        return self._receiver.available_sources

    @property
    def sound_mode(self) -> str | None:
        """Return name of the current sound mode."""
        return self._receiver.sound_mode

    @property
    def sound_mode_list(self) -> list[str] | None:
        """Return list of available sound modes."""
        return self._receiver.available_sound_modes

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return device specific state attributes."""
        state_attributes = {}
        if isinstance(self._receiver.volume, float):
            state_attributes[_ATTR_VOLUME_NATIVE] = f"{self._receiver.volume:.1f}"
        return state_attributes

    def linear_to_log_interpolated_db(
        self,
        value: float,
        min_input=_DEFAULT_MIN_LINEAR,
        max_input=_DEFAULT_MAX_LINEAR,
        min_db=_DEFAULT_MIN_DB,
        max_db=_DEFAULT_MAX_DB,
    ) -> float:
        """Convert a linear float [0–1] to dB (0.5 decimal), using log-scale interpolation."""

        # Clamp input within allowed range
        value = max(min(value, max_input), min_input)

        # Compute dB from log-scaled interpolation
        log_min = math.log10(min_input)
        log_max = math.log10(max_input)
        log_value = math.log10(value)
        t = (log_value - log_min) / (log_max - log_min)
        db = min_db + t * (max_db - min_db)

        # Apply 0.5 dB rounding only if within range
        if min_db < db < max_db:
            db = round(db * 2) / 2

        return db

    def db_to_linear_interpolated(
        self,
        db: float,
        min_input=_DEFAULT_MIN_LINEAR,
        max_input=_DEFAULT_MAX_LINEAR,
        min_db=_DEFAULT_MIN_DB,
        max_db=_DEFAULT_MAX_DB,
    ):
        """Convert dB value to a float linear value [0–1] (rounded to 2 decimals)."""

        # Clamp dB within allowed range
        db = round(max(min(db, max_db), min_db), 1)

        # Compute log scale position
        t = (db - min_db) / (max_db - min_db)
        log_min = math.log10(min_input)
        log_max = math.log10(max_input)
        log_value = log_min + t * (log_max - log_min)

        # Convert back to linear value
        linear_value = 10**log_value
        return round(linear_value, 2)
