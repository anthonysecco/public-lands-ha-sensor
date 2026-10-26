# Dashboard Cards

<img width="1074" height="545" alt="image" src="https://github.com/user-attachments/assets/f65718f7-50f1-4a70-b8f7-f53dc4eedb52" />

[← Back to README](../README.md)

## Rules link card

Shows where you are and links to the managing office's rules page, plus BLM's camping page on BLM land.  Add a **Markdown** card and paste this into its code editor:

```yaml
type: markdown
content: |
  {% set manager = 'sensor.uspl_management_name' %}
  {% set rules_url = state_attr(manager, 'rules_url') %}
  {% set general_url = state_attr(manager, 'general_rules_url') %}
  {% set county = states('sensor.uspl_county') %}
  {% if county not in ['unknown', 'unavailable'] %}
  {{ states('sensor.uspl_city') }} · {{ county }} · {{ states('sensor.uspl_state') }}
  {% endif %}
  ### {{ states('sensor.uspl_unit_name') }}

  {{ states('sensor.uspl_designation') }} · {{ states(manager) }}

  Access: {{ states('sensor.uspl_public_access') }}

  {% if rules_url %}
  📜 [{{ state_attr(manager, 'rules_office') }}]({{ rules_url }})
  {% if general_url %}

  🏕️ [BLM Camping]({{ general_url }})
  {% endif %}
  {% else %}
  No rules link for this location.
  {% endif %}
```

At Alabama Hills it shows:

> Unincorporated · Inyo County · California
> ### Alabama Hills National Scenic Area
> National Scenic, Botanical or Volcanic Area · Bureau of Land Management
>
> Access: Restricted Access
>
> 📜 [Bishop Field Office](https://www.blm.gov/office/bishop-field-office)
>
> 🏕️ [BLM Camping](https://www.blm.gov/programs/recreation/camping)

The city, county and state line appears only when the city, county and state option is on (see [Configuration](configuration.md)).  "Unincorporated" means you're outside any city's limits.  On private land the card shows "No rules link for this location."

## Nearby campgrounds card

Needs the nearby campgrounds option.  A table of the nearest campgrounds, with a short description of each below it.  Tap the miles for directions, or a name to open the campground's page:

- **Reservable campgrounds** open their Recreation.gov page, to check availability and book.
- **First-come Forest Service campgrounds** open their Forest Service page, which shows whether the site is open.
- **Other campgrounds** open the Recreation.gov page for their area, such as the national forest.

```yaml
type: markdown
content: |
  {% set s = 'sensor.uspl_nearby_campgrounds' %}
  {% set camps = state_attr(s, 'campgrounds') or [] %}
  {% set total = states(s) | int(0) %}
  {% set hidden = state_attr(s, 'closed_hidden') | int(0) %}
  ### ⛺ {{ total }} campground{{ '' if total == 1 else 's' }} within {{ state_attr(s, 'radius_mi') | int(25) }} miles
  {% if total > camps | count %}
  *Showing the nearest {{ camps | count }}*
  {% endif %}
  {% if camps %}
  | Campground | Miles | Phone |
  |:---|---:|:---|
  {%- for c in camps %}
  | {% if c.url %}[{{ c.name }}]({{ c.url }}){% else %}{{ c.name }}{% endif %} | [{{ c.distance_mi }}]({{ c.directions_url }}) | {{ c.phone or '—' }} |
  {%- endfor %}
  {% for c in camps if c.description %}

  **{{ c.name }}:** {{ c.description }}
  {%- endfor %}
  {% else %}
  No Recreation.gov campgrounds nearby.
  {% endif %}
  {% if hidden %}

  *{{ hidden }} closed for the season hidden*
  {% endif %}

  *Data: ridb.recreation.gov*
```

The `{%-` markers keep the table rows together; without them the table breaks apart.  From Lone Pine, CA in late October it shows:

> ### ⛺ 3 campgrounds within 25 miles
>
> | Campground | Miles | Phone |
> |:---|---:|:---|
> | [Tuttle Creek Campground](https://www.recreation.gov/camping/campgrounds/10004620) | [4.6](https://www.google.com/maps/dir/?api=1&destination=36.565,-118.127) | — |
> | [Lone Pine](https://www.recreation.gov/camping/campgrounds/232069) | [6.8](https://www.google.com/maps/dir/?api=1&destination=36.5976111,-118.1848056) | 760-937-6070 |
> | [Grays Meadows](https://www.recreation.gov/camping/campgrounds/232052) | [17.1](https://www.google.com/maps/dir/?api=1&destination=36.7688889,-118.295) | 760-937-6070 |
>
> **Tuttle Creek Campground:** $12.00 per site per night. No reservations. Open all year. Tuttle Creek Campground offers 81 RV/tent sites, with ten pull-through trailer spaces…
>
> **Lone Pine:** Lone Pine Campground is located near the base of Mt. Whitney, the highest peak in the continental United States, offering unparalleled views of the mountain…
>
> **Grays Meadows:** Grays Meadows Campground is situated along Independence Creek in the Onion Valley area of the eastern Sierra Nevada Mountains.
>
> *2 closed for the season hidden*
>
> *Data: ridb.recreation.gov*

Recreation.gov lists mainly federal campgrounds, so the card can show none near cities.  It can't show tonight's availability; tap a campground's name to check.  See [Data Sources](data-sources.md#recreationgov).

## Hiding sensors

- **No connection:** use **API Status** with conditional visibility to hide cards when a refresh failed.
- **Private land:** hide cards when **Unit Name** is "Private Land" or "Non-Protected Area".

## Screenshots

From v0.2; they don't show the newer attributes and options.

**Public land**

![image](https://github.com/user-attachments/assets/00ed28f7-26b3-4228-8489-aa490f7b0807)

![image](https://github.com/user-attachments/assets/55b51e88-e30e-4279-a5f0-184be36588fa)

![image](https://github.com/user-attachments/assets/c7ebddaa-8812-429f-bf1b-c62fa6d7a434)

![image](https://github.com/user-attachments/assets/3e7802b6-4a40-4656-91f9-467b24d82469)

**Non-public land**

![image](https://github.com/user-attachments/assets/d542a6f6-8fcd-4da2-8b8c-27b513d92afc)

**Refresh button**

![image](https://github.com/user-attachments/assets/57a87b6e-a57f-4bb3-8e7f-d66b9b1e4b7e)
