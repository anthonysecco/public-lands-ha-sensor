# Public Land Sensor
This YAML configuration will allow you to query the [US Government Protected Area Data](https://www.arcgis.com/apps/mapviewer/index.html?layers=e80a13374cb74cf2bba8903867b29997) (Internet connection permitting) with your current GPS coordinates set in Home Assistant and will post back a response with details.

This sensor should provide information on almost any protected land in the US include federal, state, county, and regional parks.  This can be useful when finding disperesed camping to quickly understand what land and jurisdiction you are within.



## Reading Sensors

| Sensor | Description |
|--------|-------------|
| Unit Name | This is the high level known name "Yosemite National Park" or "Alabama Hills National Scenic Area" |
| Public Access | Open to the public, Restricted (permit needed), Closed Access (military base) |
| Management Type | State, Federal, Regional etc. |
| Management Name | National Park Service, Bureau of Land Management etc. |
| Designation | Wilderness Area, National Park etc. |

Here are some examples:

![image](https://github.com/user-attachments/assets/41264f11-ddad-4848-8ee5-fab048410b7e)

![image](https://github.com/user-attachments/assets/c3ac2d71-c6d2-41ef-a165-859d7a71b247)

![image](https://github.com/user-attachments/assets/f4857c65-3418-4a58-81db-aba82a3cb361)

When you're not on protected lands you'll see the following:

![image](https://github.com/user-attachments/assets/d09d836f-99b2-4c6e-aa90-eab69c144fd5)

### Notes

Accuracy - The GPS coordinateds are limited to four decimal points (-118.1222,36.5597).  This limits the accuracy to 10-15 meters.

Rate Limit - By default the sensor refreshes ever 600s (10 minutes) but can be adjusted up or town.  I haven't confirmed the rate limits so be mindful of that.
