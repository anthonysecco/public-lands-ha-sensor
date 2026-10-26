# Sensors and Actions

[← Back to README](../README.md)

Sensors are empty until **Refresh USPL** is pressed for the first time.  After that, they keep their last values across restarts and when a refresh fails.

## Land sensors

| Sensor | Entity | Description |
|--------|--------|-------------|
| Unit Name | `sensor.uspl_unit_name` | The area's name, for example "Yosemite National Park" or "Alabama Hills National Scenic Area".  Shows **Private Land** on private land. |
| Designation | `sensor.uspl_designation` | Wilderness Area, National Park, National Forest, etc. |
| Management Name | `sensor.uspl_management_name` | National Park Service, Bureau of Land Management, etc. |
| Management Type | `sensor.uspl_management_type` | Federal, State, Local Government, etc. |
| Public Access | `sensor.uspl_public_access` | Open to the Public, Restricted Access (permit needed) or Closed to the Public (for example a military base). |
| API Status | `sensor.uspl_api_status` | On if the last refresh worked, off if it failed. |
| Last Successful Refresh | `sensor.uspl_last_successful_refresh` | When the last refresh worked. |

When areas overlap, the sensors show the most specific one, for example a Wilderness Area inside a National Forest.

### Unit Name attributes

| Attribute | Description |
|-----------|-------------|
| underlying_land | The land parcel under a special designation, for example "Bishop Field Office" under Alabama Hills. |
| overlapping_areas | Every area at your location. |
| source | `PAD-US`; `PAD-US (nearby)` when a small gap in PAD-US was filled from an area within 300 m managed by the same agency; or `BLM Surface Management`. |
| surface_manager | Who BLM's map says manages the surface, when it was used. |
| latitude / longitude | The coordinates that were looked up. |
| location_entity | The entity the coordinates came from. |

### Management Name attributes (rules link)

A link to the managing office's own web page, so you can read its rules.  Home Assistant shows these links as clickable when you open the sensor.

| Attribute | Description |
|-----------|-------------|
| rules_office | The office the link is for, for example "Bishop Field Office" at Alabama Hills. |
| rules_url | That office's page: the BLM field office, National Park, National Forest or Wildlife Refuge.  Other public land links to a Recreation.gov search. |
| general_rules_url | BLM's general camping rules page (on BLM land only). |

These attributes are left out on private land.  National Park and National Forest links take one extra lookup per refresh; if it fails, they're left out and the other sensors still update.

## Optional sensors

Turned on under [Configuration](configuration.md).

| Sensor | Entity | Description |
|--------|--------|-------------|
| City | `sensor.uspl_city` | The incorporated city you're in, or "Unincorporated".  Attribute `full_name`, for example "San Jose city". |
| County | `sensor.uspl_county` | For example "Inyo County". |
| State | `sensor.uspl_state` | For example "California". |
| Nearby Campgrounds | `sensor.uspl_nearby_campgrounds` | How many Recreation.gov campgrounds and dispersed-camping sites are within the search radius. |

### Nearby Campgrounds attributes

| Attribute | Description |
|-----------|-------------|
| campgrounds | The nearest ten, each with `name`, `distance_mi`, `booking` (Reservable, First come or Dispersed), `reservable`, `dispersed`, `stay_limit`, `phone`, `description` (the start of Recreation.gov's description, up to about 160 characters), `url` (Recreation.gov page) and `directions_url` (Google Maps).  `booking` comes from Recreation.gov's reservable flag, which isn't always right. |
| nearest / nearest_distance_mi | The closest one. |
| closed_hidden | How many campgrounds were left out because the Forest Service reports them closed for the season.  Other agencies don't publish a status, so their campgrounds always show. |
| radius_mi | The search radius used. |
| attribution | "Data source: ridb.recreation.gov". |

If an optional lookup fails, its sensor shows unknown; the land sensors and API Status are not affected.

## Button

| Button | Entity | Description |
|--------|--------|-------------|
| Refresh USPL | `button.refresh_uspl` | Looks up your current location.  Press it yourself or from an [automation](automations.md). |

## Actions

**Public Lands: Look up a location** (`public_lands.lookup`) checks any coordinate and returns the result without changing the sensors, for example to check a destination before you drive there.  Leave the coordinates out to use the current location.

```yaml
action: public_lands.lookup
data:
  latitude: 36.6
  longitude: -118.13
response_variable: land
```

The response has the same values as the sensors, plus the rules link under `rules_link`.  Optional sensors that are turned on are included under `extras` (`city_county`, `campgrounds`).
