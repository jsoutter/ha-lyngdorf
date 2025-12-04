"""Media player entity for the Lyngdorf integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)


from .entity import LyngdorfCoordinator, LyngdorfEntity

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_ATTR_VOLUME_NATIVE = "volume_native"

_SUPPORT_LYNGDORF = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the platform from a config entry."""
    coordinator: LyngdorfCoordinator = entry.runtime_data

    async_add_entities([LyngdorfMediaPlayer(coordinator)], update_before_add=True)


class LyngdorfMediaPlayer(LyngdorfEntity, MediaPlayerEntity):
    """Implementation of the Lyngdorf Media Player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize media player."""
        super().__init__(coordinator)

        self._attr_supported_features = _SUPPORT_LYNGDORF
        self._attr_supported_features |= (
            self._receiver.multichannel and MediaPlayerEntityFeature.SELECT_SOUND_MODE
        )

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if self._receiver.power:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    async def async_turn_on(self) -> None:
        """Turn on media player."""
        await self._receiver.async_power_on()

    async def async_turn_off(self) -> None:
        """Turn off media player."""
        await self._receiver.async_power_off()

    async def async_volume_up(self) -> None:
        """Volume up media player."""
        await self._receiver.async_volume_up()

    async def async_volume_down(self) -> None:
        """Volume down media player."""
        await self._receiver.async_volume_down()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self._receiver.async_set_volume_percent(volume)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute/unmute player volume."""
        await self._receiver.async_mute(mute)

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        await self._receiver.async_set_source(source)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Set Sound Mode for receiver.."""
        await self._receiver.async_set_audio_mode(sound_mode)

    async def async_media_play(self) -> None:
        """Send play command."""
        await self._receiver.async_play()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self._receiver.async_play()

    async def async_media_play_pause(self) -> None:
        """Send play/pause command."""
        await self._receiver.async_play()

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self._receiver.async_previous()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self._receiver.async_next()

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        return self._receiver.volume_percent

    @property
    def is_volume_muted(self) -> bool | None:
        """Return a boolean if volume is currently muted."""
        return self._receiver.muted

    @property
    def source(self) -> str | None:
        """Return name of the current input source."""
        return self._receiver.source

    @property
    def source_list(self) -> list[str] | None:
        """Return list of available input sources."""
        return self._receiver.sources

    @property
    def sound_mode(self) -> str | None:
        """Return name of the current sound mode."""
        return self._receiver.audio_mode

    @property
    def sound_mode_list(self) -> list[str] | None:
        """Return list of available sound modes."""
        return self._receiver.audio_modes

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return device specific state attributes."""
        state_attributes = {}
        state_attributes[_ATTR_VOLUME_NATIVE] = (
            f"{self._receiver.volume:.1f}"
            if self._receiver.volume is not None
            else None
        )
        return state_attributes
