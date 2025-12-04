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

| | MP-40, MP-50, MP-60 | TDAI-1120, TDAI-2210, TDAI-3400 |
|-|-|-|
| Get and set volume | ✅ | ✅ |
| Increase or decrease volume | ✅ | ✅ |
| Get source list | ✅ | ✅ |
| Get and set source | ✅ | ✅ |
| Get sounds modes | ✅ | ❌ |
| Get and set sound mode | ✅ | ❌ |
| Attribute for volume in native format (dB) | ✅ | ✅ |

#### Select Entity

| | MP-40, MP-50, MP60 | TDAI-1120, TDAI-2200, TDAI-3400 |
|-|-|-|
| Get focus positions list | ✅ | ✅ |
| Get and set focus position | ✅ | ✅ |
| Get voicings list | ✅ | ✅ |
| Get and set voicing | ✅ | ✅ |

#### Sensor Entity

| | MP-40, MP-50, MP60 | TDAI-1120, TDAI-2200, TDAI-3400 |
|-|-|-|
| Get streaming source | ✅ | ✅ |
| Get audio input | ✅ | ❌ |
| Get audio information | ✅ | ✅ |
| Get video input | ✅ | ❌ |
| Get video information | ✅ | ❌ |
| Get video output | ✅ | ❌ |

## Known Limitations and Issues

- Integration does not expose a remote entity.

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
