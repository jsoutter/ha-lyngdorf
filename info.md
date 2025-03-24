# `ha_lyngdorf`

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Community Forum][forum-shield]][forum]

## Functionality

The integration allows you to control an Lyngdorf processor using TCP sockets from Home Assistant. This has been tested with an MP-60, it should work ith other Lyngdorf processors such as the MP-40 and MP-50.

### Supported Features

- Media player
  - Get and set volume
  - Increase or decrease volume
  - Get source list
  - Get and set source
  - Get sounds modes
  - Get and set sound mode
- Select
  - Get focus positions list
  - Get and set focus position
  - Get voicings list
  - Get and set voicing
- Sensor
  - Get audio information
  - Get audio input
  - Get streaming source
  - Get video information
  - Get video input

## Known Limitations and Issues

- Devices can only be added through Bonjour discovery.
- Volume slider is logarithmic rather than linear.

{% if not installed %}

## Installation

1. Click install.
1. In the HA UI go to "Settings" -> "Device & services" where  discovered devices will be shown.

{% endif %}

## Credits

Uses @fishloa Automation Library for Lyngdorf receivers https://github.com/fishloa/lyngdorf.

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
