#!/usr/bin/env python3
"""
Module implements constants for Lyngdorf devices.

:license: MIT, see LICENSE for more details.
"""

from collections.abc import Callable
from enum import Enum, auto
from types import MappingProxyType
from typing import Final

import attr

LYNGDORF_ATTR_SETATTR: list[Callable[..., object]] = [
    attr.setters.validate,
    attr.setters.convert,
]


# Defaults
DEFAULT_PORT = 84

MONITOR_INTERVAL = 90.0
RECONNECT_BACKOFF = 0.5
RECONNECT_SCALE = 2.0
RECONNECT_MAX_WAIT = 30.0

COMMAND_PREFIX = "!"
ECHO_PREFIX = "#"
MIN_MESSAGE_LENGTH = 3

MIN_VOLUME_DB = -99.9
DEFAULT_MAX_VOLUME_DB = 12.0
DEFAULT_MIN_LIPSYNC = 0
DEFAULT_MAX_LIPSYNC = 500

TRIM_RANGE_BASS_TREBLE = 12.0
TRIM_RANGE_CHANNEL = 10.0


class DeviceModel(str, Enum):
    """Supported device models."""

    MP40 = "MP-40"
    MP50 = "MP-50"
    MP60 = "MP-60"
    TDAI1120 = "TDAI-1120"
    TDAI2210 = "TDAI-2210"
    TDAI3400 = "TDAI-3400"


class LyngdorfCommand(Enum):
    """Lyngdorf commands."""

    VERBOSE = auto()
    POWER_ON = auto()
    POWER_OFF = auto()
    VOLUME = auto()
    VOLUME_UP = auto()
    VOLUME_DOWN = auto()
    MUTE = auto()
    MUTE_ON = auto()
    MUTE_OFF = auto()
    SOURCE_BUTTON = auto()
    SOURCE = auto()
    SOURCE_NEXT = auto()
    SOURCE_PREV = auto()
    VOICING = auto()
    VOICING_NEXT = auto()
    VOICING_PREV = auto()
    FOCUS_POSITION = auto()
    FOCUS_POSITION_NEXT = auto()
    FOCUS_POSITION_PREV = auto()
    AUDIO_MODE_BUTTON = auto()
    AUDIO_MODE = auto()
    AUDIO_MODE_NEXT = auto()
    AUDIO_MODE_PREV = auto()
    LIPSYNC = auto()
    LIPSYNC_UP = auto()
    LIPSYNC_DOWN = auto()
    DTS_DIALOG_UP = auto()
    DTS_DIALOG_DOWN = auto()
    PLAY = auto()
    NEXT = auto()
    PREVIOUS = auto()
    BASS_TRIM = auto()
    BASS_TRIM_UP = auto()
    BASS_TRIM_DOWN = auto()
    TREBLE_TRIM = auto()
    TREBLE_TRIM_UP = auto()
    TREBLE_TRIM_DOWN = auto()
    CENTER_TRIM = auto()
    CENTER_TRIM_UP = auto()
    CENTER_TRIM_DOWN = auto()
    HEIGHTS_TRIM = auto()
    HEIGHTS_TRIM_UP = auto()
    HEIGHTS_TRIM_DOWN = auto()
    LFE_TRIM = auto()
    LFE_TRIM_UP = auto()
    LFE_TRIM_DOWN = auto()
    SURROUNDS_TRIM = auto()
    SURROUNDS_TRIM_UP = auto()
    SURROUNDS_TRIM_DOWN = auto()
    # Navigation
    CURSOR_UP = auto()
    CURSOR_DOWN = auto()
    CURSOR_LEFT = auto()
    CURSOR_RIGHT = auto()
    CURSOR_ENTER = auto()
    DIGIT_0 = auto()
    DIGIT_1 = auto()
    DIGIT_2 = auto()
    DIGIT_3 = auto()
    DIGIT_4 = auto()
    DIGIT_5 = auto()
    DIGIT_6 = auto()
    DIGIT_7 = auto()
    DIGIT_8 = auto()
    DIGIT_9 = auto()
    MENU = auto()
    INFO = auto()
    SETTINGS = auto()
    BACK = auto()


