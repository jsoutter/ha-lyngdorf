"""Config flow for Lyngdorf integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, cast

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_IP_ADDRESS, CONF_MODEL, CONF_NAME, CONF_PORT

import voluptuous as vol

from .pylyngdorf.const import DEFAULT_PORT
from .pylyngdorf.exceptions import LyngdorfNetworkError, LyngdorfTimoutError
from .pylyngdorf.lyngdorf import Lyngdorf

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

_LOGGER = logging.getLogger(__name__)


class LyngdorfConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Lyngdorf config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize a new LyngdorfConfigFlow."""
        self.hostname: str
        self.host: str
        self.port: int | None
        self.name: str
        self.model: str

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        self.hostname = discovery_info.hostname
        self.host = discovery_info.host
        self.port = discovery_info.port
        self.name = discovery_info.name.split(".", 1)[0]

        await self.async_set_unique_id(self.hostname)
        self._abort_if_unique_id_configured(
            updates={
                CONF_IP_ADDRESS: self.host,
                CONF_PORT: self.port,
                CONF_NAME: self.name,
            }
        )
        _LOGGER.debug(
            "New Lyngdorf found via zeroconf: %s (%s:%d)",
            self.hostname,
            self.host,
            self.port,
        )

        errors = {}
        if errors := await self.async_test_connection():
            return self.async_abort(
                reason="discovery_connection_failed",
                description_placeholders={
                    "error": errors["base"],
                },
            )

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
                    CONF_IP_ADDRESS: self.host,
                    CONF_PORT: self.port,
                    CONF_NAME: self.name,
                },
                options={CONF_MODEL: self.model},
            )
        placeholders = {
            "name": self.name,
            "ip_address": self.host,
            "port": self.port,
        }
        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders=placeholders,
        )

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Handle user input for Lyngdorf setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.host = user_input["host"]
            self.port = user_input["port"]

            if not (errors := await self.async_test_connection()):
                # Create unique ID based on host + port
                unique_id = f"lyngdorf-{self.host}:{self.port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self.name,
                    data={
                        CONF_IP_ADDRESS: self.host,
                        CONF_PORT: self.port,
                        CONF_NAME: self.name,
                    },
                    options={CONF_MODEL: self.model},
                )

        # Schema with default port
        data_schema = vol.Schema(
            {
                vol.Required("host"): str,
                vol.Optional("port", default=DEFAULT_PORT): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_test_connection(self) -> dict[str, str]:
        """Test connection to Lyngdorf device"""
        errors: dict[str, str] = {}

        try:
            port = cast(int, self.port)
            receiver: Lyngdorf = Lyngdorf.create(self.host, port)

            await receiver.async_connect()
            await asyncio.sleep(0.1)
            await receiver.async_disconnect()

            if not (model := receiver.model):
                errors["base"] = "unsupported"
            else:
                self.name = model.value
                self.model = model.value

        except LyngdorfTimoutError:
            errors["base"] = "timeout"
        except LyngdorfNetworkError:
            errors["base"] = "cannot_connect"
        except Exception as err:
            _LOGGER.exception("Unexpected error connecting: %s", err)
            errors["base"] = "unknown"

        return errors
