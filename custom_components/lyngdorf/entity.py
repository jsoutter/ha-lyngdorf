"""Base entity for Lyngdorf integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import CONF_IP_ADDRESS, CONF_MODEL, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


from .const import DOMAIN as LYNGDORF_DOMAIN
from .const import NAME as LYNGDORF_NAME
from .pylyngdorf.const import DeviceModel, DEFAULT_PORT
from .pylyngdorf.exceptions import LyngdorfNetworkError, LyngdorfTimoutError
from .pylyngdorf.lyngdorf import Lyngdorf

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

type LyngdorfConfigEntry = ConfigEntry[LyngdorfCoordinator]


class LyngdorfCoordinator(DataUpdateCoordinator[None]):
    """Define the Lyngdorf integration coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: LyngdorfConfigEntry) -> None:
        """Set up the coordinator and set in config_entry."""
        super().__init__(hass, _LOGGER, config_entry=config_entry, name=LYNGDORF_DOMAIN)

        self.entry_id = config_entry.entry_id
        self.name = config_entry.data[CONF_NAME]
        self.host = config_entry.data[CONF_IP_ADDRESS]
        self.port = config_entry.data.get(CONF_PORT) or DEFAULT_PORT

        try:
            self.model = DeviceModel(config_entry.options.get(CONF_MODEL))
        except ValueError:
            self.model = DeviceModel.MP60

        self.receiver: Lyngdorf = Lyngdorf.create(
            self.host,
            self.port,
            device_model=self.model,
        )

    async def async_setup(self) -> None:
        """Set up the coordinator; connect to the host; and retrieve initial data."""
        # Connect to the device
        try:
            await self.receiver.async_connect()
        except (LyngdorfTimoutError, LyngdorfNetworkError) as err:
            msg = f"Unable to connect to {self.host}: {err}"
            raise ConfigEntryNotReady(msg) from err

        # Set notification callback
        self.receiver.set_notification_callback(self._notify_callback)

    async def _async_update_data(self):
        """No polling needed."""
        return self.data

    def _notify_callback(self) -> None:
        """Handle a notification."""
        self.async_update_listeners()

    async def async_shutdown(self) -> None:
        """Disconnect from the device."""
        await self.receiver.async_disconnect()
        await super().async_shutdown()


class LyngdorfEntity(CoordinatorEntity[LyngdorfCoordinator]):
    """Defines a base Lyngdorf entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._receiver = coordinator.receiver
        self._attr_unique_id = coordinator.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(LYNGDORF_DOMAIN, coordinator.entry_id)},
            name=coordinator.name,
            manufacturer=LYNGDORF_NAME,
            model=coordinator.model.value,
        )
