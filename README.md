![icon](https://github.com/user-attachments/assets/de5ad0b3-8f84-4b37-a003-0a3bd3b0b2b2)

# Public Lands
This is a HACS Custom Component that queries ARCGIS [US Government Protected Area Data](https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/Protection_Mechanism_Category_PADUS/FeatureServer/0) with your current GPS coordinates set in Home Assistant and will post back a response with details.

This sensor should provide information on almost any protected land in the United States including federal, state, county, and regional lands.  This can be useful when finding dispersed camping to quickly understand what land and jurisdiction you are within.

> Note: An Internet connection is required for this integration to work.

⚠️ **Dispersed Camping  Disclaimer** ⚠️

Use your judgement when deciding where to setup a dispersed camp.  I am not responsible for the accuracy of the data or whether you run into problems at your chosen location.  Refer to the applicable government website for rules and regulations on dispersed camping for your chosen location.

With that out of the way, let's get started...

## Installation

To install, simply click the link below.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=anthonysecco&repository=public-lands-ha-sensor&category=integration)

> This integration is not yet available in the HACS default store.  Meanwhile, it will be added as a custom repository.

Once installed, restart Home Assistant and the sensors will appear.

### Manual Installation

1. Download the source code of the [latest release](https://github.com/anthonysecco/public-lands-ha-sensor/releases).
2. Unzip the source code download.
3. Copy **public_lands** from the **custom_components** directory you just downloaded to your Home Assistant **custom_components** directory:
   ```
   config/custom_components/public_lands/
   ```
4. Restart Home Assistant.

## Usage

Once the integration is added, it will automatically create the sensors and button.  No configuration needed.

No data will be found in those sensors until it is triggered.  Please see the following section for details on that.

###Trigger Methods

#### Press the Button
This is simple.  If you want to know your USPL status immediately based on Home Assistant's current coordinate, press the button.

![image](https://github.com/user-attachments/assets/57a87b6e-a57f-4bb3-8e7f-d66b9b1e4b7e)

#### Create Automation

##### Upon GPS Update
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

##### Upon Parking
If you use a binary sensor to track when RV is moving / not moving, I suggest triggering a button press when transitioning from moving to not moving state.  This will capture the GPS coordinates at the time the vehicle stops and not the last update interval.  This is relevant when stopping to validate the jurisdiction of a campsite.

### Sensors
The following sensors will be created upon installation.

| Sensor | Description |
|--------|-------------|
| Unit Name | This is the high level known name "Yosemite National Park" or "Alabama Hills National Scenic Area." |
| Designation | Wilderness Area, National Park etc. |
| Management Name | National Park Service, Bureau of Land Management etc. |
| Management Type | State, Federal, Regional etc. |
| Public Access | Open to the public, Restricted (permit needed), Closed Access (military base). |
| API Status | 'On' if last refresh was successful.  'Off' if last refresh failed. |
| Last Successful Refresh | Timestamp of last referesh |

These sensors will not populate with data unless the USPL Refresh Button is pressed

### Buttons
The integration will create one button

| Button | Description |
|--------|-------------|
| Refresh USPL | Pressing this button will call for the API with Home Assistant's current coordinates. |

The button can be exposed to the UI for manual trigger or via automations previously mentioned.

### Dashboard Visability Recommendations

If you want to hide USPL sensors when they're unavailable (such as no Internet connectivity), use the API status and conditional visability in your dashboard.

If you want to hide USPL sensors when on private land, hide when 'Unit Name' is 'Non-Protected Area'.

### Example Data

**Public Land**

![image](https://github.com/user-attachments/assets/00ed28f7-26b3-4228-8489-aa490f7b0807)

![image](https://github.com/user-attachments/assets/55b51e88-e30e-4279-a5f0-184be36588fa)

![image](https://github.com/user-attachments/assets/c7ebddaa-8812-429f-bf1b-c62fa6d7a434)

![image](https://github.com/user-attachments/assets/3e7802b6-4a40-4656-91f9-467b24d82469)

**Non-Public Land**

![image](https://github.com/user-attachments/assets/d542a6f6-8fcd-4da2-8b8c-27b513d92afc)

## Notes

- **Connectivity** - Internet is required at the time of the button press.
- **Polling** - The integration does not automatically poll.  It leaves this task to the user to configure either manually or via automation.
- **Frequency** - Please limit you refresh period to no less than **10 minutes** when in motion.
- **GPS Accuracy** - The GPS coordinateds are limited to four decimal points (-118.1222,36.5597).  This limits the accuracy to 15 meters.
- **Data Accuracy** - The API data is refreshed annually in June by USGS (United States Geological Survey).

## Contributions

Open issues, suggest improvements, or contribute pull requests directly here on GitHub.

## License

This project is licensed under the MIT License. For more details, see the LICENSE file.&#x20;
