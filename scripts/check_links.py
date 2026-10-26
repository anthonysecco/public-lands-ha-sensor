"""Weekly check that the data services and agency links still work.

Agencies move pages and services without notice. This script checks every
service the integration queries and every link pattern it builds, and exits
with an error if something is broken so the scheduled workflow fails and
GitHub sends a notification.

Uses only the standard library and loads the integration's link code directly,
so Home Assistant does not need to be installed.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
import time
import types
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
INTEGRATION = ROOT / "custom_components" / "public_lands"

# Import rules.py and forests.py without running the integration's __init__.py.
_pkg = types.ModuleType("public_lands_links")
_pkg.__path__ = [str(INTEGRATION)]
sys.modules["public_lands_links"] = _pkg
rules = importlib.import_module("public_lands_links.rules")
forests = importlib.import_module("public_lands_links.forests")

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) public-lands-ha link check "
    "(+https://github.com/anthonysecco/public-lands-ha-sensor)"
)
TIMEOUT = 40
RATE_LIMITED = {403, 429}

failures: list[str] = []
skipped: list[str] = []


def fetch(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as err:
            return err.code, b""
        except (urllib.error.URLError, TimeoutError) as err:
            if attempt:
                return 0, str(err).encode()
            time.sleep(5)
    return 0, b""


def check_page(url: str) -> None:
    status, _ = fetch(url)
    if status == 200:
        print(f"ok    {url}")
    elif status in RATE_LIMITED:
        skipped.append(url)
        print(f"skip  {url} (HTTP {status}, rate limited)")
    else:
        failures.append(f"{url} -> HTTP {status}")
        print(f"FAIL  {url} -> HTTP {status}")


def check_point_query(name: str, url: str, lat: float, lon: float, field: str, expected: str) -> None:
    params = urllib.parse.urlencode(
        {
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "outFields": field,
            "returnGeometry": "false",
            "f": "json",
        }
    )
    status, body = fetch(f"{url}?{params}")
    try:
        values = [f["attributes"].get(field) for f in json.loads(body)["features"]]
    except (ValueError, KeyError, TypeError):
        values = []
    if status == 200 and expected in values:
        print(f"ok    {name}: {expected}")
    else:
        failures.append(f"{name}: expected {expected!r}, got HTTP {status} {values}")
        print(f"FAIL  {name}: expected {expected!r}, got HTTP {status} {values}")


def main() -> int:
    const = {}
    exec((INTEGRATION / "const.py").read_text(encoding="utf-8"), const)  # noqa: S102

    print("== Data services")
    check_point_query("PAD-US", const["PADUS_QUERY_URL"], 36.6, -118.13, "Unit_Nm", "Alabama Hills National Scenic Area")
    check_point_query("BLM surface management", const["SMA_QUERY_URL"], 36.6, -118.13, "ADMIN_AGENCY_CODE", "BLM")
    check_point_query("Census places", const["CENSUS_PLACES_URL"], 37.3352, -121.8811, "NAME", "San Jose city")
    check_point_query("Census counties", const["CENSUS_COUNTIES_URL"], 37.3352, -121.8811, "NAME", "Santa Clara County")
    check_point_query("NPS boundaries", const["NPS_BOUNDARY_URL"], 37.7456, -119.5936, "UNIT_CODE", "YOSE")
    check_point_query("Forest boundaries", const["USFS_FOREST_URL"], 37.65, -118.95, "forestorgcode", "0504")
    status, _ = fetch(f"{const['RIDB_FACILITIES_URL']}?limit=1")
    if status == 401:
        print("ok    Recreation.gov API answers (401 without a key)")
    else:
        failures.append(f"Recreation.gov API: expected 401 without a key, got {status}")
        print(f"FAIL  Recreation.gov API: expected 401 without a key, got {status}")

    print("== Agency links")
    for url in (
        rules.BLM_CAMPING_URL,
        rules.blm_office_url("Bishop Field Office"),
        rules.nps_unit_url("YOSE"),
        rules.fws_refuge_url("Desert National Wildlife Refuge"),
        rules.fws_refuge_url("J. N. Ding Darling National Wildlife Refuge"),
        rules.recreation_gov_search_url("Alabama Hills"),
    ):
        check_page(url)
        time.sleep(1)

    print(f"== Forest links ({len(forests.FOREST_SLUGS)})")
    for code in forests.FOREST_SLUGS:
        check_page(rules.forest_url(code))
        time.sleep(3)  # the Forest Service rate-limits quick requests

    print(f"\n{len(failures)} failed, {len(skipped)} skipped (rate limited)")
    for failure in failures:
        print(f"  - {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
