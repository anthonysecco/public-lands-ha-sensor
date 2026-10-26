"""Build offline pack v2: grid-cut boundaries, shared strings, state files.

Inputs: raw/padus.jsonl.gz and raw/sma.jsonl.gz from fetch.py, and the Census
cartographic boundary file for states (cb_2024_us_state_500k.zip).

Outputs (in OUTPUT_DIR):
  public_lands_us.sqlite        national pack
  states/public_lands_XX.sqlite one per state or territory (every grid cell
                                that touches the state, so the whole state is
                                covered)
  index.json                    which states each grid cell needs, and each
                                state's neighbors
  sizes.json                    size report

Build-time only dependencies: shapely, pyshp. The integration would read the
packs with the standard library only.

Usage: python build_v2.py RAW_DIR STATES_ZIP OUTPUT_DIR
"""

from __future__ import annotations

import gzip
import json
import lzma
import math
import os
from pathlib import Path
import sqlite3
import sys
import time

import numpy as np
import shapefile  # pyshp
import shapely
from shapely import STRtree
from shapely.geometry import LinearRing, MultiPolygon, Polygon, shape

sys.path.insert(0, str(Path(__file__).parent))
import pack2  # noqa: E402

CELL = pack2.CELL_DEG


# --- geometry --------------------------------------------------------------

def to_geom(rings: list[list[list[float]]]):
    """Esri rings (outer clockwise, holes counter-clockwise) to a valid geometry."""
    shells, holes = [], []
    for r in rings:
        if len(r) < 4:
            continue
        (holes if LinearRing(r).is_ccw else shells).append(r)
    if not shells:
        shells, holes = holes, []
    if not shells:
        return None
    shell_polys = [Polygon(s) for s in shells]
    hole_lists: list[list] = [[] for _ in shells]
    if holes:
        tree = STRtree(shell_polys)
        for h in holes:
            rp = Polygon(h).representative_point()
            idx = tree.query(rp, predicate="within")
            if len(idx):
                best = min(idx, key=lambda i: shell_polys[i].area)
                hole_lists[best].append(h)
    geom = MultiPolygon([Polygon(s, hl) for s, hl in zip(shells, hole_lists)])
    geom = shapely.make_valid(geom)
    return None if geom.is_empty else geom


def polygon_rings(geom) -> list:
    rings = []
    for part in shapely.get_parts(geom):
        if part.geom_type == "Polygon" and not part.is_empty:
            rings.append(list(part.exterior.coords))
            rings.extend(list(i.coords) for i in part.interiors)
        elif part.geom_type in ("MultiPolygon", "GeometryCollection"):
            rings.extend(polygon_rings(part))
    return rings


def cells_and_pieces(geom):
    """Yield (cell_id, blob or None for a full cell)."""
    minx, miny, maxx, maxy = geom.bounds
    cx0, cy0 = math.floor(minx / CELL), math.floor(miny / CELL)
    cx1, cy1 = math.floor(maxx / CELL), math.floor(maxy / CELL)
    if cx0 == cx1 and cy0 == cy1:
        rings = polygon_rings(geom)
        if rings:
            yield pack2.cell_id(cx0, cy0), pack2.encode(rings)[0]
        return
    cxs, cys = np.meshgrid(np.arange(cx0, cx1 + 1), np.arange(cy0, cy1 + 1))
    cxs, cys = cxs.ravel(), cys.ravel()
    boxes = shapely.box(cxs * CELL, cys * CELL, (cxs + 1) * CELL, (cys + 1) * CELL)
    shapely.prepare(geom)
    touch = shapely.intersects(geom, boxes)
    full = shapely.contains(geom, boxes)
    for i in np.nonzero(touch)[0]:
        cx, cy = int(cxs[i]), int(cys[i])
        if full[i]:
            yield pack2.cell_id(cx, cy), None
            continue
        piece = shapely.clip_by_rect(geom, cx * CELL, cy * CELL, (cx + 1) * CELL, (cy + 1) * CELL)
        rings = polygon_rings(piece) if not piece.is_empty else []
        if rings:
            yield pack2.cell_id(cx, cy), pack2.encode(rings)[0]


# --- building --------------------------------------------------------------

