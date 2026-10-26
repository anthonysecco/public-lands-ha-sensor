"""Build the offline land pack from the official services (Phase 0 spike).

Pages through the USGS PAD-US 4.1 Manager Name service and the BLM Surface
Management Agency service one request at a time, asking the servers to
simplify boundaries to about 20 m, and writes a single SQLite pack. BLM's
private and unclassified polygons are skipped: offline, "no public, tribal or
state land found" already means private land.

Usage: python build_pack.py OUTPUT_DIR
"""

from __future__ import annotations

import gzip
import json
import lzma
import os
from pathlib import Path
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).parent))
import pack  # noqa: E402

PADUS_LAYER = (
    "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/"
    "Manager_Name_PADUS/FeatureServer/0"
)
SMA_LAYER = (
    "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer/1"
)
USER_AGENT = (
    "public-lands-ha offline pack builder "
    "(+https://github.com/anthonysecco/public-lands-ha-sensor)"
)
SIMPLIFY_DEG = "0.0002"  # about 20 m
PAGE = 2000
PAUSE = 0.5  # seconds between requests, to be gentle on the servers
SAMPLE_STATES = ("CA", "NV", "AZ", "MD")


def get_json(url: str, params: dict[str, str]) -> dict:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    for attempt in range(5):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.load(resp)
            if "error" in data:
                raise RuntimeError(data["error"])
            return data
        except Exception as err:  # noqa: BLE001
            wait = 15 * (attempt + 1)
            print(f"  request failed ({err}); retrying in {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"giving up on {full}")


def oid_field(layer: str) -> str:
    info = get_json(layer, {"f": "json"})
    if info.get("objectIdField"):
        return info["objectIdField"]
    return next(f["name"] for f in info["fields"] if f["type"] == "esriFieldTypeOID")


def pages(layer: str, where: str, fields: str):
    oid = oid_field(layer)
    last = -1
    n = 0
    while True:
        data = get_json(
            f"{layer}/query",
            {
                "where": f"({where}) AND {oid} > {last}",
                "outFields": f"{oid},{fields}",
                "orderByFields": f"{oid} ASC",
                "resultRecordCount": str(PAGE),
                "returnGeometry": "true",
                "outSR": "4326",
                "maxAllowableOffset": SIMPLIFY_DEG,
                "geometryPrecision": "5",
                "f": "json",
            },
        )
        feats = data.get("features") or []
        if not feats:
            return
        n += len(feats)
        last = max(f["attributes"][oid] for f in feats)
        if (n // PAGE) % 20 == 0:
            print(f"  {layer.rsplit('/', 3)[-3]}: {n:,} records", flush=True)
        yield feats
        time.sleep(PAUSE)


def build(db_path: Path) -> dict:
    db_path.unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(pack.SCHEMA)
    counts = {"padus": 0, "sma": 0, "grid": 0, "skipped_no_geometry": 0}
    t0 = time.time()

    print("PAD-US 4.1 (Manager Name)", flush=True)
    for feats in pages(
        PADUS_LAYER, "1=1",
        "FeatClass,Unit_Nm,Pub_Access,Mang_Type,Mang_Name,Des_Tp,GIS_Acres,State_Nm",
    ):
        for f in feats:
            rings = (f.get("geometry") or {}).get("rings")
            if not rings:
                counts["skipped_no_geometry"] += 1
                continue
            a = f["attributes"]
            blob, bbox = pack.encode(rings)
            cur = conn.execute(
                "INSERT INTO padus (feat_class, unit_name, pub_access, mang_type, mang_name,"
                " des_tp, acres, state, minx, miny, maxx, maxy, geom)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (a.get("FeatClass"), a.get("Unit_Nm"), a.get("Pub_Access"), a.get("Mang_Type"),
                 a.get("Mang_Name"), a.get("Des_Tp"), a.get("GIS_Acres"), a.get("State_Nm"),
                 *bbox, blob),
            )
            cells = [(c, pack.LAYER_PADUS, cur.lastrowid) for c in pack.cells_for_bbox(*bbox)]
            conn.executemany("INSERT OR IGNORE INTO grid VALUES (?,?,?)", cells)
            counts["padus"] += 1
            counts["grid"] += len(cells)
        conn.commit()

    print("BLM Surface Management (non-private)", flush=True)
    for feats in pages(
        SMA_LAYER, "ADMIN_AGENCY_CODE NOT IN ('PVT','UND')", "ADMIN_AGENCY_CODE,ADMIN_ST"
    ):
        for f in feats:
            rings = (f.get("geometry") or {}).get("rings")
            if not rings:
                counts["skipped_no_geometry"] += 1
                continue
            a = f["attributes"]
            blob, bbox = pack.encode(rings)
            cur = conn.execute(
                "INSERT INTO sma (agency, state, minx, miny, maxx, maxy, geom) VALUES (?,?,?,?,?,?,?)",
                (a.get("ADMIN_AGENCY_CODE"), a.get("ADMIN_ST"), *bbox, blob),
            )
            cells = [(c, pack.LAYER_SMA, cur.lastrowid) for c in pack.cells_for_bbox(*bbox)]
            conn.executemany("INSERT OR IGNORE INTO grid VALUES (?,?,?)", cells)
            counts["sma"] += 1
            counts["grid"] += len(cells)
        conn.commit()

    meta = {
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "padus_source": PADUS_LAYER,
        "sma_source": SMA_LAYER,
        "simplify_deg": SIMPLIFY_DEG,
        "counts": json.dumps(counts),
    }
    conn.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", meta.items())
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    counts["build_minutes"] = round((time.time() - t0) / 60, 1)
    return counts


def extract_state(national: Path, state: str, out: Path) -> None:
    out.unlink(missing_ok=True)
    conn = sqlite3.connect(out)
    conn.executescript(pack.SCHEMA)
    conn.execute("ATTACH DATABASE ? AS n", (str(national),))
    conn.execute("INSERT INTO padus SELECT * FROM n.padus WHERE state = ?", (state,))
    conn.execute("INSERT INTO sma SELECT * FROM n.sma WHERE state = ?", (state,))
    conn.execute(
        "INSERT INTO grid SELECT g.* FROM n.grid g WHERE"
        " (g.layer = 1 AND g.fid IN (SELECT fid FROM padus))"
        " OR (g.layer = 2 AND g.fid IN (SELECT fid FROM sma))"
    )
    conn.commit()
    conn.execute("DETACH DATABASE n")
    conn.execute("VACUUM")
    conn.close()


def sizes(path: Path) -> dict:
    raw = path.read_bytes()
    gz = len(gzip.compress(raw, compresslevel=6))
    xz_path = path.with_suffix(path.suffix + ".xz")
    with lzma.open(xz_path, "wb", preset=6) as f:
        f.write(raw)
    return {"raw_mb": round(len(raw) / 1e6, 1), "gzip_mb": round(gz / 1e6, 1),
            "xz_mb": round(xz_path.stat().st_size / 1e6, 1)}


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "pack-out")
    out.mkdir(parents=True, exist_ok=True)
    national = out / "public_lands_us.sqlite"
    counts = build(national)

    report = {"counts": counts, "national": sizes(national), "states": {}}
    for st in SAMPLE_STATES:
        p = out / f"public_lands_{st}.sqlite"
        extract_state(national, st, p)
        report["states"][st] = sizes(p)

    # Table sizes inside the national file (approximate, via dbstat if available).
    try:
        conn = sqlite3.connect(national)
        report["tables_mb"] = {
            name: round(size / 1e6, 1)
            for name, size in conn.execute(
                "SELECT name, SUM(pgsize) FROM dbstat GROUP BY name ORDER BY 2 DESC"
            )
        }
        conn.close()
    except sqlite3.Error:
        pass

    (out / "sizes.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

    lines = [
        "## Offline pack sizes",
        f"Records: PAD-US {counts['padus']:,}, BLM non-private {counts['sma']:,}, "
        f"grid rows {counts['grid']:,}; built in {counts['build_minutes']} min.",
        "",
        "| Pack | Raw MB | gzip MB | xz MB |",
        "|---|---|---|---|",
        f"| **National** | {report['national']['raw_mb']} | {report['national']['gzip_mb']} | {report['national']['xz_mb']} |",
    ]
    for st, s in report["states"].items():
        lines.append(f"| {st} | {s['raw_mb']} | {s['gzip_mb']} | {s['xz_mb']} |")
    if "tables_mb" in report:
        lines += ["", "Table sizes (MB): " + ", ".join(f"{k} {v}" for k, v in report["tables_mb"].items())]
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    # Keep the national file for the accuracy check; state extracts only as .xz.
    for p in out.glob("*.sqlite"):
        if p != national:
            p.unlink()


if __name__ == "__main__":
    main()
