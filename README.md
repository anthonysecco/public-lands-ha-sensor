=======
> Upcoming versions will be refactored into the [HACS](https://hacs.xyz/) store.  Stay tuned.

---------------

# USA Public Land Sensor
This YAML configuration will allow you to query the [US Government Protected Area Data](https://www.arcgis.com/apps/mapviewer/index.html?layers=e80a13374cb74cf2bba8903867b29997) (Internet connection permitting) with your current GPS coordinates set in Home Assistant and will post back a response with details.

This sensor should provide information on almost any protected land in the US include federal, state, county, and regional parks.  This can be useful when finding dispersed camping to quickly understand what land and jurisdiction you are within.

## Reading Sensors

| Sensor | Description |
|--------|-------------|
| Unit Name | This is the high level known name "Yosemite National Park" or "Alabama Hills National Scenic Area" |
| Public Access | Open to the public, Restricted (permit needed), Closed Access (military base) |
| Management Type | State, Federal, Regional etc. |
| Management Name | National Park Service, Bureau of Land Management etc. |
| Designation | Wilderness Area, National Park etc. |

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
