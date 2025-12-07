"""Number entities for the Lyngdorf integration."""

from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from homeassistant.const import EntityCategory, UnitOfTime, UnitOfSoundPressure
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)

from .entity import LyngdorfCoordinator, LyngdorfEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from .pylyngdorf.lyngdorf import Lyngdorf

_TRIM_MIN_BASS_TREBLE = -12.0
_TRIM_MAX_BASS_TREBLE = 12.0
_TRIM_MIN_CHANNEL = -10.0
_TRIM_MAX_CHANNEL = 10.0
_TRIM_STEP = 0.1

_LIPSYNC: Final = "lipsync"
_BASS_TRIM: Final = "bass_trim"
_TREBLE_TRIM: Final = "treble_trim"
_CENTER_TRIM: Final = "center_trim"
_HEIGHTS_TRIM: Final = "heights_trim"
_LFE_TRIM: Final = "lfe_trim"
_SURROUNDS_TRIM: Final = "surrounds_trim"


@dataclass(frozen=True, kw_only=True)
class LyngdorfNumberDescription(NumberEntityDescription):
    """Class to describe an Lyngdorf number entity."""

    native_min_value_fn: Callable[[Lyngdorf], int | float]
    native_max_value_fn: Callable[[Lyngdorf], int | float]

    value_fn: Callable[[Lyngdorf], float | None]
    set_value_fn: Callable[[Lyngdorf, float], Awaitable[None]]


SELECT_TYPES: tuple[LyngdorfNumberDescription, ...] = (
    LyngdorfNumberDescription(
        key=_LIPSYNC,
        translation_key=_LIPSYNC,
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DURATION,
        native_min_value_fn=lambda receiver: receiver.min_lipsync,
        native_max_value_fn=lambda receiver: receiver.max_lipsync,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        value_fn=lambda receiver: receiver.lipsync,
        set_value_fn=lambda receiver, value: receiver.async_set_lipsync(value),
    ),
    LyngdorfNumberDescription(
        key=_BASS_TRIM,
        translation_key=_BASS_TRIM,
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.SOUND_PRESSURE,
        native_min_value_fn=lambda _: _TRIM_MIN_BASS_TREBLE,
        native_max_value_fn=lambda _: _TRIM_MAX_BASS_TREBLE,
        native_step=_TRIM_STEP,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        value_fn=lambda receiver: receiver._bass_trim,
        set_value_fn=lambda receiver, value: receiver.async_set_bass_trim(value),
    ),
    LyngdorfNumberDescription(
        key=_TREBLE_TRIM,
        translation_key=_TREBLE_TRIM,
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.SOUND_PRESSURE,
        native_min_value_fn=lambda _: _TRIM_MIN_BASS_TREBLE,
        native_max_value_fn=lambda _: _TRIM_MAX_BASS_TREBLE,
        native_step=_TRIM_STEP,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        value_fn=lambda receiver: receiver.treble_trim,
        set_value_fn=lambda receiver, value: receiver.async_set_treble_trim(value),
    ),
    LyngdorfNumberDescription(
        key=_CENTER_TRIM,
        translation_key=_CENTER_TRIM,
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.SOUND_PRESSURE,
        native_min_value_fn=lambda _: _TRIM_MIN_CHANNEL,
        native_max_value_fn=lambda _: _TRIM_MAX_CHANNEL,
        native_step=_TRIM_STEP,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        value_fn=lambda receiver: receiver.center_trim,
        set_value_fn=lambda receiver, value: receiver.async_set_center_trim(value),
    ),
    LyngdorfNumberDescription(
        key=_HEIGHTS_TRIM,
        translation_key=_HEIGHTS_TRIM,
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.SOUND_PRESSURE,
        native_min_value_fn=lambda _: _TRIM_MIN_CHANNEL,
        native_max_value_fn=lambda _: _TRIM_MAX_CHANNEL,
        native_step=_TRIM_STEP,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        value_fn=lambda receiver: receiver.heights_trim,
        set_value_fn=lambda receiver, value: receiver.async_set_heights_trim(value),
    ),
    LyngdorfNumberDescription(
        key=_LFE_TRIM,
        translation_key=_LFE_TRIM,
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.SOUND_PRESSURE,
        native_min_value_fn=lambda _: _TRIM_MIN_CHANNEL,
        native_max_value_fn=lambda _: _TRIM_MAX_CHANNEL,
        native_step=_TRIM_STEP,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        value_fn=lambda receiver: receiver.lfe_trim,
        set_value_fn=lambda receiver, value: receiver.async_set_lfe_trim(value),
    ),
    LyngdorfNumberDescription(
        key=_SURROUNDS_TRIM,
        translation_key=_SURROUNDS_TRIM,
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.SOUND_PRESSURE,
        native_min_value_fn=lambda _: _TRIM_MIN_CHANNEL,
        native_max_value_fn=lambda _: _TRIM_MAX_CHANNEL,
        native_step=_TRIM_STEP,
        native_unit_of_measurement=UnitOfSoundPressure.DECIBEL,
        value_fn=lambda receiver: receiver.surrounds_trim,
        set_value_fn=lambda receiver, value: receiver.async_set_surrounds_trim(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the platform from a config entry."""
    coordinator: LyngdorfCoordinator = entry.runtime_data

    async_add_entities(
        LyngdorfNumber(coordinator, description)
        for description in SELECT_TYPES
        if coordinator.receiver.multichannel
    )


class LyngdorfNumber(LyngdorfEntity, NumberEntity):
    """Lyngdorf select entity."""

    entity_description: LyngdorfNumberDescription

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        description: LyngdorfNumberDescription,
    ) -> None:
        """Initialize number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._attr_unique_id}_{description.key}"

    @property
    def available(self):
        """Entity available only when device is on."""
        return self._receiver.power

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return self.entity_description.value_fn(self._receiver)

    @property
    def native_max_value(self) -> float:
        """Return the native max value of the number."""
        return self.entity_description.native_max_value_fn(self._receiver)

    @property
    def native_min_value(self) -> float:
        """Return the native min value of the number."""
        return self.entity_description.native_min_value_fn(self._receiver)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.entity_description.set_value_fn(self._receiver, int(value))
