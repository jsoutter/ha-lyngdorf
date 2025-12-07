#!/usr/bin/env python3
"""
Module implements constants for Lyngdorf processors.

:license: MIT, see LICENSE for more details.
"""

import re
from collections.abc import Callable, Mapping
from enum import Enum, auto
from types import MappingProxyType
from typing import Any, Final

import attr

from .exceptions import LyngdorfUnsupportedError

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

MIN_VOLUME_DB = -99.9
DEFAULT_MAX_VOLUME_DB = 12.0
DEFAULT_MIN_LIPSYNC = 0
DEFAULT_MAX_LIPSYNC = 500

TRIM_RANGE_BASS_TREBLE = 12.0
TRIM_RANGE_CHANNEL = 10.0


# Supported devices
class DeviceModel(str, Enum):
    MP40 = "MP-40"
    MP50 = "MP-50"
    MP60 = "MP-60"
    TDAI1120 = "TDAI-1120"
    TDAI2210 = "TDAI-2210"
    TDAI3400 = "TDAI-3400"


# Commands
class LyngdorfCommands(Enum):
    VERBOSE = auto()
    POWER_ON = auto()
    POWER_OFF = auto()
    VOLUME = auto()
    VOLUME_UP = auto()
    VOLUME_DOWN = auto()
    MUTE_ON = auto()
    MUTE_OFF = auto()
    SOURCE = auto()
    VOICING = auto()
    FOCUS_POSITION = auto()
    AUDIO_MODE = auto()
    LIPSYNC = auto()
    PLAY = auto()
    PREVIOUS = auto()
    NEXT = auto()
    TRIM_BASS = auto()
    TRIM_TREBLE = auto()
    TRIM_CENTER = auto()
    TRIM_HEIGHTS = auto()
    TRIM_LFE = auto()
    TRIM_SURROUNDS = auto()


# Queries
class LyngdorfQueries(Enum):
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
    FOCUS_POSITON_LIST = auto()
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
    TRIM_BASS = auto()
    TRIM_TREBLE = auto()
    TRIM_CENTER = auto()
    TRIM_HEIGHTS = auto()
    TRIM_LFE = auto()
    TRIM_SURROUNDS = auto()


@attr.dataclass(frozen=True)
class CommandDefinition:
    template: str
    parameter: bool = False


class DeviceCommands:
    def __init__(self, commands: dict[LyngdorfCommands, CommandDefinition]):
        self.commands = commands

    def get_command(self, cmd: LyngdorfCommands, *args: Any) -> str:
        if cmd not in self.commands:
            raise ValueError(f"Command {cmd.name} not supported by this device.")

        definition = self.commands[cmd]

        if args:
            return definition.template.format(*args)

        if definition.parameter:
            raise ValueError(f"Command {cmd.name} requires exactly one argument.")

        # Strip placeholders like "({:d})" or "({:.0f})"
        return re.sub(r"\([^)]*{[^}]*}\)", "", definition.template).strip()


@attr.dataclass(frozen=True)
class DeviceProtocol:
    commands: DeviceCommands
    queries: Mapping[LyngdorfQueries, str]
    streaming_types: Mapping[int, str | None] = MappingProxyType({})
    multichannel: bool = False
    audio_inputs: Mapping[int, str | None] = MappingProxyType({})
    video_inputs: Mapping[int, str | None] = MappingProxyType({})
    video_outputs: Mapping[int, str | None] = MappingProxyType({})


COMMON_COMMANDS: Final = DeviceCommands(
    {
        LyngdorfCommands.VERBOSE: CommandDefinition("VERB({:d})", parameter=True),
        LyngdorfCommands.VOLUME: CommandDefinition("VOL({:.0f})", parameter=True),
        LyngdorfCommands.PLAY: CommandDefinition("PLAY"),
        LyngdorfCommands.PREVIOUS: CommandDefinition("PREV"),
        LyngdorfCommands.NEXT: CommandDefinition("NEXT"),
    }
)

