# Data Sources

[← Back to README](../README.md)

All sources are official and free.  Only Recreation.gov needs an API key, and only for the optional campground sensor.  An Internet connection is needed at the time of each refresh.

| Source | Used for | Key |
|--------|----------|-----|
| USGS [PAD-US 4.1](https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-web-services) ([Manager Name layer](https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Manager_Name_PADUS/FeatureServer/0)) | The land sensors: protected and public land across the U.S., including federal, state, county and regional lands | No |
| BLM [Surface Management Agency](https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer/1) | Private land, and small gaps in PAD-US such as road corridors inside a park | No |
| National Park Service boundaries | The park for the rules link | No |
| Forest Service forest boundaries | The national forest for the rules link | No |
| Agency websites (blm.gov, nps.gov, fs.usda.gov, fws.gov) | Rules link targets | No |
| U.S. Census Bureau [TIGERweb](https://tigerweb.geo.census.gov/) | City, county and state (optional) | No |
| [Recreation.gov RIDB](https://ridb.recreation.gov/) | Nearby campgrounds (optional) | Yes, your own |
| Forest Service recreation sites | Hiding Forest Service campgrounds closed for the season | No |

A weekly GitHub check confirms these services and links still work.

## How the land lookup works

1. PAD-US is checked at your coordinates.  When areas overlap, the most specific one is shown (a designation such as a Wilderness Area, then the land parcel, then marine areas, then the smallest area).
2. If PAD-US has nothing there, BLM's map says who manages the surface.  Private or undetermined land shows **Private Land**.
3. If BLM says it's public land that PAD-US missed, a PAD-US area within 300 m is used, but only if BLM agrees on the managing agency.

## Accuracy

- **Coordinates** are rounded to four decimal places (about 11 meters).
- **PAD-US** is published by USGS every one to two years; the current release is 4.1 (March 2025).  BLM updates its map as land changes hands.
- **Boundaries:** near a boundary the answer can be off.  Always check posted signs and the managing office's rules.

## Recreation.gov

- **Federal campgrounds only:** mainly Forest Service, BLM, National Park Service and Army Corps.  State and county parks, such as most Bay Area campgrounds, aren't included.
- **No availability:** the API doesn't offer tonight's availability, and Recreation.gov's terms don't allow collecting it from the website.  Tap a campground's name to check on Recreation.gov.
- **No fees:** the fee field is empty for most campgrounds.  Some descriptions mention the fee, for example Tuttle Creek's "$12.00 per site per night".
- **Closures:** only the Forest Service publishes open/closed status.  Other agencies' campgrounds always show.
- **Limits:** one request per refresh; Recreation.gov allows 50 requests per second.
