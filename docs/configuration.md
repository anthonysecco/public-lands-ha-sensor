# Configuration

[← Back to README](../README.md)

Public Lands works with no setup: add the integration and press **Refresh USPL**.  To change a setting, go to **Settings > Devices & Services > Public Lands > Configure**.  Saving reloads the integration, and your last values are kept.

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Location entity | `zone.home` | Where the coordinates come from.  Pick any zone, device tracker, person, or sensor with latitude and longitude, for example your van's GPS tracker. |
| City, county and state sensors | Off | Adds **USPL City** (or "Unincorporated" outside city limits), **USPL County** and **USPL State**, from the U.S. Census Bureau.  Many overnight-parking bans are city rules. |
| Nearby campgrounds sensor | Off | Adds **USPL Nearby Campgrounds** from Recreation.gov.  Needs a Recreation.gov API key. |
| Recreation.gov API key | Empty | Your own free key.  Only needed for nearby campgrounds.  See [below](#recreationgov-api-key). |
| Campground search radius | 25 miles | How far to look for campgrounds: 10 to 25 miles (25 is Recreation.gov's maximum). |

Optional sensors update when you press **Refresh USPL**.  Turning an option off removes its sensors.  See [Sensors](sensors.md) for what each one shows.

## Recreation.gov API key

1. Sign up at [ridb.recreation.gov](https://ridb.recreation.gov/).
2. Create an API key in your account.
3. Paste it into **Recreation.gov API key** on the Configure screen and turn on **Nearby campgrounds sensor**.

The key is checked before it's saved and stays on your Home Assistant.  Recreation.gov's terms don't allow sharing a key, so each user needs their own.

Each refresh makes one Recreation.gov request.  Recreation.gov allows 50 requests per second, so normal use is far below the limit.