MP_COMMANDS: Final = DeviceCommands(
    {
        **COMMON_COMMANDS.commands,
        LyngdorfCommands.POWER_ON: CommandDefinition("POWERONMAIN"),
        LyngdorfCommands.POWER_OFF: CommandDefinition("POWEROFFMAIN"),
        LyngdorfCommands.VOLUME_UP: CommandDefinition("VOL+"),
        LyngdorfCommands.VOLUME_DOWN: CommandDefinition("VOL-"),
        LyngdorfCommands.MUTE_ON: CommandDefinition("MUTEON"),
        LyngdorfCommands.MUTE_OFF: CommandDefinition("MUTEOFF"),
        LyngdorfCommands.SOURCE: CommandDefinition("SRC({:d})", parameter=True),
        LyngdorfCommands.VOICING: CommandDefinition("RPVOI({:d})", parameter=True),
        LyngdorfCommands.FOCUS_POSITION: CommandDefinition(
            "RPFOC({:d})", parameter=True
        ),
        LyngdorfCommands.AUDIO_MODE: CommandDefinition("AUDMODE({:d})", parameter=True),
        LyngdorfCommands.LIPSYNC: CommandDefinition("LIPSYNC({:d})", parameter=True),
        LyngdorfCommands.TRIM_BASS: CommandDefinition("TRIMBASS({:d})", parameter=True),
        LyngdorfCommands.TRIM_TREBLE: CommandDefinition(
            "TRIMTREB({:d})", parameter=True
        ),
        LyngdorfCommands.TRIM_CENTER: CommandDefinition(
            "TRIMCENTER({:d})", parameter=True
        ),
        LyngdorfCommands.TRIM_HEIGHTS: CommandDefinition(
            "TRIMHEIGHT({:d})", parameter=True
        ),
        LyngdorfCommands.TRIM_LFE: CommandDefinition("TRIMLFE({:d})", parameter=True),
        LyngdorfCommands.TRIM_SURROUNDS: CommandDefinition(
            "TRIMSURRS({:d})", parameter=True
        ),
    }
)


TDAI_COMMANDS: Final = DeviceCommands(
    {
        **COMMON_COMMANDS.commands,
        LyngdorfCommands.POWER_ON: CommandDefinition("ON"),
        LyngdorfCommands.POWER_OFF: CommandDefinition("OFF"),
        LyngdorfCommands.VOLUME_UP: CommandDefinition("VOLUP"),
        LyngdorfCommands.VOLUME_DOWN: CommandDefinition("VOLDN"),
        LyngdorfCommands.MUTE_ON: CommandDefinition("MUTEON"),
        LyngdorfCommands.MUTE_OFF: CommandDefinition("MUTEOFF"),
        LyngdorfCommands.SOURCE: CommandDefinition("SRC({:d})", parameter=True),
        LyngdorfCommands.VOICING: CommandDefinition("VOI({:d})", parameter=True),
        LyngdorfCommands.FOCUS_POSITION: CommandDefinition("RP({:d})", parameter=True),
    }
)

COMMON_QUERIES: Final[Mapping[LyngdorfQueries, str]] = MappingProxyType(
    {
        LyngdorfQueries.VERBOSE: "VERB?",
        LyngdorfQueries.DEVICE: "DEVICE?",
    }
)

