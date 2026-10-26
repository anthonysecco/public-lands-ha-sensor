# Changelog

Full notes for each version are on the [releases page](https://github.com/anthonysecco/public-lands-ha-sensor/releases).

## Upgrading from v0.2.x

Upgrading is safe.  Entity IDs, the refresh button and sensor values keep the same names and wording, so dashboards and automations keep working.  What changes:

- Private land shows **Private Land** instead of blank sensors.
- Sensors keep their last values after a Home Assistant restart.
- Unit Name has new attributes, and Management Name links to the managing office's rules page.
- Optional sensors are off, so no new entities appear until you turn them on.

## v0.3.0-beta

**Land lookup**
- Switched to the USGS PAD-US 4.1 Manager Name layer.  Same sensor values as before, plus `underlying_land` and `overlapping_areas` attributes on Unit Name.
- **Private Land** instead of blank sensors, from BLM's surface management map.  Small gaps in PAD-US (such as road corridors in a park) are filled from a nearby area managed by the same agency.
- **Rules link** on USPL Management Name: `rules_office`, `rules_url` (BLM field office, National Park, National Forest or Wildlife Refuge page) and `general_rules_url` (BLM camping rules).

**Optional sensors** (off by default, under Configure)
- **USPL City, County and State** from the U.S. Census Bureau.
- **USPL Nearby Campgrounds** from Recreation.gov, with your own free API key: campgrounds and dispersed-camping sites within 10 to 25 miles, the nearest ten with booking type, phone, Recreation.gov and directions links.  Campgrounds the Forest Service reports closed are hidden.

**New settings and actions**
- Choose the location entity (default `zone.home`).
- `public_lands.lookup` action to check any coordinate without changing the sensors.

**Reliability**
- Rebuilt on Home Assistant's data coordinator.  Values are kept across restarts and failed refreshes, and service errors are no longer reported as success.
- Failed lookups retry once; optional lookups never fail the main refresh.
- Fixed the Last Successful Refresh timestamp, the reload bug and the startup warning.  The integration can only be added once.

**Project**
- Tests, validation and a weekly link check on GitHub Actions.
- Translations, a "Public Lands" device, and documentation split into `docs/` pages.

## v0.2.2

- Previous stable release.
