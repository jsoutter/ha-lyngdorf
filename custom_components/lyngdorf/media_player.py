"""Media player entity for the Lyngdorf integration."""

from __future__ import annotations

import datetime as dt
import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform


from .pylyngdorf.const import MIN_VOLUME_DB
from .pylyngdorf.music_player import MediaState, RepeatMode as LyngdorfRepeatMode

from .entity import LyngdorfCoordinator, LyngdorfEntity

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from homeassistant.helpers.entity_platform import AddEntitiesCallback

SUPPORT_LYNGDORF = (
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
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.REPEAT_SET
    | MediaPlayerEntityFeature.SHUFFLE_SET
)

ATTR_VOLUME_NATIVE = "volume_native"
ATTR_VOLUME_DB = "volume_db"
ATTR_VOLUME_MIN_DB = "volume_min_db"
ATTR_VOLUME_MAX_DB = "volume_max_db"

SERVICE_SET_VOLUME_DB = "set_volume_db"

MEDIA_PLAYER_STATE_MAP = {
    MediaState.BUFFERING: MediaPlayerState.BUFFERING,
    MediaState.PLAYING: MediaPlayerState.PLAYING,
    MediaState.PAUSED: MediaPlayerState.PAUSED,
}

REPEAT_MODE_MAP = {
    RepeatMode.ALL: LyngdorfRepeatMode.ALL,
    RepeatMode.ONE: LyngdorfRepeatMode.ONE,
}

REVERSE_REPEAT_MODE_MAP = {v: k for k, v in REPEAT_MODE_MAP.items()}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform from a config entry."""
    coordinator: LyngdorfCoordinator = entry.runtime_data

    async_add_entities([LyngdorfMediaPlayer(coordinator)], update_before_add=True)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_VOLUME_DB,
        cv.make_entity_service_schema({vol.Required("volume"): vol.Coerce(float)}),
        "async_set_volume_db",
    )


class LyngdorfMediaPlayer(LyngdorfEntity, MediaPlayerEntity):
    """Implementation of the Lyngdorf Media Player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize media player entity."""
        super().__init__(coordinator)

        self._attr_supported_features = SUPPORT_LYNGDORF
        self._attr_supported_features |= (
            self._receiver.multichannel and MediaPlayerEntityFeature.SELECT_SOUND_MODE
        )
        self._optimistic_volume: float | None = None

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if not self._receiver.power:
            self._state = MediaPlayerState.OFF
        else:
            self._state = MEDIA_PLAYER_STATE_MAP.get(
                self._receiver.media_data.state, MediaPlayerState.ON
            )
        return self._state

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if self._optimistic_volume is not None:
            _LOGGER.debug("Returning optimistic volume: %s", self._optimistic_volume)
            return self._optimistic_volume

        return self._receiver.volume_level

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
    def shuffle(self) -> bool | None:
        """Boolean if shuffle is enabled."""
        return self._receiver.media_data.shuffle or False

    @property
    def repeat(self) -> RepeatMode | str | None:
        """Return current repeat mode."""
        return REVERSE_REPEAT_MODE_MAP.get(
            self._receiver.media_data.repeat, RepeatMode.OFF
        )

    @property
    def media_content_type(self) -> MediaType | str | None:
        """Content type of current playing media."""
        if self._receiver.media_data.state == MediaState.STOPPED:
            return None
        return MediaType.MUSIC

    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        if self._receiver.media_data.state == MediaState.STOPPED:
            return None
        return self._receiver.media_data.duration

    @property
    def media_position(self) -> int | None:
        """Position of current playing media in seconds."""
        if self._receiver.media_data.state == MediaState.STOPPED:
            return None
        return self._receiver.media_data.position

    @property
    def media_position_updated_at(self) -> dt.datetime | None:
        """When was the position of the current playing media valid."""
        return self.coordinator.media_position_updated_at

    @property
    def media_image_url(self) -> str | None:
        """Image url of current playing media."""
        return self._receiver.media_data.image_url

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        return self._receiver.media_data.title

    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media, music track only."""
        return self._receiver.media_data.artist

    @property
    def media_album_name(self) -> str | None:
        """Album name of current playing media, music track only."""
        return self._receiver.media_data.album

    @property
    def media_album_artist(self) -> str | None:
        """Album artist of current playing media, music track only."""
        return self._receiver.media_data.album_artist

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return device specific state attributes."""
        state_attributes = {}
        if self._receiver.volume is not None:
            state_attributes[ATTR_VOLUME_NATIVE] = self._receiver.volume
            state_attributes[ATTR_VOLUME_DB] = self._receiver.volume

        state_attributes[ATTR_VOLUME_MIN_DB] = MIN_VOLUME_DB
        state_attributes[ATTR_VOLUME_MAX_DB] = self._receiver.max_volume

        return state_attributes

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
        self._optimistic_volume = volume
        self.async_write_ha_state()

        try:
            await self._receiver.async_set_volume_level(volume)
        except Exception as err:
            _LOGGER.error("Failed to set volume: %s", err, exc_info=True)
            self._optimistic_volume = None
            self.async_write_ha_state()
            raise

    async def async_set_volume_db(self, volume: float) -> None:
        """Set volume in decibels."""
        await self._receiver.async_set_volume(volume)

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

    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        await self._receiver.async_seek(int(position))

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Enable/disable shuffle mode."""
        await self._receiver.async_shuffle(shuffle)

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Set repeat mode."""
        repeat_mode = REPEAT_MODE_MAP.get(repeat, LyngdorfRepeatMode.OFF)
        await self._receiver.async_repeat(repeat_mode)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._optimistic_volume is not None:
            real_volume = self._receiver.volume_level

            if (
                real_volume is not None
                and abs(real_volume - self._optimistic_volume) < 0.1
            ):
                _LOGGER.debug(
                    "Clearing optimistic volume (matched): real=%s optimistic=%s",
                    real_volume,
                    self._optimistic_volume,
                )
                self._optimistic_volume = None
            else:
                _LOGGER.debug(
                    "Keeping optimistic volume: real=%s optimistic=%s",
                    real_volume,
                    self._optimistic_volume,
                )

        super()._handle_coordinator_update()
