# `ha_lyngdorf`

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Community Forum][forum-shield]][forum]

## Functionality

The integration allows you to control an Lyngdorf processor using TCP sockets from Home Assistant.

### Supported Features

#### Media Player Entity

| Function | MP-40, MP-50, MP-60 | TDAI-1120, TDAI-2210, TDAI-3400 |
|-|-|-|
| Get and set volume | ✅ | ✅ |
| Increase or decrease volume | ✅ | ✅ |
| Get source list | ✅ | ✅ |
| Get and set source | ✅ | ✅ |
| Get sounds modes | ✅ | ❌ |
| Get and set sound mode | ✅ | ❌ |
| Attribute for volume in native format (dB) | ✅ | ✅ |

| Attribute Name | Description |
|----------------|-------------|
| **volume_db** | Current volume in decibels |
| **volume_min_db** | Minimum volume in decibels |
| **volume_max_db** | Maximum volume in decibels |
| **volume_native** | Current volume in decibels *(will be removed in a future release)* |

#### Select Entity

| Function | MP-40, MP-50, MP60 | TDAI-1120, TDAI-2200, TDAI-3400 |
|-|-|-|
| Get focus positions list | ✅ | ✅ |
| Get and set focus position | ✅ | ✅ |
| Get voicings list | ✅ | ✅ |
| Get and set voicing | ✅ | ✅ |

#### Sensor Entity

| Senor | MP-40, MP-50, MP60 | TDAI-1120, TDAI-2200, TDAI-3400 |
|-|-|-|
| Streaming source | ✅ | ✅ |
| Audio input | ✅ | ❌ |
| Audio information | ✅ | ✅ |
| Video input | ✅ | ❌ |
| Video information | ✅ | ❌ |
| Video output | ✅ | ❌ |

#### Remote Entity

| Command | MP-40, MP-50, MP-60 | TDAI-1120, TDAI-2210, TDAI-3400 |
|-|-|-|
| VOLUME_UP | ✅ | ✅ |
| VOLUME_DOWN | ✅ | ✅ |
| MUTE_TOGGLE | ✅ | ✅ |
| MUTE | ✅ | ✅ |
| UNMUTE | ✅ | ✅ |
| PLAY_PAUSE | ✅ | ✅ |
| NEXT | ✅ | ✅ |
| PREVIOUS | ✅ | ✅ |
| SOURCE_BUTTON | ✅ | ❌ |
| SOURCE_NEXT | ✅ | ✅ |
| SOURCE_PREV | ✅ | ✅ |
| VOICING_NEXT | ✅ | ✅ |
| VOICING_PREV | ✅ | ✅ |
| FOCUS_POSITION_NEXT | ✅ | ✅ |
| FOCUS_POSITION_PREV | ✅ | ✅ |
| CURSOR_UP | ✅ | ❌ |
| CURSOR_DOWN | ✅ | ❌ |
| CURSOR_LEFT | ✅ | ❌ |
| CURSOR_RIGHT  ✅ | ❌ |
| CURSOR_ENTER | ✅ | ❌ |
| DIGIT_0 | ✅ | ❌ |
| DIGIT_1 | ✅ | ❌ |
| DIGIT_2 | ✅ | ❌ |
| DIGIT_3 | ✅ | ❌ |
| DIGIT_4 | ✅ | ❌ |
| DIGIT_5 | ✅ | ❌ |
| DIGIT_6 | ✅ | ❌ |
| DIGIT_7 | ✅ | ❌ |
| DIGIT_8 | ✅ | ❌ |
| DIGIT_9 | ✅ | ❌ |
| MENU | ✅ | ❌ |
| INFO | ✅ | ❌ |
| SETTINGS | ✅ | ❌ |
| BACK | ✅ | ❌ |
| AUDIO_MODE_BUTTON | ✅ | ❌ |
| AUDIO_MODE_NEXT | ✅ | ❌ |
| AUDIO_MODE_PREV | ✅ | ❌ |
| LIPSYNC_UP | ✅ | ❌ |
| LIPSYNC_DOWN | ✅ | ❌ |
| DTS_DIALOG_UP | ✅ | ❌ |
| DTS_DIALOG_DOWN | ✅ | ❌ |
| BASS_TRIM_UP | ✅ | ❌ |
| BASS_TRIM_DOWN | ✅ | ❌ |
| TREBLE_TRIM_UP | ✅ | ❌ |
| TREBLE_TRIM_DOWN | ✅ | ❌ |
| CENTER_TRIM_UP | ✅ | ❌ |
| CENTER_TRIM_DOWN | ✅ | ❌ |
| HEIGHTS_TRIM_UP | ✅ | ❌ |
| HEIGHTS_TRIM_DOWN | ✅ | ❌ |
| LFE_TRIM_UP | ✅ | ❌ |
| LFE_TRIM_DOWN | ✅ | ❌ |
| SURROUNDS_TRIM_UP | ✅ | ❌ |
| SURROUNDS_TRIM_DOWN | ✅ | ❌ |

#### Services

- Set Volume (dB)

    Example for button tap action:
    ```yaml
    tap_action:
    action: perform-action
    perform_action: lyngdorf.set_volume_db
    target:
        entity_id: media_player.mp_60
    data:
        volume: -40
    ```

{% if not installed %}

## Installation

1. Click install.
1. In the HA UI go to "Settings" -> "Device & services" where  discovered devices will be shown.

{% endif %}

## Credits

Inspiration from @fishloa Automation Library for Lyngdorf receivers <https://github.com/fishloa/lyngdorf>.

Code template based upon [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template.

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[commits-shield]: https://img.shields.io/github/commit-activity/y/jsoutter/ha-lyngdorf.svg?style=for-the-badge
[commits]: https://github.com/jsoutter/ha-lyngdorf/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: https://github.com/jsoutter/ha-lyngdorf/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/jsoutter/ha-lyngdorf.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40jsoutter-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jsoutter/ha-lyngdorf.svg?style=for-the-badge
[releases]: https://github.com/jsoutter/ha-lyngdorf/releases
[user_profile]: https://github.com/jsoutter