class Strings:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.ids: dict[str, int] = {}

    def __call__(self, s) -> int | None:
        if s is None or s == "":
            return None
        s = str(s)
        if s not in self.ids:
            self.ids[s] = len(self.ids) + 1
            self.conn.execute("INSERT INTO strings VALUES (?, ?)", (self.ids[s], s))
        return self.ids[s]


def read_raw(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def build_national(raw: Path, db: Path) -> dict:
    db.unlink(missing_ok=True)
    conn = sqlite3.connect(db)
    conn.executescript(pack2.SCHEMA)
    conn.execute("PRAGMA journal_mode = OFF")
    conn.execute("PRAGMA synchronous = OFF")
    s = Strings(conn)
    stats = {"padus": 0, "sma": 0, "pieces": 0, "full_cells": 0, "bad_geometry": 0}
    t0 = time.time()

    def add(fid: int, rings, row: tuple) -> None:
        try:
            geom = to_geom(rings)
        except Exception:  # noqa: BLE001  (a handful of malformed source shapes)
            geom = None
        if geom is None:
            stats["bad_geometry"] += 1
            return
        conn.execute("INSERT INTO areas VALUES (?,?,?,?,?,?,?,?,?)", (fid, *row))
        pieces = list(cells_and_pieces(geom))
        conn.executemany("INSERT OR IGNORE INTO pieces VALUES (?,?,?)", [(c, fid, b) for c, b in pieces])
        stats["pieces"] += len(pieces)
        stats["full_cells"] += sum(1 for _, b in pieces if b is None)

    for i, rec in enumerate(read_raw(raw / "padus.jsonl.gz"), start=1):
        a = rec["a"]
        add(i, rec["r"], (
            pack2.LAYER_PADUS, s(a.get("FeatClass")), s(a.get("Unit_Nm")), s(a.get("Pub_Access")),
            s(a.get("Mang_Type")), s(a.get("Mang_Name")), s(a.get("Des_Tp")), a.get("GIS_Acres"),
        ))
        stats["padus"] += 1
        if i % 50_000 == 0:
            conn.commit()
            print(f"  PAD-US {i:,} ({(time.time() - t0) / 60:.1f} min)", flush=True)

    for i, rec in enumerate(read_raw(raw / "sma.jsonl.gz"), start=1):
        a = rec["a"]
        add(pack2.SMA_FID_OFFSET + i, rec["r"], (
            pack2.LAYER_SMA, None, None, None, None, s(a.get("ADMIN_AGENCY_CODE")), None, None,
        ))
        stats["sma"] += 1
        if i % 50_000 == 0:
            conn.commit()
            print(f"  BLM {i:,} ({(time.time() - t0) / 60:.1f} min)", flush=True)

    conn.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", {
        "format": "public-lands-pack-2",
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cell_deg": str(CELL),
    }.items())
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    stats["build_minutes"] = round((time.time() - t0) / 60, 1)
    return stats


def state_cells(states_zip: Path) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    reader = shapefile.Reader(str(states_zip))
    fields = [f[0] for f in reader.fields[1:]]
    for sr in reader.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        geom = shapely.make_valid(shape(sr.shape.__geo_interface__))
        cells = sorted({c for c, _ in cells_and_pieces(geom)})
        out[rec["STUSPS"]] = cells
    return out


def build_state(national: Path, cells: list[int], out: Path) -> None:
    out.unlink(missing_ok=True)
    conn = sqlite3.connect(out)
    conn.executescript(pack2.SCHEMA)
    conn.execute("CREATE TEMP TABLE want (cell INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO want VALUES (?)", [(c,) for c in cells])
    conn.execute("ATTACH DATABASE ? AS n", (str(national),))
    conn.execute("INSERT INTO pieces SELECT p.* FROM n.pieces p JOIN want w ON p.cell = w.cell")
    conn.execute("INSERT INTO areas SELECT * FROM n.areas WHERE fid IN (SELECT DISTINCT fid FROM pieces)")
    conn.execute(
        "INSERT INTO strings SELECT * FROM n.strings WHERE id IN ("
        " SELECT feat_class FROM areas UNION SELECT unit FROM areas UNION SELECT access FROM areas"
        " UNION SELECT mtype FROM areas UNION SELECT mname FROM areas UNION SELECT des FROM areas)"
    )
    conn.execute("INSERT INTO meta SELECT * FROM n.meta")
    conn.commit()
    conn.execute("DETACH DATABASE n")
    conn.execute("VACUUM")
    conn.close()