class LyngdorfQuery(Enum):
    """Lyngdorf queries."""

    VERBOSE = auto()
    DEVICE = auto()
    POWER = auto()
    VOLUME = auto()
    MUTE = auto()
    SOURCE_LIST = auto()
    SOURCE = auto()
    STREAM_TYPE = auto()
    VOICING_LIST = auto()
    VOICING = auto()
    FOCUS_POSITION_LIST = auto()
    FOCUS_POSITION = auto()
    AUDIO_MODE_LIST = auto()
    AUDIO_MODE = auto()
    MAX_VOLUME = auto()
    AUDIO_INPUT = auto()
    AUDIO_TYPE = auto()
    VIDEO_INPUT = auto()
    VIDEO_TYPE = auto()
    VIDEO_OUTPUT = auto()
    LIPSYNC_RANGE = auto()
    LIPSYNC = auto()
    DTS_DIALOG_AVAILABLE = auto()
    DTS_DIALOG = auto()
    LOUDNESS = auto()
    BASS_TRIM = auto()
    TREBLE_TRIM = auto()
    CENTER_TRIM = auto()
    HEIGHTS_TRIM = auto()
    LFE_TRIM = auto()
    SURROUNDS_TRIM = auto()


MP_STREAM_TYPES: Final = MappingProxyType(
    {
        0: None,
        1: "vTuner",
        2: "Spotify",
        3: "AirPlay",
        4: "UPnP",
        5: "Storage",
        6: "Roon ready",
        7: "TIDAL",
        8: "airable",
        9: "Artist Connection",
        10: "Qobuz",
    }
)


TDAI1120_STREAM_TYPES: Final = MappingProxyType(
    {
        0: None,
        1: "vTuner",
        2: "Spotify",
        3: "Airplay",
        4: "uPnP",
        5: "USB File",
        6: "Roon Ready",
        7: "Bluetooth",
        8: "GoogleCast",
        9: "TIDAL",
        10: "airable",
        11: "Qobuz",
    }
)

TDAI2210_STREAM_TYPES = TDAI1120_STREAM_TYPES

TDAI3400_STREAM_TYPES: Final = MappingProxyType(
    {
        0: None,
        1: "vTuner",
        2: "Spotify",
        3: "Airplay",
        4: "uPnP",
        5: "USB File",
        6: "Roon Ready",
        7: "Bluetooth",
        8: "TIDAL",
        9: "airable",
        10: "Qobuz",
    }
)

MP_AUDIO_INPUTS: Final = MappingProxyType(
    {
        0: None,
        1: "HDMI",
        3: "Spdif 1 (Opt.)",
        4: "Spdif 2 (Opt.)",
        5: "Spdif 3 (Opt.)",
        6: "Spdif 4 (Opt.)",
        7: "Spdif 5 (AES)",
        8: "Spdif 6 (Coax)",
        9: "Spdif 7 (Coax)",
        10: "Spdif 8 (Coax)",
        11: "Internal Player",
        12: "USB",
        20: "16-Channel (AES module)",
        21: "16-Channel 2.0 (AES module)",
        22: "16-Channel 5.1 (AES module)",
        23: "16-Channel 7.1 (AES module)",
        24: "Audio Return Channel",
        35: "vTuner",
        36: "TIDAL",
        37: "Spotify",
        38: "AirPlay",
        39: "Roon Ready",
        40: "DLNA",
        41: "Storage",
        42: "airable",
        43: "Artist Connection",
        44: "Qobuz",
    }
)

MP_VIDEO_INPUTS: Final = MappingProxyType(
    {
        0: None,
        1: "HDMI 1",
        2: "HDMI 2",
        3: "HDMI 3",
        4: "HDMI 4",
        5: "HDMI 5",
        6: "HDMI 6",
        7: "HDMI 7",
        8: "HDMI 8",
        9: "Internal",
    }
)

MP_VIDEO_OUTPUTS: Final = MappingProxyType(
    {
        0: None,
        1: "HDMI Out 1",
        2: "HDMI Out 2",
        3: "HDBT Out",
    }
)
