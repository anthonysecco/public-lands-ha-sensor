"""Constants for the Public Lands integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "public_lands"

CONF_LOCATION_ENTITY: Final = "location_entity"
DEFAULT_LOCATION_ENTITY: Final = "zone.home"

# USGS PAD-US 4.1 "Manager Name" layer: returns every overlapping area at a point.
PADUS_QUERY_URL: Final = (
    "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/"
    "Manager_Name_PADUS/FeatureServer/0/query"
)
PADUS_FIELDS: Final = "FeatClass,Unit_Nm,Pub_Access,Mang_Type,Mang_Name,Des_Tp,GIS_Acres"

# BLM Surface Management Agency layer: who manages every acre, including private land.
SMA_QUERY_URL: Final = (
    "https://gis.blm.gov/arcgis/rest/services/lands/"
    "BLM_Natl_SMA_LimitedScale/MapServer/1/query"
)
SMA_FIELDS: Final = "ADMIN_AGENCY_CODE"

# Radius used to fill small gaps in PAD-US (road corridors, inholdings).
NEARBY_DISTANCE_M: Final = 300
REQUEST_TIMEOUT: Final = 20
RETRY_DELAY: Final = 2
COORD_PRECISION: Final = 4

STORAGE_KEY: Final = DOMAIN
STORAGE_VERSION: Final = 1

SOURCE_PADUS: Final = "PAD-US"
SOURCE_PADUS_NEARBY: Final = "PAD-US (nearby)"
SOURCE_SMA: Final = "BLM Surface Management"

PRIVATE_LAND: Final = "Private Land"
NON_PROTECTED_AREA: Final = "Non-Protected Area"
UNKNOWN: Final = "Unknown"

# Same wording as v0.2.x so dashboards and automations keep working.
ACCESS_MAP: Final = {
    "OA": "Open to the Public",
    "RA": "Restricted Access",
    "XA": "Closed to the Public",
    "UK": "Unknown",
}
