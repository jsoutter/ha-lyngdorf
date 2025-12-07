"""Select entities for the Lyngdorf integration."""

from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .entity import LyngdorfCoordinator, LyngdorfEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from .pylyngdorf.lyngdorf import Lyngdorf

_FOCUS_POSITION: Final = "focus_position"
_VOICING: Final = "voicing"


@dataclass(frozen=True, kw_only=True)
class LyngdorfSelectDescription(SelectEntityDescription):
    """Class to describe an Lyngdorf select entity."""

    value_fn: Callable[[Lyngdorf], str | None]
    options_fn: Callable[[Lyngdorf], list[str]]
    set_value_fn: Callable[[Lyngdorf, str], Awaitable[None]]


SELECT_TYPES: tuple[LyngdorfSelectDescription, ...] = (
    LyngdorfSelectDescription(
        key=_FOCUS_POSITION,
        translation_key=_FOCUS_POSITION,
        value_fn=lambda receiver: receiver.focus_position,
        options_fn=lambda receiver: receiver.focus_positions,
        set_value_fn=lambda receiver, value: receiver.async_set_focus_position(value),
    ),
    LyngdorfSelectDescription(
        key=_VOICING,
        translation_key=_VOICING,
        value_fn=lambda receiver: receiver.voicing,
        options_fn=lambda receiver: receiver.voicings,
        set_value_fn=lambda receiver, value: receiver.async_set_voicing(value),
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
        LyngdorfSelect(coordinator, description) for description in SELECT_TYPES
    )


class LyngdorfSelect(LyngdorfEntity, SelectEntity):
    """Lyngdorf select entity."""

    entity_description: LyngdorfSelectDescription

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        description: LyngdorfSelectDescription,
    ) -> None:
        """Initialize select entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._attr_unique_id}_{description.key}"

    @property
    def available(self):
        """Entity available only when device is on."""
        return self._receiver.power

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of an option."""
        await self.entity_description.set_value_fn(self._receiver, option)

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return self.entity_description.options_fn(self._receiver)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        return self.entity_description.value_fn(self._receiver)
