"""Constants for the Public Lands integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "public_lands"

CONF_LOCATION_ENTITY: Final = "location_entity"
DEFAULT_LOCATION_ENTITY: Final = "zone.home"

# Optional features (all off by default).
CONF_CITY_COUNTY: Final = "city_county"
CONF_CAMPGROUNDS: Final = "campgrounds"
CONF_RIDB_API_KEY: Final = "ridb_api_key"
CONF_SEARCH_RADIUS: Final = "search_radius"
DEFAULT_SEARCH_RADIUS: Final = 25
MIN_SEARCH_RADIUS: Final = 5
MAX_SEARCH_RADIUS: Final = 25  # Recreation.gov's maximum, in miles

FEATURE_CITY_COUNTY: Final = "city_county"

# Removed in v0.3.3: the rules link moved to attributes on USPL Management Name.
REMOVED_UNIQUE_IDS: Final = ("uspl_rules_link",)
FEATURE_CAMPGROUNDS: Final = "campgrounds"

# Census Bureau TIGERweb: layer 28 = Incorporated Places, 82 = Counties.
CENSUS_BASE_URL: Final = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer"
)
CENSUS_PLACES_URL: Final = f"{CENSUS_BASE_URL}/28/query"
CENSUS_COUNTIES_URL: Final = f"{CENSUS_BASE_URL}/82/query"

NPS_BOUNDARY_URL: Final = (
    "https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/"
    "NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2/query"
)
USFS_FOREST_URL: Final = (
    "https://apps.fs.usda.gov/arcx/rest/services/EDW/"
    "EDW_ForestSystemBoundaries_01/MapServer/0/query"
)

RIDB_FACILITIES_URL: Final = "https://ridb.recreation.gov/api/v1/facilities"
RIDB_ATTRIBUTION: Final = "Data source: ridb.recreation.gov"
MAX_CAMPGROUNDS_LISTED: Final = 10

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
