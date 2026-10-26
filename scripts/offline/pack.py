"""Offline land pack format (Phase 0 spike).

A single SQLite file with simplified PAD-US and BLM surface-management
boundaries plus a grid index, readable with only the Python standard library.

Geometry encoding: coordinates are stored as integers (degrees * 1e5, about
1 m), delta-encoded per ring and written as zigzag varints. Rings use the
even-odd rule, which handles holes without knowing ring orientation.
"""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Iterable, Iterator

SCALE = 100_000  # 5 decimal places
CELL_DEG = 0.25  # grid cell size in degrees
LAYER_PADUS = 1
LAYER_SMA = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS padus (
    fid INTEGER PRIMARY KEY, feat_class TEXT, unit_name TEXT, pub_access TEXT,
    mang_type TEXT, mang_name TEXT, des_tp TEXT, acres REAL, state TEXT,
    minx INTEGER, miny INTEGER, maxx INTEGER, maxy INTEGER, geom BLOB
);
CREATE TABLE IF NOT EXISTS sma (
    fid INTEGER PRIMARY KEY, agency TEXT, state TEXT,
    minx INTEGER, miny INTEGER, maxx INTEGER, maxy INTEGER, geom BLOB
);
CREATE TABLE IF NOT EXISTS grid (
    cell INTEGER, layer INTEGER, fid INTEGER,
    PRIMARY KEY (cell, layer, fid)
) WITHOUT ROWID;
"""


# --- varint geometry codec -------------------------------------------------

def _zz(n: int) -> int:
    return (n << 1) ^ (n >> 63)


def _unzz(z: int) -> int:
    return (z >> 1) ^ -(z & 1)


def _put(buf: bytearray, n: int) -> None:
    while n >= 0x80:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    buf.append(n)


def encode(rings: list[list[list[float]]]) -> tuple[bytes, tuple[int, int, int, int]]:
    """Encode rings of [lon, lat] and return (blob, int bbox)."""
    buf = bytearray()
    _put(buf, len(rings))
    minx = miny = 2**62
    maxx = maxy = -(2**62)
    for ring in rings:
        _put(buf, len(ring))
        px = py = 0
        for x, y, *_ in ring:
            ix, iy = round(x * SCALE), round(y * SCALE)
            _put(buf, _zz(ix - px))
            _put(buf, _zz(iy - py))
            px, py = ix, iy
            minx, maxx = min(minx, ix), max(maxx, ix)
            miny, maxy = min(miny, iy), max(maxy, iy)
    return bytes(buf), (minx, miny, maxx, maxy)


def decode(blob: bytes) -> list[list[tuple[int, int]]]:
    """Decode a blob into rings of integer (x, y)."""
    pos = 0

    def get() -> int:
        nonlocal pos
        shift = result = 0
        while True:
            b = blob[pos]
            pos += 1
            result |= (b & 0x7F) << shift
            if b < 0x80:
                return result
            shift += 7

    rings = []
    for _ in range(get()):
        n = get()
        px = py = 0
        ring = []
        for _ in range(n):
            px += _unzz(get())
            py += _unzz(get())
            ring.append((px, py))
        rings.append(ring)
    return rings


def contains(rings: list[list[tuple[int, int]]], x: int, y: int) -> bool:
    """Even-odd point-in-polygon over all rings."""
    inside = False
    for ring in rings:
        n = len(ring)
        if n < 3:
            continue
        x1, y1 = ring[-1]
        for x2, y2 in ring:
            if (y1 > y) != (y2 > y):
                xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x < xin:
                    inside = not inside
            x1, y1 = x2, y2
    return inside


# --- grid index ------------------------------------------------------------

def cell_of(lon: float, lat: float) -> int:
    return (math.floor(lon / CELL_DEG) + 1000) * 10_000 + (math.floor(lat / CELL_DEG) + 1000)


def cells_for_bbox(minx: int, miny: int, maxx: int, maxy: int) -> Iterator[int]:
    x0 = math.floor(minx / SCALE / CELL_DEG)
    x1 = math.floor(maxx / SCALE / CELL_DEG)
    y0 = math.floor(miny / SCALE / CELL_DEG)
    y1 = math.floor(maxy / SCALE / CELL_DEG)
    for cx in range(x0, x1 + 1):
        for cy in range(y0, y1 + 1):
            yield (cx + 1000) * 10_000 + (cy + 1000)


# --- lookup ----------------------------------------------------------------

def lookup(conn: sqlite3.Connection, lon: float, lat: float) -> tuple[list[dict], list[str]]:
    """Return (PAD-US records, BLM agency codes) containing the point."""
    x, y = round(lon * SCALE), round(lat * SCALE)
    padus: list[dict] = []
    sma: list[str] = []
    rows = conn.execute(
        "SELECT layer, fid FROM grid WHERE cell = ?", (cell_of(lon, lat),)
    ).fetchall()
    for layer, fid in rows:
        if layer == LAYER_PADUS:
            r = conn.execute(
                "SELECT feat_class, unit_name, pub_access, mang_type, mang_name, des_tp, acres,"
                " minx, miny, maxx, maxy, geom FROM padus WHERE fid = ?",
                (fid,),
            ).fetchone()
            if r and r[7] <= x <= r[9] and r[8] <= y <= r[10] and contains(decode(r[11]), x, y):
                padus.append(
                    dict(zip(
                        ("FeatClass", "Unit_Nm", "Pub_Access", "Mang_Type", "Mang_Name", "Des_Tp", "GIS_Acres"),
                        r[:7],
                    ))
                )
        else:
            r = conn.execute(
                "SELECT agency, minx, miny, maxx, maxy, geom FROM sma WHERE fid = ?", (fid,)
            ).fetchone()
            if r and r[1] <= x <= r[3] and r[2] <= y <= r[4] and contains(decode(r[5]), x, y):
                sma.append(r[0])
    return padus, sma


PRIORITY = {"Designation": 0, "Fee": 1, "Easement": 2, "Marine": 3}


def primary(records: Iterable[dict]) -> dict | None:
    """Same choice the integration makes between overlapping areas."""
    recs = list(records)
    if not recs:
        return None
    return min(
        recs,
        key=lambda r: (
            PRIORITY.get(r.get("FeatClass") or "", 9),
            r.get("GIS_Acres") if isinstance(r.get("GIS_Acres"), (int, float)) else float("inf"),
        ),
    )
