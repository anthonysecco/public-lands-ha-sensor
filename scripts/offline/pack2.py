"""Offline land pack format, version 2 (Phase 0 spike).

Changes from version 1:
- Boundaries are cut into pieces along a 0.25 degree grid at build time.
  A lookup reads only the pieces in its own cell. A cell that lies wholly
  inside an area is stored with no geometry at all ("full cell").
- Repeated text (names, codes) is stored once in a strings table.

Reading needs only the Python standard library (sqlite3).
"""

from __future__ import annotations

import math
import sqlite3

from pack import SCALE, contains, decode, encode  # noqa: F401  (re-exported)

CELL_DEG = 0.25
LAYER_PADUS = 1
LAYER_SMA = 2
SMA_FID_OFFSET = 10_000_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS strings (id INTEGER PRIMARY KEY, s TEXT);
CREATE TABLE IF NOT EXISTS areas (
    fid INTEGER PRIMARY KEY, layer INTEGER,
    feat_class INTEGER, unit INTEGER, access INTEGER,
    mtype INTEGER, mname INTEGER, des INTEGER, acres REAL
);
CREATE TABLE IF NOT EXISTS pieces (
    cell INTEGER, fid INTEGER, geom BLOB,
    PRIMARY KEY (cell, fid)
) WITHOUT ROWID;
"""


def cell_xy(lon: float, lat: float) -> tuple[int, int]:
    return math.floor(lon / CELL_DEG), math.floor(lat / CELL_DEG)


def cell_id(cx: int, cy: int) -> int:
    return (cx + 1000) * 10_000 + (cy + 1000)


def cell_of(lon: float, lat: float) -> int:
    return cell_id(*cell_xy(lon, lat))


def _s(conn: sqlite3.Connection, sid: int | None) -> str | None:
    if sid is None:
        return None
    row = conn.execute("SELECT s FROM strings WHERE id = ?", (sid,)).fetchone()
    return row[0] if row else None


def lookup(conn: sqlite3.Connection, lon: float, lat: float) -> tuple[list[dict], list[str]]:
    """Return (PAD-US records, BLM agency codes) at a point."""
    x, y = round(lon * SCALE), round(lat * SCALE)
    hits = [
        fid
        for fid, geom in conn.execute(
            "SELECT fid, geom FROM pieces WHERE cell = ?", (cell_of(lon, lat),)
        )
        if geom is None or contains(decode(geom), x, y)
    ]
    padus: list[dict] = []
    sma: list[str] = []
    for fid in hits:
        row = conn.execute(
            "SELECT layer, feat_class, unit, access, mtype, mname, des, acres FROM areas WHERE fid = ?",
            (fid,),
        ).fetchone()
        if not row:
            continue
        layer, fc, unit, access, mtype, mname, des, acres = row
        if layer == LAYER_SMA:
            sma.append(_s(conn, mname))
        else:
            padus.append({
                "FeatClass": _s(conn, fc), "Unit_Nm": _s(conn, unit), "Pub_Access": _s(conn, access),
                "Mang_Type": _s(conn, mtype), "Mang_Name": _s(conn, mname), "Des_Tp": _s(conn, des),
                "GIS_Acres": acres,
            })
    return padus, sma
