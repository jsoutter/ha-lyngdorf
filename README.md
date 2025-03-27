# Lyngdorf

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

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
- Volume slider does not convert between linear and scaled logarithmic value.

## Installation (Manual)

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new older called `lyngdorf`.
1. Download _all_ the files from the `custom_components/lyngdorf/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant.
1. In the HA UI go to "Settings" -> "Device & services" where  discovered devices will be shown.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/lyngdorf/translations/en.json
custom_components/lyngdorf/__init__.py
custom_components/lyngdorf/config_flow.py
custom_components/lyngdorf/const.py
custom_components/lyngdorf/entity.py
custom_components/lyngdorf/icons.json
custom_components/lyngdorf/manifest.json
custom_components/lyngdorf/media_player.py
custom_components/lyngdorf/select.py
custom_components/lyngdorf/sensor.py
custom_components/lyngdorf/strings.json
```

## Installation (HACS)

Please follow directions [here](https://hacs.xyz/docs/faq/custom_repositories/), and use https://github.com/jsoutter/ha-lyngdorf as the repository URL.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md).

## Credits

Uses @fishloa Automation Library for Lyngdorf receivers https://github.com/fishloa/lyngdorf.

Code template based upon [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template.

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/jsoutter/ha-lyngdorf.svg?style=for-the-badge
[commits]: https://github.com/jsoutter/ha-lyngdorf/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/jsoutter/ha-lyngdorf.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40jsoutter-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jsoutter/ha-lyngdorf.svg?style=for-the-badge
[releases]: https://github.com/jsoutter/ha-lyngdorf/releases
[user_profile]: https://github.com/jsoutter
