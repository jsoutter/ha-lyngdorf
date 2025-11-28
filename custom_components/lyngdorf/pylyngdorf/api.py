#!/usr/bin/env python3
"""
Module implements API for Lyngdorf processors.

:license: MIT, see LICENSE for more details.
"""

import asyncio
import contextlib
import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any, Final

import attr

from .const import (
    COMMAND_PREFIX,
    DEFAULT_PORT,
    ECHO_PREFIX,
    MONITOR_INTERVAL,
    RECONNECT_BACKOFF,
    RECONNECT_MAX_WAIT,
    RECONNECT_SCALE,
    DeviceProtocol,
    LyngdorfCommands,
    LyngdorfQueries,
)
from .exceptions import (
    LyngdorfNetworkError,
    LyngdorfProcessingError,
    LyngdorfTimoutError,
)

_LOGGER = logging.getLogger(__name__)

_MESSAGE_PATTERN: Final = re.compile(
    f"^[{COMMAND_PREFIX}{ECHO_PREFIX}]"  # Must start with '!' or '#'
    r"(?P<cmd>\w+)"  # Command name
    r"\??"  # Optional '?'
    r"(?:\((?P<params>[^\)]*)\))?"  # Optional (param1,param2)
    r"(?:\"(?P<string>[^\"]*)\")?"  # Optional "string"
)

_SPLIT_PARAMS: Final = re.compile(r'"(.*?)"|([^,]+)')


@attr.define(auto_attribs=True, frozen=True)
class LyngdorfParsedMessage:
    """Represents a parsed message from the Lyngdorf protocol."""

    event: str
    params: list[str]


