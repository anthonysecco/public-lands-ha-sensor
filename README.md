![icon](https://github.com/user-attachments/assets/de5ad0b3-8f84-4b37-a003-0a3bd3b0b2b2)

# Public Lands
This is a HACS Custom Component that queries ARCGIS [US Government Protected Area Data]([https://www.arcgis.com/apps/mapviewer/index.html?layers=e80a13374cb74cf2bba8903867b29997](https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/Protection_Mechanism_Category_PADUS/FeatureServer/0)) with your current GPS coordinates set in Home Assistant and will post back a response with details.

This sensor should provide information on almost any protected land in the United States including federal, state, county, and regional lands.  This can be useful when finding dispersed camping to quickly understand what land and jurisdiction you are within.

> Note: An Internet connection is required at the time of query.

## Installation

[![Open this repository in your Home Assistant instance.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=anthonysecco&repository=public-lands-ha-sensor&category=integration)

### Manual Installation

1. Download the source code of the [latest release](https://github.com/anthonysecco/public-lands-ha-sensor/releases).
2. Unzip the source code download.
3. Copy **public_lands** from the **custom_components** directory you just downloaded to your Home Assistant **custom_components** directory:
   ```
   config/custom_components/public_lands/
   ```
4. Restart Home Assistant.

## Trigger Methods

### Press the Button
This is simple.  If you want to know your USPL status immediately based on Home Assistant's current coordinate, press the button.

### Create Automation

#### Upon GPS Update
Here's an example automation that will refresh USPL data when the zone.home is updated.  It will update at 10 minute intervals when the GPS coordinates are changing.

```yaml
alias: "USPL: Update via Button"
description: "Presses the Refresh USPL button when zone.home changes, throttled to once every 10 minutes."
trigger:
  - platform: state
    entity_id: zone.home
condition:
  - condition: template
    value_template: >
      {{ (as_timestamp(now()) - as_timestamp(this.last_triggered | default(0))) > 600 }}
action:
  - service: button.press
    target:
      entity_id: button.refresh_uspl
mode: single
```

#### Upon Parking
If you use a binary sensor to track when RV is moving / not moving, I suggest triggering a button press when transitioning from moving to not moving state.  This will capture the GPS coordinates at the time the vehicle stops and not the last update interval.  This is relevant when stopping to validate the jurisdiction of a campsite.


## Reading Sensors

| Sensor | Description |
|--------|-------------|
| Unit Name | This is the high level known name "Yosemite National Park" or "Alabama Hills National Scenic Area." |
| Designation | Wilderness Area, National Park etc. |
| Management Name | National Park Service, Bureau of Land Management etc. |
| Management Type | State, Federal, Regional etc. |
| Public Access | Open to the public, Restricted (permit needed), Closed Access (military base). |
| API Status | 'On' if last refresh was successful.  'Off' if last refresh failed. |
| Last Successful Refresh | Timestamp of last referesh |

If you want to hide USPL sensors when they're unavailable (such as no Internet connectivity), use the API status and conditional visability in your dashboard.


## Example Data

Examples include the following:

![image](https://github.com/user-attachments/assets/41264f11-ddad-4848-8ee5-fab048410b7e)

![image](https://github.com/user-attachments/assets/c3ac2d71-c6d2-41ef-a165-859d7a71b247)

![image](https://github.com/user-attachments/assets/f4857c65-3418-4a58-81db-aba82a3cb361)

When you're not on protected lands you'll see the following:

![image](https://github.com/user-attachments/assets/7b9eb1bc-d110-4598-8b87-328c81c1b7ca)

I suggest using a condition to hide the card when 'Unit Name' is "Non-Protected Area" so as to reduce the clutter on your dashboard.

You may use the refresh button to immediately check your current location.  This can be useful when pulling up to a site.

## Notes

Accuracy - The GPS coordinateds are limited to four decimal points (-118.1222,36.5597).  This limits the accuracy to 15 meters.

By default the sensor refreshes ever 3600s (1 hour).  If you need to immediately check your location, use the refresh button.
