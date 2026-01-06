"""Remote entity for the Lyngdorf integration."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity

from .entity import LyngdorfCoordinator, LyngdorfEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform from a config entry."""
    coordinator: LyngdorfCoordinator = entry.runtime_data

    async_add_entities([LyngdorfRemote(coordinator)])


class LyngdorfRemote(LyngdorfEntity, RemoteEntity):
    """Implementation of the Lyngdorf Remote."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._receiver.power

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self._receiver.async_power_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self._receiver.async_power_off()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to device."""
        num_repeats = kwargs[ATTR_NUM_REPEATS]

        for _ in range(num_repeats):
            for single_command in command:
                await self._receiver.async_send_command(single_command)
