"""Base Entity for Lyngdorf."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN as LYNGDORF_DOMAIN
from .const import NAME as LYNGDORF_NAME

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from lyngdorf.device import Receiver


class LyngdorfEntity(Entity):
    """Defines a base Lyngdorf entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, receiver: Receiver, config_entry: ConfigEntry) -> None:
        """Initialize entity."""
        self._receiver = receiver
        self._attr_unique_id = config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(LYNGDORF_DOMAIN, config_entry.entry_id)},
            name=config_entry.data[CONF_NAME],
            manufacturer=LYNGDORF_NAME,
            model=config_entry.data[CONF_NAME],
        )

    async def async_added_to_hass(self) -> None:
        """Notify of addition to haas."""
        self._receiver.register_notification_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Notify of removal from haas."""
        self._receiver.un_register_notification_callback(self.async_write_ha_state)
