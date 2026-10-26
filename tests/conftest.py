"""Fixtures for Public Lands tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from custom_components.public_lands.const import PADUS_QUERY_URL, SMA_QUERY_URL

pytest_plugins = "pytest_homeassistant_custom_component"

NEARBY_URL = f"{PADUS_QUERY_URL}?distance=300"

# Records copied from live PAD-US 4.1 responses (Oct 2026).
BLM_FEE = {
    "FeatClass": "Fee",
    "Unit_Nm": "Bishop Field Office",
    "Pub_Access": "OA",
    "Mang_Type": "FED",
    "Mang_Name": "BLM",
    "Des_Tp": "PUB",
    "GIS_Acres": 751921,
}
ALABAMA_HILLS = {
    "FeatClass": "Designation",
    "Unit_Nm": "Alabama Hills National Scenic Area",
    "Pub_Access": "RA",
    "Mang_Type": "FED",
    "Mang_Name": "BLM",
    "Des_Tp": "NSBV",
    "GIS_Acres": 18839,
}
REDWOOD_FEE = {
    "FeatClass": "Fee",
    "Unit_Nm": "Redwood National Park",
    "Pub_Access": "OA",
    "Mang_Type": "FED",
    "Mang_Name": "NPS",
    "Des_Tp": "NP",
    "GIS_Acres": 77974,
}
REDWOOD_MARINE = {
    "FeatClass": "Marine",
    "Unit_Nm": "Redwood National Park",
    "Pub_Access": "OA",
    "Mang_Type": "FED",
    "Mang_Name": "NPS",
    "Des_Tp": "MPA",
    "GIS_Acres": 115640,
}
DEATH_VALLEY_WILDERNESS = {
    "FeatClass": "Designation",
    "Unit_Nm": "Death Valley Wilderness Area",
    "Pub_Access": "RA",
    "Mang_Type": "FED",
    "Mang_Name": "NPS",
    "Des_Tp": "WA",
    "GIS_Acres": 3144801,
}
DEATH_VALLEY_FEE = {
    "FeatClass": "Fee",
    "Unit_Nm": "Death Valley National Park",
    "Pub_Access": "OA",
    "Mang_Type": "FED",
    "Mang_Name": "NPS",
    "Des_Tp": "NP",
    "GIS_Acres": 3270447,
}


def features(*records: dict[str, Any]) -> dict[str, Any]:
    """Build an ArcGIS query response."""
    return {"features": [{"attributes": r} for r in records]}


def sma(code: str) -> dict[str, Any]:
    """Build a BLM surface management response."""
    return {"features": [{"attributes": {"ADMIN_AGENCY_CODE": code}}]}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading custom_components in every test."""
    yield


@pytest.fixture(autouse=True)
def no_retry_delay():
    """Skip the wait between retries."""
    with patch("custom_components.public_lands.const.RETRY_DELAY", 0):
        yield


@pytest.fixture
def mock_alabama_hills(aioclient_mock):
    """PAD-US returns BLM land with the Alabama Hills Scenic Area on top."""
    aioclient_mock.get(PADUS_QUERY_URL, json=features(BLM_FEE, ALABAMA_HILLS))
    return aioclient_mock


__all__ = [
    "ALABAMA_HILLS",
    "BLM_FEE",
    "DEATH_VALLEY_FEE",
    "DEATH_VALLEY_WILDERNESS",
    "NEARBY_URL",
    "PADUS_QUERY_URL",
    "REDWOOD_FEE",
    "REDWOOD_MARINE",
    "SMA_QUERY_URL",
    "features",
    "sma",
]
