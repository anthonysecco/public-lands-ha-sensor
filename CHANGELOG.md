# Changelog

Full notes for each version are on the [releases page](https://github.com/anthonysecco/public-lands-ha-sensor/releases).

## Upgrading from v0.2.x

Upgrading is safe.  Entity IDs, the refresh button and sensor values keep the same names and wording, so dashboards and automations keep working.  What changes:

- Private land shows **Private Land** instead of blank sensors.
- Sensors keep their last values after a Home Assistant restart.
- Unit Name has new attributes, and Management Name links to the managing office's rules page.
- Optional sensors are off, so no new entities appear until you turn them on.

## v0.3.4-beta

- New **USPL State** sensor, part of the city, county and state option.
- Nearby Campgrounds adds dispersed-camping sites, hides campgrounds the Forest Service reports closed, and adds booking type, phone and directions links.
- Campground search radius is 10 to 25 miles.
- Beta testers: `state` moved from the City and County attributes to `sensor.uspl_state`.

## v0.3.3-beta

- Rules link moved to attributes on **USPL Management Name** (`rules_office`, `rules_url`, `general_rules_url`), always on.  The separate USPL Rules Link sensor is removed automatically.

## v0.3.2-beta

- USPL Rules Link shows the office name, with the link as an attribute.

## v0.3.1-beta

- Optional sensors: city and county, rules link, and nearby campgrounds from Recreation.gov.
- Weekly link check.

## v0.3.0-beta

- Rebuilt on Home Assistant's data coordinator.  Keeps values across restarts and failed refreshes; errors are no longer reported as success.
- **Private Land** from BLM's surface management map.
- PAD-US 4.1 Manager Name layer, with underlying land and overlapping areas.
- Location entity setting and `public_lands.lookup` action.
- Tests, validation and translations.

## v0.2.2

- Previous stable release.
