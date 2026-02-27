import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Final, TypeAlias

import aiohttp

from .const import (
    RECONNECT_BACKOFF,
    RECONNECT_MAX_WAIT,
    RECONNECT_SCALE,
)

_LOG = logging.getLogger(__name__)

MediaDataType: TypeAlias = "MediaData"


class MediaState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    BUFFERING = auto()


@dataclass(slots=True)
class MediaData:
    state: MediaState = MediaState.STOPPED
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    image_url: str | None = None
    duration: int = 0
    position: int = 0

    @classmethod
    def from_events(cls, events: dict[str, Any]) -> MediaDataType:
        def get_typed_value(entry: dict[str, Any]) -> Any:
            """Retrieve the value using its 'type' key as the key name."""
            key = entry.get("type")
            return entry.get(key) if isinstance(key, str) else None

        player_data = events.get(MusicPlayer.PATH_PLAYER_DATA, {})
        playtime_data = events.get(MusicPlayer.PATH_PLAYTIME)
        track_data = player_data.get("trackRoles", {})
        meta_data = track_data.get("mediaData", {}).get("metaData", {})

        state = {
            "playing": MediaState.PLAYING,
            "paused": MediaState.PAUSED,
            "transitioning": MediaState.BUFFERING,
        }.get(player_data.get("state"), MediaState.STOPPED)

        duration = int((player_data.get("status", {}).get("duration") or 0) / 1000)
        position = int(get_typed_value(playtime_data) / 1000) if playtime_data else 0

        return cls(
            state=state,
            title=track_data.get("title"),
            artist=meta_data.get("artist"),
            album=meta_data.get("album"),
            album_artist=meta_data.get("albumArtist") or meta_data.get("artist"),
            image_url=track_data.get("icon"),
            duration=duration,
            position=position,
        )


CallbackType = Callable[[MediaData], None | Awaitable[None] | None] | None


class MusicPlayer:
    PATH_PLAYER_DATA: Final[str] = "player:player/data"
    PATH_PLAYTIME: Final[str] = "player:player/data/playTime"
    PATHS: Final[list[str]] = [PATH_PLAYER_DATA, PATH_PLAYTIME]

    def __init__(
        self,
        host: str,
        callback: CallbackType = None,
        poll_timeout: int = 30,
    ) -> None:
        self.base_url = f"http://{host}:8080"
        self.callback = callback
        self.poll_timeout = poll_timeout

        self._running = False
        self._session: aiohttp.ClientSession | None = None
        self._poll_task: asyncio.Task[None] | None = None
        self._queue_id: str | None = None
        self._poll_url: str | None = None
        self._subscribe_url: str | None = None
        self._events: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def _ensure_session(self) -> None:
        if not self._session or self._session.closed:
            _LOG.debug("Creating new aiohttp session.")
            self._session = aiohttp.ClientSession()

    async def _fetch_json(self, url: str) -> Any:
        """GET request and return parsed JSON."""
        assert self._session is not None
        async with self._session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def _update_events(self, path: str | None, data: Any) -> None:
        """Update internal events dictionary."""
        if path is None:
            self._events.update(
                {j["path"]: j.get("itemValue") for j in data if "path" in j}
            )
        else:
            self._events[path] = data[0]
        _LOG.debug("Events updated: %s", self._events)

    async def _dispatch_media_data(self) -> None:
        """Generate MediaData and call the callback, with logging."""
        if not all(p in self._events for p in self.PATHS):
            media_data = MediaData(state=MediaState.STOPPED)
        else:
            media_data = MediaData.from_events(self._events)

        _LOG.debug("Dispatching MediaData: %s", media_data)

        if self.callback:
            try:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(media_data)
                else:
                    self.callback(media_data)
            except Exception:
                _LOG.exception("Callback error for MediaData")

    async def _initialize_queue(self) -> None:
        """Initialize queue, fetch initial data, and subscribe."""
        await self._ensure_session()

        init_url = (
            f"{self.base_url}/api/event/modifyQueue?queueId=&subscribe[]=&unsubscribe[]"
        )
        raw_text = await self._fetch_json(init_url)
        self._queue_id = raw_text[1:-1]  # strip {}
        _LOG.debug("Initialized queueId: %s", self._queue_id)

        self._poll_url = (
            f"{self.base_url}/api/event/pollQueue"
            f"?queueId={self._queue_id}&timeout={self.poll_timeout}"
        )
        subscribe_entries = [{"path": p, "type": "itemWithValue"} for p in self.PATHS]
        self._subscribe_url = (
            f"{self.base_url}/api/event/modifyQueue?"
            f"queueId={self._queue_id}&subscribe={json.dumps(subscribe_entries)}&unsubscribe=[]"
        )

        # Fetch initial data
        async def fetch_path(path: str) -> tuple[str, Any | None]:
            data_url = f"{self.base_url}/api/getData?path={path}&roles=value"
            try:
                return path, await self._fetch_json(data_url)
            except Exception:
                _LOG.exception("Failed to fetch initial data for %s", path)
                return path, None

        async with asyncio.TaskGroup() as tg:
            for p in self.PATHS:
                tg.create_task(fetch_path(p))

        for p in self.PATHS:
            data = await fetch_path(p)
            if data[1] is not None:
                await self._update_events(p, data[1])

        await self._dispatch_media_data()
        await self._fetch_json(self._subscribe_url)
        _LOG.debug("Subscription established for queueId=%s", self._queue_id)

    async def _poll_loop(self) -> None:
        """Continuously poll queue for events."""
        try:
            backoff = RECONNECT_BACKOFF
            while self._running:
                try:
                    if not self._queue_id or not self._poll_url:
                        await self._initialize_queue()

                    assert self._poll_url is not None
                    _LOG.debug("self._poll_url: %s", self._poll_url)

                    data = await self._fetch_json(self._poll_url)
                    await self._update_events(None, data)
                    await self._dispatch_media_data()

                except (
                    TimeoutError,
                    aiohttp.ClientConnectionError,
                    aiohttp.ClientOSError,
                ):
                    _LOG.exception("Connection error during polling")
                    await self._reconnect(backoff)
                except Exception:
                    _LOG.exception("Unexpected polling error")
                    await asyncio.sleep(backoff)

                backoff = min(RECONNECT_MAX_WAIT, backoff * RECONNECT_SCALE)

        except asyncio.CancelledError:
            _LOG.debug("Poll loop cancelled, exiting immediately.")
            raise

    async def _reset_state(self) -> None:
        """Reset internal poller state."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
        self._queue_id = None
        self._poll_url = None
        self._subscribe_url = None
        self._events.clear()

    async def _reconnect(self, backoff: float) -> None:
        """Close session and reset state before reconnecting."""
        _LOG.debug("Reconnecting after %.1f seconds.", backoff)
        await self._reset_state()
        await asyncio.sleep(backoff)

    async def start(self) -> None:
        """Start background polling safely."""
        async with self._lock:
            if self._running:
                _LOG.debug("Poller already running.")
                return

            _LOG.debug("Starting poller.")
            self._running = True
            await self._reset_state()
            self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop polling safely and cancel ongoing operations."""
        async with self._lock:
            if not self._running:
                _LOG.debug("Poller not running.")
                return

            _LOG.debug("Stopping poller.")
            self._running = False

            if self._poll_task:
                self._poll_task.cancel()
                try:
                    await self._poll_task
                except asyncio.CancelledError:
                    _LOG.debug("Poll task cancelled successfully.")
                self._poll_task = None

            if self._session:
                await self._session.close()
                self._session = None

            self._events.clear()
            await self._dispatch_media_data()

            _LOG.debug("Poller stopped.")
