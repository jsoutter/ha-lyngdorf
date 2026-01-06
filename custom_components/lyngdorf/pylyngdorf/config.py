#!/usr/bin/env python3
"""
Module implements configuration for Lyngdorf devices.

:license: MIT, see LICENSE for more details.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Final

import attr

from .const import (
    MP_AUDIO_INPUTS,
    MP_STREAM_TYPES,
    MP_VIDEO_INPUTS,
    MP_VIDEO_OUTPUTS,
    TDAI1120_STREAM_TYPES,
    TDAI2210_STREAM_TYPES,
    TDAI3400_STREAM_TYPES,
    DeviceModel,
    LyngdorfCommand,
    LyngdorfQuery,
)
from .exceptions import LyngdorfUnsupportedError


@attr.dataclass(frozen=True)
class CommandDefinition:
    template: str
    parameter: bool = False

    def format(self, arg: Any | None = None) -> str:
        if self.parameter and arg is None:
            raise ValueError(f"{self.template} requires an argument.")
        if not self.parameter and arg is not None:
            raise ValueError(f"{self.template} does not accept an argument.")

        if arg is not None:
            return self.template.format(arg)

        return self.template


class DeviceCommands:
    def __init__(self, commands: Mapping[LyngdorfCommand, CommandDefinition]):
        self.commands = commands

    def get_command(self, cmd: LyngdorfCommand) -> CommandDefinition:
        """Return the CommandDefinition for the given enum."""
        if cmd not in self.commands:
            raise ValueError(f"Unknown Lyngdorf command name: '{cmd.name}'")

        return self.commands[cmd]

    def get_command_by_name(self, name: str) -> CommandDefinition:
        """Return the CommandDefinition for the given enum name string."""
        name = name.upper()
        try:
            enum_key = LyngdorfCommand[name]
        except KeyError as err:
            raise KeyError(f"Unknown Lyngdorf command name: '{name}'") from err

        try:
            return self.commands[enum_key]
        except KeyError as err:
            raise KeyError(f"No command definition found for: '{name}'") from err


@attr.dataclass(frozen=True)
class DeviceProtocol:
    commands: DeviceCommands
    queries: Mapping[LyngdorfQuery, str]
    streaming_types: Mapping[int, str | None] = MappingProxyType({})
    multichannel: bool = False
    audio_inputs: Mapping[int, str | None] = MappingProxyType({})
    video_inputs: Mapping[int, str | None] = MappingProxyType({})
    video_outputs: Mapping[int, str | None] = MappingProxyType({})


COMMON_COMMANDS: Final = DeviceCommands(
    {
        LyngdorfCommand.VERBOSE: CommandDefinition("VERB({:d})", parameter=True),
        LyngdorfCommand.VOLUME: CommandDefinition("VOL({:d})", parameter=True),
        LyngdorfCommand.MUTE_ON: CommandDefinition("MUTEON"),
        LyngdorfCommand.MUTE_OFF: CommandDefinition("MUTEOFF"),
        LyngdorfCommand.SOURCE: CommandDefinition("SRC({:d})", parameter=True),
        LyngdorfCommand.PLAY: CommandDefinition("PLAY"),
        LyngdorfCommand.PREVIOUS: CommandDefinition("PREV"),
        LyngdorfCommand.NEXT: CommandDefinition("NEXT"),
    }
)

MP_COMMANDS: Final = DeviceCommands(
    {
        **COMMON_COMMANDS.commands,
        LyngdorfCommand.POWER_ON: CommandDefinition("POWERONMAIN"),
        LyngdorfCommand.POWER_OFF: CommandDefinition("POWEROFFMAIN"),
        LyngdorfCommand.VOLUME_UP: CommandDefinition("VOL+"),
        LyngdorfCommand.VOLUME_DOWN: CommandDefinition("VOL-"),
        LyngdorfCommand.SOURCE_BUTTON: CommandDefinition("SRCBTN"),
        LyngdorfCommand.SOURCE_NEXT: CommandDefinition("SRC+"),
        LyngdorfCommand.SOURCE_PREV: CommandDefinition("SRC-"),
        LyngdorfCommand.VOICING: CommandDefinition("RPVOI({:d})", parameter=True),
        LyngdorfCommand.VOICING_NEXT: CommandDefinition("RPVOI+"),
        LyngdorfCommand.VOICING_PREV: CommandDefinition("RPVOI-"),
        LyngdorfCommand.FOCUS_POSITION: CommandDefinition(
            "RPFOC({:d})", parameter=True
        ),
        LyngdorfCommand.FOCUS_POSITION_NEXT: CommandDefinition("RPFOC+"),
        LyngdorfCommand.FOCUS_POSITION_PREV: CommandDefinition("RPFOC-"),
        LyngdorfCommand.AUDIO_MODE_BUTTON: CommandDefinition("AUDIO"),
        LyngdorfCommand.AUDIO_MODE: CommandDefinition("AUDMODE({:d})", parameter=True),
        LyngdorfCommand.AUDIO_MODE_NEXT: CommandDefinition("AUDMODE+"),
        LyngdorfCommand.AUDIO_MODE_PREV: CommandDefinition("AUDMODE-"),
        LyngdorfCommand.LIPSYNC: CommandDefinition("LIPSYNC({:d})", parameter=True),
        LyngdorfCommand.LIPSYNC_UP: CommandDefinition("LIPSYNC+"),
        LyngdorfCommand.LIPSYNC_DOWN: CommandDefinition("LIPSYNC-"),
        LyngdorfCommand.DTS_DIALOG_UP: CommandDefinition("DTSDIALOGUP"),
        LyngdorfCommand.DTS_DIALOG_DOWN: CommandDefinition("DTSDIALOGDN"),
        LyngdorfCommand.BASS_TRIM: CommandDefinition("TRIMBASS({:d})", parameter=True),
        LyngdorfCommand.BASS_TRIM_UP: CommandDefinition("TRIMBASS+"),
        LyngdorfCommand.BASS_TRIM_DOWN: CommandDefinition("TRIMBASS-"),
        LyngdorfCommand.TREBLE_TRIM: CommandDefinition(
            "TRIMTREB({:d})", parameter=True
        ),
        LyngdorfCommand.TREBLE_TRIM_UP: CommandDefinition("TRIMTREB+"),
        LyngdorfCommand.TREBLE_TRIM_DOWN: CommandDefinition("TRIMTREB-"),
        LyngdorfCommand.CENTER_TRIM: CommandDefinition(
            "TRIMCENTER({:d})", parameter=True
        ),
        LyngdorfCommand.CENTER_TRIM_UP: CommandDefinition("TRIMCENTER+"),
        LyngdorfCommand.CENTER_TRIM_DOWN: CommandDefinition("TRIMCENTER-"),
        LyngdorfCommand.HEIGHTS_TRIM: CommandDefinition(
            "TRIMHEIGHT({:d})", parameter=True
        ),
        LyngdorfCommand.HEIGHTS_TRIM_UP: CommandDefinition("TRIMHEIGHT+"),
        LyngdorfCommand.HEIGHTS_TRIM_DOWN: CommandDefinition("TRIMHEIGHT-"),
        LyngdorfCommand.LFE_TRIM: CommandDefinition("TRIMLFE({:d})", parameter=True),
        LyngdorfCommand.LFE_TRIM_UP: CommandDefinition("TRIMLFE+"),
        LyngdorfCommand.LFE_TRIM_DOWN: CommandDefinition("TRIMLFE-"),
        LyngdorfCommand.SURROUNDS_TRIM: CommandDefinition(
            "TRIMSURRS({:d})", parameter=True
        ),
        LyngdorfCommand.SURROUNDS_TRIM_UP: CommandDefinition("TRIMSURRS+"),
        LyngdorfCommand.SURROUNDS_TRIM_DOWN: CommandDefinition("TRIMSURRS-"),
        # Navigation
        LyngdorfCommand.CURSOR_UP: CommandDefinition("DIRU"),
        LyngdorfCommand.CURSOR_DOWN: CommandDefinition("DIRD"),
        LyngdorfCommand.CURSOR_LEFT: CommandDefinition("DIRL"),
        LyngdorfCommand.CURSOR_RIGHT: CommandDefinition("DIRR"),
        LyngdorfCommand.CURSOR_ENTER: CommandDefinition("ENTER"),
        LyngdorfCommand.DIGIT_0: CommandDefinition("NUM(0)"),
        LyngdorfCommand.DIGIT_1: CommandDefinition("NUM(1)"),
        LyngdorfCommand.DIGIT_2: CommandDefinition("NUM(2)"),
        LyngdorfCommand.DIGIT_3: CommandDefinition("NUM(3)"),
        LyngdorfCommand.DIGIT_4: CommandDefinition("NUM(4)"),
        LyngdorfCommand.DIGIT_5: CommandDefinition("NUM(5)"),
        LyngdorfCommand.DIGIT_6: CommandDefinition("NUM(6)"),
        LyngdorfCommand.DIGIT_7: CommandDefinition("NUM(7)"),
        LyngdorfCommand.DIGIT_8: CommandDefinition("NUM(8)"),
        LyngdorfCommand.DIGIT_9: CommandDefinition("NUM(9)"),
        LyngdorfCommand.MENU: CommandDefinition("MENU"),
        LyngdorfCommand.INFO: CommandDefinition("INFO"),
        LyngdorfCommand.SETTINGS: CommandDefinition("SETUP"),
        LyngdorfCommand.BACK: CommandDefinition("BACK"),
    }
)


TDAI_COMMANDS: Final = DeviceCommands(
    {
        **COMMON_COMMANDS.commands,
        LyngdorfCommand.POWER_ON: CommandDefinition("ON"),
        LyngdorfCommand.POWER_OFF: CommandDefinition("OFF"),
        LyngdorfCommand.VOLUME_UP: CommandDefinition("VOLUP"),
        LyngdorfCommand.VOLUME_DOWN: CommandDefinition("VOLDN"),
        LyngdorfCommand.SOURCE_NEXT: CommandDefinition("SRCUP"),
        LyngdorfCommand.SOURCE_PREV: CommandDefinition("SRCDN"),
        LyngdorfCommand.VOICING: CommandDefinition("VOI({:d})", parameter=True),
        LyngdorfCommand.VOICING_NEXT: CommandDefinition("VOIUP"),
        LyngdorfCommand.VOICING_PREV: CommandDefinition("VOIDN"),
        LyngdorfCommand.FOCUS_POSITION: CommandDefinition("RP({:d})", parameter=True),
        LyngdorfCommand.FOCUS_POSITION_NEXT: CommandDefinition("RPUP"),
        LyngdorfCommand.FOCUS_POSITION_PREV: CommandDefinition("RPDN"),
    }
)

COMMON_QUERIES: Final[Mapping[LyngdorfQuery, str]] = MappingProxyType(
    {
        LyngdorfQuery.VERBOSE: "VERB?",
        LyngdorfQuery.DEVICE: "DEVICE?",
    }
)

MP_QUERIES: Final[Mapping[LyngdorfQuery, str]] = MappingProxyType(
    {
        **COMMON_QUERIES,
        LyngdorfQuery.POWER: "POWER?",
        LyngdorfQuery.MAX_VOLUME: "MAXVOL?",
        LyngdorfQuery.VOLUME: "VOL?",
        LyngdorfQuery.MUTE: "MUTE?",
        LyngdorfQuery.SOURCE_LIST: "SRCS?",
        LyngdorfQuery.SOURCE: "SRC?",
        LyngdorfQuery.STREAM_TYPE: "STREAMTYPE?",
        LyngdorfQuery.VOICING_LIST: "RPVOIS?",
        LyngdorfQuery.VOICING: "RPVOI?",
        LyngdorfQuery.FOCUS_POSITION_LIST: "RPFOCS?",
        LyngdorfQuery.FOCUS_POSITION: "RPFOC?",
        LyngdorfQuery.AUDIO_MODE_LIST: "AUDMODEL?",
        LyngdorfQuery.AUDIO_MODE: "AUDMODE?",
        LyngdorfQuery.AUDIO_INPUT: "AUDIN?",
        LyngdorfQuery.AUDIO_TYPE: "AUDTYPE?",
        LyngdorfQuery.VIDEO_INPUT: "VIDIN?",
        LyngdorfQuery.VIDEO_TYPE: "VIDTYPE?",
        LyngdorfQuery.VIDEO_OUTPUT: "HDMIMAINOUT?",
        LyngdorfQuery.LIPSYNC_RANGE: "LIPSYNCRANGE?",
        LyngdorfQuery.LIPSYNC: "LIPSYNC?",
        LyngdorfQuery.DTS_DIALOG_AVAILABLE: "DTSDIALOGAVAILABLE?",
        LyngdorfQuery.DTS_DIALOG: "DTSDIALOG?",
        LyngdorfQuery.LOUDNESS: "LOUDNESS?",
        LyngdorfQuery.BASS_TRIM: "TRIMBASS?",
        LyngdorfQuery.TREBLE_TRIM: "TRIMTREB?",
        LyngdorfQuery.CENTER_TRIM: "TRIMCENTER?",
        LyngdorfQuery.HEIGHTS_TRIM: "TRIMHEIGHT?",
        LyngdorfQuery.LFE_TRIM: "TRIMLFE?",
        LyngdorfQuery.SURROUNDS_TRIM: "TRIMSURRS?",
    }
)

TDAI_QUERIES: Final[Mapping[LyngdorfQuery, str]] = MappingProxyType(
    {
        **COMMON_QUERIES,
        LyngdorfQuery.POWER: "PWR?",
        LyngdorfQuery.VOLUME: "VOL?",
        LyngdorfQuery.MUTE: "MUTE?",
        LyngdorfQuery.SOURCE_LIST: "SRCLIST?",
        LyngdorfQuery.SOURCE: "SRCNAME?",
        LyngdorfQuery.STREAM_TYPE: "STREAMTYPE?",
        LyngdorfQuery.AUDIO_TYPE: "AUDIOSTATUS?",
        LyngdorfQuery.VOICING_LIST: "VOILIST?",
        LyngdorfQuery.VOICING: "VOINAME?",
        LyngdorfQuery.FOCUS_POSITION_LIST: "RPLIST?",
        LyngdorfQuery.FOCUS_POSITION: "RPNAME?",
    }
)

MP_MODELS: Final = [DeviceModel.MP40, DeviceModel.MP50, DeviceModel.MP60]
TDAI_MODELS: Final = [DeviceModel.TDAI1120, DeviceModel.TDAI2210, DeviceModel.TDAI3400]

TDAI_STREAM_TYPES: Final = {
    DeviceModel.TDAI1120: TDAI1120_STREAM_TYPES,
    DeviceModel.TDAI2210: TDAI2210_STREAM_TYPES,
    DeviceModel.TDAI3400: TDAI3400_STREAM_TYPES,
}

DEFAULT_PROTOCOL: Final = DeviceProtocol(COMMON_COMMANDS, COMMON_QUERIES)

DEVICE_PROTOCOLS: Final[Mapping[DeviceModel, DeviceProtocol]] = MappingProxyType(
    {
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
)


def get_device_protocol(model: DeviceModel) -> DeviceProtocol:
    try:
        return DEVICE_PROTOCOLS[model]
    except KeyError:
        raise LyngdorfUnsupportedError(
            f"Unsupported device model: {model.value}"
        ) from None