MP_QUERIES: Final[Mapping[LyngdorfQueries, str]] = MappingProxyType(
    {
        **COMMON_QUERIES,
        LyngdorfQueries.POWER: "POWER?",
        LyngdorfQueries.MAX_VOLUME: "MAXVOL?",
        LyngdorfQueries.VOLUME: "VOL?",
        LyngdorfQueries.MUTE: "MUTE?",
        LyngdorfQueries.SOURCE_LIST: "SRCS?",
        LyngdorfQueries.SOURCE: "SRC?",
        LyngdorfQueries.STREAM_TYPE: "STREAMTYPE?",
        LyngdorfQueries.VOICING_LIST: "RPVOIS?",
        LyngdorfQueries.VOICING: "RPVOI?",
        LyngdorfQueries.FOCUS_POSITON_LIST: "RPFOCS?",
        LyngdorfQueries.FOCUS_POSITION: "RPFOC?",
        LyngdorfQueries.AUDIO_MODE_LIST: "AUDMODEL?",
        LyngdorfQueries.AUDIO_MODE: "AUDMODE?",
        LyngdorfQueries.AUDIO_INPUT: "AUDIN?",
        LyngdorfQueries.AUDIO_TYPE: "AUDTYPE?",
        LyngdorfQueries.VIDEO_INPUT: "VIDIN?",
        LyngdorfQueries.VIDEO_TYPE: "VIDTYPE?",
        LyngdorfQueries.VIDEO_OUTPUT: "HDMIMAINOUT?",
        LyngdorfQueries.LIPSYNC_RANGE: "LIPSYNCRANGE?",
        LyngdorfQueries.LIPSYNC: "LIPSYNC?",
        LyngdorfQueries.DTS_DIALOG_AVAILABLE: "DTSDIALOGAVAILABLE?",
        LyngdorfQueries.DTS_DIALOG: "DTSDIALOG?",
        LyngdorfQueries.LOUDNESS: "LOUDNESS?",
        LyngdorfQueries.TRIM_BASS: "TRIMBASS?",
        LyngdorfQueries.TRIM_TREBLE: "TRIMTREB?",
        LyngdorfQueries.TRIM_CENTER: "TRIMCENTER?",
        LyngdorfQueries.TRIM_HEIGHTS: "TRIMHEIGHT?",
        LyngdorfQueries.TRIM_LFE: "TRIMLFE?",
        LyngdorfQueries.TRIM_SURROUNDS: "TRIMSURRS?",
    }
)

TDAI_QUERIES: Final[Mapping[LyngdorfQueries, str]] = MappingProxyType(
    {
        **COMMON_QUERIES,
        LyngdorfQueries.POWER: "PWR?",
        LyngdorfQueries.VOLUME: "VOL?",
        LyngdorfQueries.MUTE: "MUTE?",
        LyngdorfQueries.SOURCE_LIST: "SRCLIST?",
        LyngdorfQueries.SOURCE: "SRCNAME?",
        LyngdorfQueries.STREAM_TYPE: "STREAMTYPE?",
        LyngdorfQueries.AUDIO_TYPE: "AUDIOSTATUS?",
        LyngdorfQueries.VOICING_LIST: "VOILIST?",
        LyngdorfQueries.VOICING: "VOINAME?",
        LyngdorfQueries.FOCUS_POSITON_LIST: "RPLIST?",
        LyngdorfQueries.FOCUS_POSITION: "RPNAME?",
    }
)


MP_STREAM_TYPES: Final = MappingProxyType(
    {
        0: None,
        1: "vTuner",
        2: "Spotify",
        3: "AirPlay",
        4: "UPnP",
        5: "Storage",
        6: "Roon ready",
        7: "Unknown",
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
        9: "airable",
        10: "Qobuz",
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

MP_MODELS: Final = [DeviceModel.MP40, DeviceModel.MP50, DeviceModel.MP60]
TDAI_MODELS: Final = (DeviceModel.TDAI1120, DeviceModel.TDAI2210, DeviceModel.TDAI3400)

TDAI_STREAM_TYPES: Final = {
    DeviceModel.TDAI1120: TDAI1120_STREAM_TYPES,
    DeviceModel.TDAI2210: TDAI2210_STREAM_TYPES,
    DeviceModel.TDAI3400: TDAI3400_STREAM_TYPES,
}

DEFAULT_PROTOCOL = DeviceProtocol(COMMON_COMMANDS, COMMON_QUERIES)

DEVICE_PROTOCOLS: dict[DeviceModel, DeviceProtocol] = {
    **{
        model: DeviceProtocol(
            MP_COMMANDS,
            MP_QUERIES,
            MP_STREAM_TYPES,
            True,
            MP_AUDIO_INPUTS,
            MP_VIDEO_INPUTS,
            MP_VIDEO_OUTPUTS,
        )
        for model in MP_MODELS
    },
    **{
        model: DeviceProtocol(
            TDAI_COMMANDS,
            TDAI_QUERIES,
            TDAI_STREAM_TYPES[model],
        )
        for model in TDAI_MODELS
    },
}


def get_device_protocol(model: DeviceModel) -> DeviceProtocol:
    try:
        return DEVICE_PROTOCOLS[model]
    except KeyError:
        raise LyngdorfUnsupportedError(
            f"Unsupported device model: {model.value}"
        ) from None
