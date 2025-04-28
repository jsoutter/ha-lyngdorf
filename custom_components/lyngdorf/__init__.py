"""The Lyngdorf integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_IP_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from lyngdorf.device import LyngdorfModel, Receiver, create_receiver

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.SELECT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lyngdorf from a config entry."""
    receiver: Receiver = create_receiver(
        entry.data[CONF_IP_ADDRESS], LyngdorfModel.MP_60
    )

    try:
        await receiver.async_connect()
    except (TimeoutError, ConnectionRefusedError) as err:
        msg = f"Unable to connect to {entry.data[CONF_IP_ADDRESS]}: {err}"
        raise ConfigEntryNotReady(msg) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = receiver

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    async def disconnect(event: Event) -> None:  # noqa: ARG001
        await receiver.async_disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, disconnect)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await hass.data[DOMAIN][entry.entry_id].async_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
