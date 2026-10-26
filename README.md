![icon](https://github.com/user-attachments/assets/de5ad0b3-8f84-4b37-a003-0a3bd3b0b2b2)

# Public Lands
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![GitHub release](https://img.shields.io/github/v/release/anthonysecco/public-lands-ha-sensor)](https://github.com/anthonysecco/public-lands-ha-sensor/releases)
[![Validate](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/validate.yml/badge.svg)](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/validate.yml)
[![Tests](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/tests.yml/badge.svg)](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/tests.yml)
[![Link check](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/links.yml/badge.svg)](https://github.com/anthonysecco/public-lands-ha-sensor/actions/workflows/links.yml)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-donate-yellow.svg)](https://www.buymeacoffee.com/anthonysecco)

This is a HACS custom integration that looks up the land at your current GPS location in Home Assistant and tells you who manages it.

It uses two official, free sources (no API key needed):

- **USGS [PAD-US 4.1](https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-web-services)** ([Manager Name layer](https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Manager_Name_PADUS/FeatureServer/0)) covers almost any protected or public land in the United States, including federal, state, county, and regional lands.
- **BLM [Surface Management Agency](https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer/1)** map is used when PAD-US has no record. It tells you when you are on private land and fills small gaps in PAD-US, such as road corridors inside a park.

[Optional sensors](#optional-sensors) add city and county (U.S. Census Bureau), a link to the land manager's rules page, and nearby campgrounds (Recreation.gov, with your own free API key).

This can be useful when finding dispersed camping to quickly understand what land and jurisdiction you are within.

> An Internet connection is required for this integration to work.
>
> Only available for the United States.

This integration pairs nicely with [Geolocator](https://github.com/SmartyVan/hass-geolocator) by [SmartyVan](https://www.youtube.com/@SmartyVan) which provides geocoded address and timezone services.

⚠️ **Dispersed Camping Disclaimer** ⚠️

Use your judgement when deciding where to setup a dispersed camp.  I am not responsible for the accuracy of the data or whether you run into problems at your chosen location.  Refer to the applicable government website for rules and regulations on dispersed camping for your chosen location.

With that out of the way, let's get started...

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=anthonysecco&repository=public-lands-ha-sensor&category=integration)

> This integration is not yet available in the HACS default store.  Meanwhile, it will be added as a custom repository.

1. Click "Open HACS Repository" button above and install **Public Lands**
2. Restart Home Assistant
3. Navigate to Settings > Devices & Services
4. Click **Add Integration** at the bottom
5. Search for **Public Lands**

### Manual Installation

1. Download the source code of the [latest release](https://github.com/anthonysecco/public-lands-ha-sensor/releases).
2. Unzip the source code download.
3. Copy **public_lands** from the **custom_components** directory you just downloaded to your Home Assistant **custom_components** directory:
   ```
   config/custom_components/public_lands/
   ```
4. Restart Home Assistant.

### Upgrading from v0.2.x

Upgrading is safe.  Entity IDs, the refresh button, and sensor values keep the same names and wording, so your dashboards and automations keep working.  What changes:

- Private land now shows **Private Land** instead of blank sensors.
- Sensors keep their last values after a Home Assistant restart.
- The Unit Name sensor has new attributes (see [Sensors](#sensors)).
- [Optional sensors](#optional-sensors) are off, so no new entities appear until you turn them on.

## Usage

Upon restart, it will automatically create the sensors and button.  No configuration needed.  No data will be found in those sensors until it is triggered.  Please see [Trigger Methods](#trigger-methods) for details on that.

### Configuration

Everything works with the defaults.  To change a setting, go to **Settings > Devices & Services > Public Lands > Configure**.  Saving reloads the integration; your last values are kept.

| Setting | Default | Description |
|---------|---------|-------------|
| Location entity | `zone.home` | Where the coordinates come from.  Pick any zone, device tracker, person, or sensor that has latitude and longitude, for example your van's GPS tracker. |
| City and county sensors | Off | Adds **USPL City** and **USPL County**.  See [Optional Sensors](#optional-sensors). |
| Rules link sensor | Off | Adds **USPL Rules Link**. |
| Nearby campgrounds sensor | Off | Adds **USPL Nearby Campgrounds**.  Needs a Recreation.gov API key. |
| Recreation.gov API key | Empty | Your own free key from [ridb.recreation.gov](https://ridb.recreation.gov/).  Only needed for nearby campgrounds. |
| Campground search radius | 25 miles | How far to look for campgrounds: 5 to 25 miles (Recreation.gov's maximum). |

### Optional Sensors

These are off by default.  Turn them on in [Configuration](#configuration).  They update when you press **Refresh USPL**, and turning one off removes its sensors.

| Option | Sensors | Source |
|--------|---------|--------|
| City and county | **USPL City** (or "Unincorporated" outside city limits) and **USPL County**, with the state as an attribute.  Many overnight-parking bans are city rules. | U.S. Census Bureau [TIGERweb](https://tigerweb.geo.census.gov/) (no key) |
| Rules link | **USPL Rules Link**: the name of the managing office, for example "Bishop Field Office".  Its `url` attribute links to that office's own web page so you can read its rules: the BLM field office, National Park, National Forest or Wildlife Refuge.  Other land links to a Recreation.gov search.  On BLM land, `general_rules_url` links to BLM's camping rules.  Unknown on private land. | Agency websites (no key) |
| Nearby campgrounds | **USPL Nearby Campgrounds**: how many Recreation.gov campgrounds are within the search radius (5 to 25 miles, default 25), with the nearest ten as attributes (name, distance, reservable, stay limit, link). | [Recreation.gov RIDB](https://ridb.recreation.gov/) (needs your own free API key) |

**Recreation.gov API key:** sign up at [ridb.recreation.gov](https://ridb.recreation.gov/), create an API key in your account, and paste it into the Configure screen.  The key is checked before it's saved and stays on your Home Assistant.  Recreation.gov's terms don't allow sharing a key, so each user needs their own.  Campground data: ridb.recreation.gov.

### Trigger Methods

#### Press the Button
This is simple.  If you want to know your USPL status immediately based on Home Assistant's current coordinate, press the button.

![image](https://github.com/user-attachments/assets/57a87b6e-a57f-4bb3-8e7f-d66b9b1e4b7e)

#### Create Automation

##### Upon GPS Update
Here's an example automation that will refresh USPL data when the zone.home is updated.  It will update at 10 minute intervals when the GPS coordinates are changing.

```yaml
alias: "USPL: Update via Button"
description: "Presses the Refresh USPL button when zone.home changes, throttled to once every 10 minutes."
triggers:
  - trigger: state
    entity_id: zone.home
conditions:
  - condition: template
    value_template: >
      {{ (as_timestamp(now()) - as_timestamp(this.attributes.last_triggered | default(0, true))) > 600 }}
actions:
  - action: button.press
    target:
      entity_id: button.refresh_uspl
mode: single
```

##### Upon Parking
If you use a binary sensor to track when RV is moving / not moving, I suggest triggering a button press when transitioning from moving to not moving state.  This will capture the GPS coordinates at the time the vehicle stops and not the last update interval.  This is relevant when stopping to validate the jurisdiction of a campsite.

### Sensors
The following sensors will be created upon installation.  [Optional sensors](#optional-sensors) are listed separately.

| Sensor | Description |
|--------|-------------|
| Unit Name | This is the high level known name "Yosemite National Park" or "Alabama Hills National Scenic Area."  Shows **Private Land** on private land. |
| Designation | Wilderness Area, National Park etc. |
| Management Name | National Park Service, Bureau of Land Management etc. |
| Management Type | State, Federal, Regional etc. |
| Public Access | Open to the Public, Restricted Access (permit needed), Closed to the Public (military base). |
| API Status | 'On' if last refresh was successful.  'Off' if last refresh failed. |
| Last Successful Refresh | Timestamp of last refresh |

When areas overlap, the sensors show the most specific one (for example a Wilderness Area inside a National Forest), the same as earlier versions.

The **Unit Name** sensor also has these attributes:

| Attribute | Description |
|-----------|-------------|
| underlying_land | The land parcel under a special designation, for example "Bishop Field Office" under Alabama Hills. |
| overlapping_areas | Every area at your location. |
| source | `PAD-US`, `PAD-US (nearby)` when a small gap in PAD-US was filled from an area within 300 m managed by the same agency, or `BLM Surface Management`. |
| surface_manager | Who BLM's map says manages the surface, when it was used. |
| latitude / longitude | The coordinates that were looked up. |
| location_entity | The entity the coordinates came from. |

These sensors will not populate with data until the Refresh USPL button is pressed for the first time.  After that, they keep their last values across restarts.

#### No Internet Connection Scenario
In the event there's no connectivity, the sensors will retain their old values.  API status will be set to 'off'.  Once the condition clears, API status will be set to 'on' and all sensors will refresh.

### Buttons
The integration will create one button

| Button | Description |
|--------|-------------|
| Refresh USPL | Pressing this button will call for the API with the current coordinates. |

The button can be exposed to the UI for manual trigger or via automations previously mentioned.

### Actions

**Public Lands: Look up a location** (`public_lands.lookup`) checks any coordinate and returns the result without changing the sensors, for example to check a destination before you drive there.  Leave the coordinates out to use the current location.

```yaml
action: public_lands.lookup
data:
  latitude: 36.6
  longitude: -118.13
response_variable: land
```

The response has the same values as the sensors.  Any optional sensors that are turned on are included under `extras` (`city_county`, `rules_link`, `campgrounds`).

### Dashboard Visibility Recommendations

If you want to hide USPL sensors when they're unavailable (such as no Internet connectivity), use the API status and conditional visibility in your dashboard.

If you want to hide USPL sensors when on private land, hide when 'Unit Name' is 'Private Land' or 'Non-Protected Area'.

The rules link is clickable when you open **USPL Rules Link** (under Attributes).  To put it on a dashboard, use a Markdown card:

```yaml
type: markdown
content: >
  {% set url = state_attr('sensor.uspl_rules_link', 'url') %}
  {% if url %}
  [{{ states('sensor.uspl_rules_link') }} rules]({{ url }})
  {% endif %}
```

### Example Data

**Public Land**

![image](https://github.com/user-attachments/assets/00ed28f7-26b3-4228-8489-aa490f7b0807)

![image](https://github.com/user-attachments/assets/55b51e88-e30e-4279-a5f0-184be36588fa)

![image](https://github.com/user-attachments/assets/c7ebddaa-8812-429f-bf1b-c62fa6d7a434)

![image](https://github.com/user-attachments/assets/3e7802b6-4a40-4656-91f9-467b24d82469)

**Non-Public Land**

![image](https://github.com/user-attachments/assets/d542a6f6-8fcd-4da2-8b8c-27b513d92afc)

## Notes

- **Connectivity** - Internet is required at the time of the button press.  If an optional lookup fails, its sensor shows unknown, and the land sensors and API Status are not affected.
- **Polling** - The integration does not automatically poll.  It leaves this task to the user to configure either manually or via automation.
- **Frequency** - Please limit your automated refresh period to no less than **10 minutes** while in motion.
- **GPS Accuracy** - The GPS coordinates are limited to four decimal places (-118.1222,36.5597).  This limits the accuracy to about 11 meters.
- **Data Accuracy** - PAD-US is published by USGS (United States Geological Survey) every one to two years; the current release is 4.1 (March 2025).  BLM updates its surface management map as land changes hands.

## Future Enhancements

Ideas being considered for later versions:

- **Camping guidance** - a sensor summarizing whether dispersed camping is generally allowed for the land you are on.
- **Red Flag Warnings** - National Weather Service fire weather warnings for your location.

## 💖 Support

If you found this project useful, consider [buying me a coffee](https://www.buymeacoffee.com/anthonysecco). ☕

## Contributions

Thanks to Smarty Van for [Geolocator](https://github.com/SmartyVan/hass-geolocator) which served as a starting point for this integration.

Open issues, suggest improvements, or contribute pull requests directly here on GitHub.

## AI Disclosure

This project was built largely with AI coding tools (Claude). I directed the design and reviewed the changes, but most of the code and documentation was written by AI. Please review the code before relying on it, and open an issue if you find a problem.

## License

This project is licensed under the MIT License. For more details, see the LICENSE file.
