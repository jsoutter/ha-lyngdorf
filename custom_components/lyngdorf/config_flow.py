"""Config flow for Lyngdorf integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

_LOGGER = logging.getLogger(__name__)


class LyngdorfConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Lyngdorf config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize a new LyngdorfConfigFlow."""
        self.host: str
        self.ip_address: str
        self.name: str

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        self.host = discovery_info.hostname
        self.ip_address = discovery_info.host
        self.name = discovery_info.name.split(".", 1)[0]

        await self.async_set_unique_id(self.host)
        self._abort_if_unique_id_configured(
            updates={CONF_IP_ADDRESS: self.ip_address, CONF_NAME: self.name}
        )
        _LOGGER.debug("New Lyngdorf found via zeroconf: %s", self.host)
        self.context.update({"title_placeholders": {"name": self.name}})
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.name,
                data={
                    CONF_IP_ADDRESS: self.ip_address,
                    CONF_NAME: self.name,
                },
            )
        placeholders = {
            "name": self.name,
            "ip_address": self.ip_address,
        }
        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders=placeholders,
        )