class LyngdorfProtocol(asyncio.Protocol):
    """Protocol for the Lyngdorf interface."""

    def __init__(
        self,
        on_message: Callable[[str], None],
        on_connection_lost: Callable[[], None],
    ) -> None:
        """Initialise the protocol."""
        self._buffer = b""
        self.transport: asyncio.Transport | None = None
        self._on_message = on_message
        self._on_connection_lost = on_connection_lost

    @property
    def connected(self) -> bool:
        """Return True if transport is connected."""
        if self.transport is None:
            return False
        return not self.transport.is_closing()

    def write(self, data: str) -> None:
        """Write data to the transport."""
        if self.transport is None or self.transport.is_closing():
            return
        self.transport.write(data.encode("utf-8"))

    def close(self) -> None:
        """Close the connection."""
        if self.transport is not None:
            self.transport.close()

    def data_received(self, data: bytes) -> None:
        """Handle data received."""
        self._buffer += data
        while b"\r" in self._buffer:
            line, _, self._buffer = self._buffer.partition(b"\r")
            with contextlib.suppress(UnicodeDecodeError):
                self._on_message(line.decode("utf-8"))

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Handle connection made."""
        self.transport = transport  # type: ignore

    def connection_lost(self, exc: Exception | None) -> None:
        """Handle connection lost."""
        self._on_connection_lost()
        self.transport = None


@attr.define(unsafe_hash=False)
class LyngdorfApi:
    """Handle responses from the Lyngdorf interface."""

    device_protocol: DeviceProtocol = attr.field()
    host: str = attr.field(converter=str, default="localhost")
    port: int = attr.field(converter=int, default=DEFAULT_PORT)
    timeout: float = attr.field(converter=float, default=2.0)
    _connection_enabled: bool = attr.field(default=False)
    _last_message_time: float = attr.field(default=-1.0)
    _connect_lock: asyncio.Lock = attr.field(default=attr.Factory(asyncio.Lock))
    _reconnect_task: asyncio.Task[Any] | None = attr.field(default=None)
    _monitor_task: asyncio.Task[Any] | None = attr.field(default=None)
    _protocol: LyngdorfProtocol | None = attr.field(default=None)
    _callback_tasks: set[asyncio.Task[Any]] = attr.field(factory=lambda: set())
    _send_lock: asyncio.Lock = attr.field(default=attr.Factory(asyncio.Lock))
    _send_confirmation_timeout: float = attr.field(converter=float, default=2.0)
    _pending_confirmations: dict[str, asyncio.Future[None]] = attr.field(
        factory=dict[str, asyncio.Future[None]]
    )
    _send_tasks: set[asyncio.Task[Any]] = attr.field(factory=lambda: set())
    _callbacks: dict[str, list[Callable[[str, list[str]], Awaitable[None]]]] = (
        attr.field(factory=dict[str, list[Callable[[str, list[str]], Awaitable[None]]]])
    )
    _raw_callbacks: list[Callable[[str], Awaitable[None]]] = attr.field(
        factory=list[Callable[[str], Awaitable[None]]]
    )

    def __attrs_post_init__(self) -> None:
        """Initialise special attributes."""
        self._register_raw_callback(self._async_send_confirmation_callback)

    async def async_connect(self) -> None:
        """Connect to the processor asynchronously."""
        _LOGGER.debug("%s: connecting", self.host)
        async with self._connect_lock:
            if self.connected:
                return
            await self._async_establish_connection()

    async def _async_establish_connection(self) -> None:
        """Establish a connection to the processor."""
        loop = asyncio.get_running_loop()
        _LOGGER.debug("%s: establishing connection", self.host)
        try:
            transport_protocol = await asyncio.wait_for(
                loop.create_connection(
                    lambda: LyngdorfProtocol(
                        on_connection_lost=self._handle_disconnected,
                        on_message=self._process_message,
                    ),
                    self.host,
                    self.port,
                ),
                timeout=self.timeout,
            )
        except TimeoutError as err:
            _LOGGER.debug("%s: Timeout exception on connect", self.host)
            raise LyngdorfTimoutError(f"TimeoutException: {err}", "connect") from err
        except ConnectionRefusedError as err:
            _LOGGER.debug("%s: Connection refused on connect: %s", self.host, err)
            raise LyngdorfNetworkError(
                f"ConnectionRefusedError: {err}", "connect"
            ) from err
        except OSError as err:
            _LOGGER.debug("%s: Connection failed on reconnect: %s", self.host, err)
            raise LyngdorfNetworkError(f"OSError: {err}", "connect") from err
        self._protocol = transport_protocol[1]
        _LOGGER.debug("%s: connection established", self.host)
        self._connection_enabled = True
        self._last_message_time = time.monotonic()
        self._monitor_task = asyncio.create_task(
            self._schedule_monitor(MONITOR_INTERVAL)
        )

        cmd = self.device_protocol.commands.get_command(LyngdorfCommands.VERBOSE, 2)
        await self._async_send_command(cmd, skip_confirmation=True)
        await self.async_send_commands(*self.device_protocol.queries.values())

    def _stop_monitor(self) -> None:
        """Stop the monitor task."""
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            self._monitor_task = None

    async def _schedule_monitor(self, delay: float) -> None:
        """Monitor task wrapper."""
        while self._connection_enabled:
            try:
                await asyncio.sleep(delay)
                await self._monitor()
            except Exception as err:
                _LOGGER.warning("%s: Monitor loop error: %s", self.host, err)

    async def _monitor(self) -> None:
        """Monitor the connection."""
        time_since_response = time.monotonic() - self._last_message_time
        if time_since_response > MONITOR_INTERVAL * 2:
            _LOGGER.info(
                "%s: Keep alive failed, disconnecting and reconnecting", self.host
            )
            self._handle_disconnected()
            return

        if time_since_response >= MONITOR_INTERVAL and self._protocol:
            # Keep the connection alive
            _LOGGER.debug("%s: Sending keep alive", self.host)
            await self._async_send_command(
                self.device_protocol.queries[LyngdorfQueries.VERBOSE]
            )

    def _handle_disconnected(self) -> None:
        """Handle disconnected."""
        _LOGGER.debug("%s: handle disconnected", self.host)
        if self._protocol is not None:
            self._protocol.close()
            self._protocol = None
        self._stop_monitor()
        if not self._connection_enabled:
            return
        if self._reconnect_task is None:
            self._reconnect_task = asyncio.create_task(self._async_reconnect())

    async def async_disconnect(self) -> None:
        """Close the connection to the processor asynchronously."""
        async with self._connect_lock:
            _LOGGER.debug("%s: disconnecting", self.host)
            self._connection_enabled = False
            self._stop_monitor()
            reconnect_task = self._reconnect_task
            if self._reconnect_task is not None:
                self._reconnect_task.cancel()
                self._reconnect_task = None
            if self._protocol is not None:
                self._protocol.close()
                self._protocol = None

            if reconnect_task is not None:
                with contextlib.suppress(asyncio.CancelledError):
                    await reconnect_task
            _LOGGER.debug("%s: Disconnected", self.host)

    async def _async_reconnect(self) -> None:
        """Reconnect to the processor asynchronously."""
        backoff = RECONNECT_BACKOFF

        while self._connection_enabled and not self.healthy:
            async with self._connect_lock:
                _LOGGER.debug("%s: Reconnecting", self.host)
                try:
                    await self._async_establish_connection()

                except LyngdorfTimoutError:
                    _LOGGER.debug("%s: Timeout exception on reconnect", self.host)
                except LyngdorfNetworkError as err:
                    _LOGGER.debug("%s: %s", self.host, err)
                except LyngdorfProcessingError as err:
                    _LOGGER.debug(
                        "%s: Failed updating state on reconnect: %s",
                        self.host,
                        err,
                    )
                except Exception as err:
                    _LOGGER.error(
                        "%s: Unexpected exception on reconnect",
                        self.host,
                        exc_info=err,
                    )
                else:
                    _LOGGER.info("%s: Reconnected", self.host)
                    break

            await asyncio.sleep(backoff)
            backoff = min(RECONNECT_MAX_WAIT, backoff * RECONNECT_SCALE)

        self._reconnect_task = None

    def register_callback(
        self, event: str, callback: Callable[[str, list[str]], Awaitable[None]]
    ) -> None:
        """Register a callback handler for an event type."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        elif callback in self._callbacks[event]:
            return
        self._callbacks[event].append(callback)

    def unregister_callback(
        self, event: str, callback: Callable[[str, list[str]], Awaitable[None]]
    ) -> None:
        """Unregister a callback handler for an event type."""
        if event not in self._callbacks:
            return
        self._callbacks[event].remove(callback)

    def _register_raw_callback(
        self, callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """Register a callback handler for raw messages."""
        if callback in self._raw_callbacks:
            return
        self._raw_callbacks.append(callback)

    def _unregister_raw_callback(
        self, callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """Unregister a callback handler for raw messages."""
        self._raw_callbacks.remove(callback)

    def _parse_message(self, message: str) -> LyngdorfParsedMessage | None:
        """Parse a message string into an event name and list of parameters."""
        match = _MESSAGE_PATTERN.match(message)
        if not match:
            return None

        command = match.group("cmd")
        params_raw = match.group("params")
        trailing = match.group("string")

        def _split_params(s: str) -> list[str]:
            return [m[0] or m[1].strip() for m in re.findall(_SPLIT_PARAMS, s)]

        params = _split_params(params_raw) if params_raw else []
        if trailing is not None:
            params.append(trailing)

        return LyngdorfParsedMessage(command, params)

    def _process_message(self, message: str) -> None:
        """Process event."""
        _LOGGER.debug("Incoming message: %s", message)
        self._last_message_time = time.monotonic()
        parsed_message = self._parse_message(message)
        if parsed_message is None:
            return

        task = asyncio.create_task(self._async_run_callbacks(message, parsed_message))
        self._callback_tasks.add(task)
        task.add_done_callback(self._callback_tasks.discard)

    async def _async_run_callbacks(
        self, message: str, parsed_message: LyngdorfParsedMessage
    ) -> None:
        """Handle triggering the registered callbacks."""
        for callback in self._raw_callbacks:
            try:
                await callback(message)
            except Exception as err:
                # We don't want a single bad callback to trip up the
                # whole system and prevent further execution
                _LOGGER.exception(
                    "%s: Raw callback caused an unhandled exception: %s",
                    self.host,
                    err,
                )

        if message.startswith(COMMAND_PREFIX):
            if parsed_message.event in self._callbacks:
                for callback in self._callbacks[parsed_message.event]:
                    try:
                        await callback(parsed_message.event, parsed_message.params)
                    except Exception as err:
                        # We don't want a single bad callback to trip up the
                        # whole system and prevent further execution
                        _LOGGER.exception(
                            "%s: Event callback caused an unhandled exception: %s",
                            self.host,
                            err,
                        )

    def _write_command(self, command: str) -> None:
        """Send a command to the processor."""
        if self._protocol:
            self._protocol.write(f"{COMMAND_PREFIX}{command}\r")
            _LOGGER.debug("%s send: %s%s", self.host, COMMAND_PREFIX, command)

    async def _async_send_command(
        self, command: str, skip_confirmation: bool = False
    ) -> None:
        """Send a command and wait for confirmation unless skipped."""
        async with self._send_lock:
            if not self.connected or not self.healthy:
                raise LyngdorfProcessingError(
                    f"Error sending command {command}. Connected: {self.connected}, Connection healthy: {self.healthy}"
                )

            future: asyncio.Future[None] | None = None
            if not skip_confirmation:
                future = asyncio.get_running_loop().create_future()
                self._pending_confirmations[command] = future

            self._write_command(command)

            if future:
                try:
                    await asyncio.wait_for(
                        future,
                        timeout=self._send_confirmation_timeout,
                    )
                except TimeoutError:
                    _LOGGER.warning(
                        "Timeout waiting for confirmation of command: %s", command
                    )
                finally:
                    self._pending_confirmations.pop(command, None)

    async def _async_send_confirmation_callback(self, message: str) -> None:
        """Confirm that the command has been executed."""
        if len(message) < 5 or not message.startswith(ECHO_PREFIX):
            return

        command = message[1:]
        future = self._pending_confirmations.pop(command, None)
        if future and not future.done():
            future.set_result(None)
            _LOGGER.debug("Command %s confirmed", command)

    async def async_send_commands(
        self, *commands: str, skip_confirmation: bool = False
    ) -> None:
        """Send commands to the processor."""
        for command in commands:
            await self._async_send_command(command, skip_confirmation=skip_confirmation)

    def send_commands(self, *commands: str, skip_confirmation: bool = False) -> None:
        """Send commands to the processor."""
        task = asyncio.create_task(
            self.async_send_commands(*commands, skip_confirmation=skip_confirmation)
        )
        self._send_tasks.add(task)
        task.add_done_callback(self._send_tasks.discard)

    ##############
    # Properties #
    ##############
    @property
    def connected(self) -> bool:
        """Return True if connection is enabled."""
        return self._connection_enabled

    @property
    def healthy(self) -> bool:
        """Return True if connection is healthy."""
        return self._protocol is not None and self._protocol.connected
