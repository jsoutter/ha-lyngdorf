"""Sensor entities for the Lyngdorf integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory

from .const import DOMAIN as LYNGDORF_DOMAIN
from .entity import LyngdorfEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from homeassistant.helpers.typing import StateType
    from lyngdorf.device import Receiver

_AUDIO_INPUT: Final = "audio_input"
_AUDIO_INFORMATION: Final = "audio_information"
_VIDEO_INPUT: Final = "video_input"
_VIDEO_INFORMATION: Final = "video_information"
_STREAMING_SOURCE: Final = "streaming_source"


@dataclass(frozen=True, kw_only=True)
class LyngdorfSensorEntityDescription(SensorEntityDescription):
    """Class to describe an Lyngdorf sensor entity."""

    value_fn: Callable[[Receiver], str | None]


SENSOR_TYPES: tuple[LyngdorfSensorEntityDescription, ...] = (
    LyngdorfSensorEntityDescription(
        key=_AUDIO_INPUT,
        translation_key=_AUDIO_INPUT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda receiver: receiver.audio_input,
    ),
    LyngdorfSensorEntityDescription(
        key=_AUDIO_INFORMATION,
        translation_key=_AUDIO_INFORMATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda receiver: receiver.audio_information,
    ),
    LyngdorfSensorEntityDescription(
        key=_VIDEO_INPUT,
        translation_key=_VIDEO_INPUT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda receiver: receiver.video_input,
    ),
    LyngdorfSensorEntityDescription(
        key=_VIDEO_INFORMATION,
        translation_key=_VIDEO_INFORMATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda receiver: receiver.video_information,
    ),
    LyngdorfSensorEntityDescription(
        key=_STREAMING_SOURCE,
        translation_key=_STREAMING_SOURCE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda receiver: receiver.streaming_source,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the platform from a config entry."""
    receiver: Receiver = hass.data[LYNGDORF_DOMAIN][entry.entry_id]
    async_add_entities(
        LyngdorfSensor(receiver, entry, description) for description in SENSOR_TYPES
    )


class LyngdorfSensor(LyngdorfEntity, SensorEntity):
    """Lyngdorf sensor entity."""

    entity_description: LyngdorfSensorEntityDescription

    def __init__(
        self,
        receiver: Receiver,
        config_entry: ConfigEntry,
        description: LyngdorfSensorEntityDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(receiver, config_entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._attr_unique_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return value of sensor."""
        return self.entity_description.value_fn(self._receiver)