def xz_size(path: Path, keep: bool) -> int:
    xz = path.with_suffix(path.suffix + ".xz")
    with open(path, "rb") as src, lzma.open(xz, "wb", preset=6) as dst:
        while chunk := src.read(1 << 20):
            dst.write(chunk)
    size = xz.stat().st_size
    if not keep:
        xz.unlink()
    return size


def main() -> None:
    raw, states_zip, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    national = out / "public_lands_us.sqlite"
    stats = build_national(raw, national)
    print(json.dumps(stats), flush=True)

    report: dict = {"stats": stats}
    report["national"] = {"raw_mb": round(national.stat().st_size / 1e6, 1),
                          "xz_mb": round(xz_size(national, keep=True) / 1e6, 1)}
    conn = sqlite3.connect(national)
    try:
        report["tables_mb"] = {n: round(sz / 1e6, 1) for n, sz in conn.execute(
            "SELECT name, SUM(pgsize) FROM dbstat GROUP BY name ORDER BY 2 DESC")}
    except sqlite3.Error:
        pass
    conn.close()

    print("States", flush=True)
    cells_by_state = state_cells(states_zip)
    (out / "states").mkdir(exist_ok=True)
    state_sizes = {}
    keep = {"CA", "NV", "AZ", "OR", "MD"}
    for st, cells in sorted(cells_by_state.items()):
        p = out / "states" / f"public_lands_{st}.sqlite"
        build_state(national, cells, p)
        state_sizes[st] = {"cells": len(cells), "raw_mb": round(p.stat().st_size / 1e6, 2),
                           "xz_mb": round(xz_size(p, keep=st in keep) / 1e6, 2)}
        if st not in {"CA", "NV", "AZ"}:
            p.unlink()  # keep only the sample states unpacked, for the accuracy check
    report["states"] = state_sizes
    xs = sorted(v["xz_mb"] for v in state_sizes.values())
    report["state_xz_summary"] = {"count": len(xs), "min": xs[0], "median": xs[len(xs) // 2],
                                  "max": xs[-1], "sum": round(sum(xs), 1)}

    # Index: cells per state, and neighbors (states sharing a grid cell).
    cell_states: dict[int, set[str]] = {}
    for st, cells in cells_by_state.items():
        for c in cells:
            cell_states.setdefault(c, set()).add(st)
    neighbors = {st: set() for st in cells_by_state}
    for sts in cell_states.values():
        for st in sts:
            neighbors[st] |= sts - {st}
    index = {"cell_deg": CELL, "states": {
        st: {"cells": cells, "neighbors": sorted(neighbors[st])} for st, cells in cells_by_state.items()
    }}
    idx_path = out / "index.json"
    idx_path.write_text(json.dumps(index, separators=(",", ":")))
    report["index"] = {"raw_kb": round(idx_path.stat().st_size / 1e3, 1),
                       "gzip_kb": round(len(gzip.compress(idx_path.read_bytes())) / 1e3, 1)}
    report["neighbors_sample"] = {st: sorted(neighbors[st]) for st in ("CA", "NV", "AZ", "OR")}

    (out / "sizes.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "states"}, indent=2))

    lines = [
        "## Offline pack v2 sizes",
        f"PAD-US {stats['padus']:,}, BLM {stats['sma']:,}, pieces {stats['pieces']:,} "
        f"(full cells {stats['full_cells']:,}), bad geometry {stats['bad_geometry']}; "
        f"build {stats['build_minutes']} min.",
        "",
        f"**National:** {report['national']['raw_mb']} MB raw, **{report['national']['xz_mb']} MB xz**",
        "",
        f"**State files (xz):** {report['state_xz_summary']}",
        f"**Index:** {report['index']}",
        "",
        "| State | Cells | Raw MB | xz MB |", "|---|---|---|---|",
    ]
    for st, v in sorted(state_sizes.items(), key=lambda kv: -kv[1]["xz_mb"]):
        lines.append(f"| {st} | {v['cells']} | {v['raw_mb']} | {v['xz_mb']} |")
    if "tables_mb" in report:
        lines.insert(4, "Tables (MB): " + ", ".join(f"{k} {v}" for k, v in report["tables_mb"].items()))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
