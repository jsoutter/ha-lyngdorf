"""Select entities for the Lyngdorf integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .const import DOMAIN as LYNGDORF_DOMAIN
from .entity import LyngdorfEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from lyngdorf.device import Receiver

_FOCUS_POSITION: Final = "focus_position"
_VOICING: Final = "voicing"


@dataclass(frozen=True, kw_only=True)
class LyngdorfSelectDescription(SelectEntityDescription):
    """Class to describe an Lyngdorf select entity."""

    value_fn: Callable[[Receiver], str | None]
    options_fn: Callable[[Receiver], list[str]]
    set_value_fn: Callable[[Receiver, str], None]


SELECT_TYPES: tuple[LyngdorfSelectDescription, ...] = (
    LyngdorfSelectDescription(
        key=_FOCUS_POSITION,
        translation_key=_FOCUS_POSITION,
        value_fn=lambda receiver: receiver.room_perfect_position,
        options_fn=lambda receiver: receiver.available_room_perfect_positions,
        set_value_fn=lambda receiver, value: setattr(
            receiver, "room_perfect_position", value
        ),
    ),
    LyngdorfSelectDescription(
        key=_VOICING,
        translation_key=_VOICING,
        value_fn=lambda receiver: receiver.voicing,
        options_fn=lambda receiver: receiver.available_voicings,
        set_value_fn=lambda receiver, value: setattr(receiver, "voicing", value),
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
        LyngdorfSelect(receiver, entry, description) for description in SELECT_TYPES
    )


class LyngdorfSelect(LyngdorfEntity, SelectEntity):
    """Lyngdorf select entity."""

    entity_description: LyngdorfSelectDescription

    def __init__(
        self,
        receiver: Receiver,
        config_entry: ConfigEntry,
        description: LyngdorfSelectDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(receiver, config_entry)
        self.entity_description = description
        self._attr_unique_id = f"{self._attr_unique_id}_{description.key}"

    def select_option(self, option: str) -> None:
        """Handle the selection of an option."""
        self.entity_description.set_value_fn(self._receiver, option)

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return self.entity_description.options_fn(self._receiver)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        return self.entity_description.value_fn(self._receiver)
