"""Compare offline pack answers with the live services (Phase 0 spike).

Samples random points (seeded, so runs are repeatable) and, for each, works
out the answer the integration would show from the live services and from
the offline pack, then reports how often they agree and how fast offline
lookups are.

Usage: python check_accuracy.py PACK.sqlite [OUTPUT_DIR]
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import random
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).parent))
import pack  # noqa: E402

PADUS_QUERY = (
    "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/"
    "Manager_Name_PADUS/FeatureServer/0/query"
)
SMA_QUERY = (
    "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer/1/query"
)
USER_AGENT = "public-lands-ha offline accuracy check (+https://github.com/anthonysecco/public-lands-ha-sensor)"
PRIVATE = {"PVT", "UND"}

BOXES = {
    "California": (-124.4, 32.5, -114.1, 42.0),
    "Nevada": (-120.0, 35.0, -114.0, 42.0),
    "Arizona": (-114.8, 31.3, -109.0, 37.0),
    "Lower 48": (-124.7, 24.5, -66.9, 49.4),
}
PER_BOX = 120
EDGE_POINTS = 150
EDGE_OFFSET_M = 30


def live_query(url: str, lon: float, lat: float, fields: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "outFields": fields,
        "returnGeometry": "false", "f": "json",
    })
    last: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(f"{url}?{params}", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            if "error" in data:
                raise RuntimeError(data["error"])
            return [f["attributes"] for f in data.get("features", [])]
        except Exception as err:  # noqa: BLE001
            time.sleep(5 * (attempt + 1))
            last = err
    raise RuntimeError(last)


def label(padus: list[dict], sma: list[str]) -> str:
    """What the integration would show, reduced to a comparable label."""
    p = pack.primary(padus)
    if p:
        return f"{p['Unit_Nm']} [{p['FeatClass']}]"
    agencies = sorted({a for a in sma if a and a not in PRIVATE})
    return f"BLM map: {agencies[0]}" if agencies else "Private / none"


def live_label(lon: float, lat: float) -> str:
    padus = live_query(PADUS_QUERY, lon, lat, "Unit_Nm,FeatClass,GIS_Acres")
    time.sleep(0.2)
    sma = [] if padus else [a.get("ADMIN_AGENCY_CODE") for a in live_query(SMA_QUERY, lon, lat, "ADMIN_AGENCY_CODE")]
    time.sleep(0.2)
    return label(padus, sma)


def edge_points(conn: sqlite3.Connection, rng: random.Random) -> list[tuple[float, float]]:
    """Points about 30 m from a random boundary vertex in CA, NV or AZ."""
    ids = [r[0] for r in conn.execute("SELECT fid FROM padus WHERE state IN ('CA','NV','AZ')")]
    pts = []
    for fid in rng.sample(ids, min(EDGE_POINTS, len(ids))):
        (blob,) = conn.execute("SELECT geom FROM padus WHERE fid = ?", (fid,)).fetchone()
        ring = rng.choice(pack.decode(blob))
        x, y = rng.choice(ring)
        lat = y / pack.SCALE
        ang = rng.uniform(0, 2 * math.pi)
        dlat = EDGE_OFFSET_M * math.sin(ang) / 111_320
        dlon = EDGE_OFFSET_M * math.cos(ang) / (111_320 * math.cos(math.radians(lat)))
        pts.append((x / pack.SCALE + dlon, lat + dlat))
    return pts


def main() -> None:
    db = Path(sys.argv[1])
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    conn = sqlite3.connect(db)
    rng = random.Random(4242)

    groups: dict[str, list[tuple[float, float]]] = {}
    for name, (x0, y0, x1, y1) in BOXES.items():
        groups[name] = [(rng.uniform(x0, x1), rng.uniform(y0, y1)) for _ in range(PER_BOX)]
    groups[f"Near boundaries (~{EDGE_OFFSET_M} m)"] = edge_points(conn, rng)

    results = {}
    mismatches = []
    timings = []
    for name, pts in groups.items():
        agree = 0
        for lon, lat in pts:
            t = time.perf_counter()
            padus, sma = pack.lookup(conn, lon, lat)
            local = label(padus, sma)
            timings.append((time.perf_counter() - t) * 1000)
            live = live_label(lon, lat)
            if local == live:
                agree += 1
            else:
                mismatches.append({"group": name, "lat": round(lat, 5), "lon": round(lon, 5),
                                   "live": live, "offline": local})
        results[name] = {"points": len(pts), "agree": agree, "pct": round(100 * agree / len(pts), 1)}
        print(name, results[name], flush=True)

    timings.sort()
    speed = {
        "median_ms": round(timings[len(timings) // 2], 2),
        "p95_ms": round(timings[int(len(timings) * 0.95)], 2),
        "max_ms": round(timings[-1], 2),
    }
    report = {"results": results, "speed": speed, "mismatches": mismatches}
    (out / "accuracy.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"results": results, "speed": speed}, indent=2))

    lines = ["## Offline vs live accuracy", "", "| Sample | Points | Agree | % |", "|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {name} | {r['points']} | {r['agree']} | {r['pct']} |")
    lines += ["", f"Offline lookup time: median {speed['median_ms']} ms, p95 {speed['p95_ms']} ms, max {speed['max_ms']} ms", ""]
    if mismatches:
        lines += ["### Mismatches (first 40)", "", "| Sample | Lat, Lon | Live | Offline |", "|---|---|---|---|"]
        for m in mismatches[:40]:
            lines.append(f"| {m['group']} | {m['lat']}, {m['lon']} | {m['live']} | {m['offline']} |")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
