"""Links to each managing agency's own page for its rules.

Plain Python with no Home Assistant imports, so scripts/check_links.py can use
the same link patterns to check that they still work.
"""

from __future__ import annotations

import re
from urllib.parse import quote

from .forests import FOREST_SLUGS

BLM_CAMPING_URL = "https://www.blm.gov/programs/recreation/camping"
RECREATION_GOV_SEARCH_URL = "https://www.recreation.gov/search?q="

_BLM_OFFICE_SUFFIXES = ("Field Office", "District Office")
_FWS_REFUGE_SUFFIX = " National Wildlife Refuge"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def blm_office_url(unit_name: str) -> str | None:
    """blm.gov page for a BLM field or district office, e.g. 'Bishop Field Office'."""
    if not unit_name.endswith(_BLM_OFFICE_SUFFIXES):
        return None
    return f"https://www.blm.gov/office/{_slug(unit_name)}"


def fws_refuge_url(unit_name: str) -> str | None:
    """fws.gov page for a National Wildlife Refuge."""
    if not unit_name.endswith(_FWS_REFUGE_SUFFIX):
        return None
    base = unit_name[: -len(_FWS_REFUGE_SUFFIX)]
    # Join initials so "J. N. Ding Darling" becomes "jn-ding-darling".
    base = re.sub(r"\b([A-Za-z])\.\s*(?=[A-Za-z]\.)", r"\1", base).replace(".", "")
    base = base.replace("&", "and")
    return f"https://www.fws.gov/refuge/{_slug(base)}"


def nps_unit_url(unit_code: str) -> str:
    """nps.gov home page for a park unit code, e.g. 'YOSE'."""
    return f"https://www.nps.gov/{unit_code.strip().lower()}/index.htm"


def forest_url(forest_org_code: str) -> str | None:
    """fs.usda.gov page for a national forest, by its 4-digit org code."""
    slug = FOREST_SLUGS.get(forest_org_code)
    return f"https://www.fs.usda.gov/{slug}" if slug else None


def recreation_gov_search_url(name: str) -> str:
    """Recreation.gov search for a place name."""
    return RECREATION_GOV_SEARCH_URL + quote(name)
