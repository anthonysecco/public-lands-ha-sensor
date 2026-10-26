![icon](https://github.com/user-attachments/assets/de5ad0b3-8f84-4b37-a003-0a3bd3b0b2b2)

# Public Lands
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![GitHub release](https://img.shields.io/github/v/release/anthonysecco/public-lands-ha-sensor)](https://github.com/anthonysecco/public-lands-ha-sensor/releases)
[![Validate](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/validate.yml/badge.svg)](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/validate.yml)
[![Tests](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/tests.yml/badge.svg)](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/tests.yml)
[![Link check](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/links.yml/badge.svg)](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/links.yml)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-donate-yellow.svg)](https://www.buymeacoffee.com/anthonysecco)

A Home Assistant integration that looks up the land at your current GPS location and tells you who manages it, with a link to that office's rules.  Useful when looking for dispersed camping to quickly understand what land and jurisdiction you're on.

- **Land:** name, designation, manager and public access, from USGS PAD-US and BLM's surface management map.  Shows **Private Land** on private land.
- **Rules link:** the BLM field office, National Park, National Forest or Wildlife Refuge page.
- **Optional:** city, county and state (U.S. Census Bureau), and nearby campgrounds (Recreation.gov, with your own free API key).

United States only.  Needs an Internet connection when it refreshes.  No account or key needed for the main sensors.

This integration pairs nicely with [Geolocator](https://github.com/SmartyVan/hass-geolocator) by [SmartyVan](https://www.youtube.com/@SmartyVan), which provides geocoded address and timezone services.

⚠️ **Dispersed Camping Disclaimer** ⚠️

Use your judgement when deciding where to set up a dispersed camp.  I am not responsible for the accuracy of the data or whether you run into problems at your chosen location.  Refer to the applicable government website for rules and regulations on dispersed camping for your chosen location.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=anthonysecco&repository=public-lands-ha-sensor&category=integration)

> Not yet in the HACS default store, so it's added as a custom repository.

1. Click the button above and install **Public Lands** in HACS.
2. Restart Home Assistant.
3. Go to **Settings > Devices & Services**, click **Add Integration**, and search for **Public Lands**.

**Manual installation:** download the [latest release](https://github.com/anthonysecco/public-lands-ha-sensor/releases), copy `custom_components/public_lands` into your Home Assistant `config/custom_components/` folder, and restart.

Upgrading from v0.2.x is safe; see the [changelog](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/CHANGELOG.md#upgrading-from-v02x).

## Quick Start

1. Press **Refresh USPL** (`button.refresh_uspl`).  The sensors fill in for your current location.
2. Add an [automation](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/docs/automations.md) to refresh when you move or park.
3. Optional: under **Configure**, choose a GPS tracker as the location and turn on extra sensors.

## Sensors

| Sensor | Example |
|--------|---------|
| USPL Unit Name | Alabama Hills National Scenic Area |
| USPL Designation | National Scenic, Botanical or Volcanic Area |
| USPL Management Name | Bureau of Land Management, with a link to Bishop Field Office's rules page |
| USPL Management Type | Federal |
| USPL Public Access | Restricted Access |
| USPL API Status | On when the last refresh worked |
| USPL Last Successful Refresh | When the last refresh worked |
| Optional: USPL City, County, State | Unincorporated · Inyo County · California |
| Optional: USPL Nearby Campgrounds | 3 campgrounds within 25 miles |

Sensors keep their last values across restarts and when a refresh fails.

## Documentation

- [Configuration](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/docs/configuration.md): every setting, optional sensors and the Recreation.gov key
- [Sensors and actions](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/docs/sensors.md): all sensors, attributes and the `public_lands.lookup` action
- [Dashboard cards](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/docs/dashboard.md): rules link and nearby campground cards
- [Automations](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/docs/automations.md): refresh when you move or park
- [Data sources](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/docs/data-sources.md): where the data comes from, accuracy and limits
- [Changelog](https://github.com/anthonysecco/public-lands-ha-sensor/blob/main/CHANGELOG.md)

## Future Enhancements

- **Camping guidance:** a sensor summarizing whether dispersed camping is generally allowed for the land you are on.
- **Red Flag Warnings:** National Weather Service fire weather warnings for your location.

## 💖 Support

If you found this project useful, consider [buying me a coffee](https://www.buymeacoffee.com/anthonysecco). ☕

## Contributions

Thanks to Smarty Van for [Geolocator](https://github.com/SmartyVan/hass-geolocator) which served as a starting point for this integration.

Open issues, suggest improvements, or contribute pull requests directly here on GitHub.

## AI Disclosure

This project was built largely with AI coding tools (Claude). I directed the design and reviewed the changes, but most of the code and documentation was written by AI. Please review the code before relying on it, and open an issue if you find a problem.

## License

This project is licensed under the MIT License. For more details, see the LICENSE file.
