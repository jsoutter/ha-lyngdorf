"""Remote entity for the Lyngdorf integration."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity

from .entity import LyngdorfCoordinator, LyngdorfEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


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

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize the remote entity."""
        super().__init__(coordinator)
        self._optimistic_is_on: bool | None = None

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        if self._optimistic_is_on is not None:
            _LOGGER.debug(
                "Returning optimistic power state: %s", self._optimistic_is_on
            )
            return self._optimistic_is_on

        return self._receiver.power

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        _LOGGER.info("Turning on device via remote")
        self._optimistic_is_on = True
        self.async_write_ha_state()

        try:
            await self._receiver.async_power_on()
        except Exception as err:
            _LOGGER.error("Failed to turn on device: %s", err, exc_info=True)
            self._optimistic_is_on = None
            self.async_write_ha_state()
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.info("Turning off device via remote")
        self._optimistic_is_on = False
        self.async_write_ha_state()

        try:
            await self._receiver.async_power_off()
        except Exception as err:
            _LOGGER.error("Failed to turn off device: %s", err, exc_info=True)
            self._optimistic_is_on = None
            self.async_write_ha_state()
            raise

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to device."""
        num_repeats = kwargs[ATTR_NUM_REPEATS]

        for _ in range(num_repeats):
            for single_command in command:
                await self._receiver.async_send_command(single_command.upper())

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._optimistic_is_on is not None:
            real_is_on = self._receiver.power
            _LOGGER.debug(
                "Coordinator update: real_is_on=%s, optimistic=%s",
                real_is_on,
                self._optimistic_is_on,
            )

            # Only clear when device confirms
            if real_is_on == self._optimistic_is_on:
                _LOGGER.debug("Clearing optimistic power state")
                self._optimistic_is_on = None

        super()._handle_coordinator_update()
