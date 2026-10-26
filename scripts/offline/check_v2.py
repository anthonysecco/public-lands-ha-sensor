"""Accuracy, coverage and speed check for offline pack v2 (Phase 0 spike).

1. Offline answers from the national pack vs the live services (random points
   and points ~30 m from boundaries), same samples as the v1 check.
2. State files vs the national pack for points inside each sample state.
3. Lookup timings for the national pack and a state file.

Usage: python check_v2.py OUTPUT_DIR RAW_DIR
"""

from __future__ import annotations

import gzip
import json
import math
import os
from pathlib import Path
import random
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
import pack2  # noqa: E402
from check_accuracy import BOXES, EDGE_OFFSET_M, EDGE_POINTS, PER_BOX, label, live_label  # noqa: E402

SAMPLE_STATES = ("CA", "NV", "AZ")


def offline_label(conn: sqlite3.Connection, lon: float, lat: float) -> tuple[str, float]:
    t = time.perf_counter()
    padus, sma = pack2.lookup(conn, lon, lat)
    return label(padus, sma), (time.perf_counter() - t) * 1000


def edge_points(raw: Path, rng: random.Random) -> list[tuple[float, float]]:
    """~30 m from a random original boundary vertex of a CA, NV or AZ area."""
    chosen: list[list] = []
    seen = 0
    with gzip.open(raw / "padus.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["a"].get("State_Nm") not in SAMPLE_STATES:
                continue
            seen += 1
            if len(chosen) < EDGE_POINTS:
                chosen.append(rec["r"])
            elif (j := rng.randrange(seen)) < EDGE_POINTS:
                chosen[j] = rec["r"]
    pts = []
    for rings in chosen:
        x, y = rng.choice(rng.choice(rings))[:2]
        ang = rng.uniform(0, 2 * math.pi)
        dlat = EDGE_OFFSET_M * math.sin(ang) / 111_320
        dlon = EDGE_OFFSET_M * math.cos(ang) / (111_320 * math.cos(math.radians(y)))
        pts.append((x + dlon, y + dlat))
    return pts


def pct(sorted_ms: list[float], q: float) -> float:
    return round(sorted_ms[min(len(sorted_ms) - 1, int(len(sorted_ms) * q))], 2)


def main() -> None:
    out, raw = Path(sys.argv[1]), Path(sys.argv[2])
    national = sqlite3.connect(out / "public_lands_us.sqlite")
    index = json.loads((out / "index.json").read_text())
    rng = random.Random(4242)

    groups = {name: [(rng.uniform(x0, x1), rng.uniform(y0, y1)) for _ in range(PER_BOX)]
              for name, (x0, y0, x1, y1) in BOXES.items()}
    groups[f"Near boundaries (~{EDGE_OFFSET_M} m)"] = edge_points(raw, rng)

    # 1. Offline (national) vs live.
    results, mismatches, nat_ms = {}, [], []
    for name, pts in groups.items():
        agree = 0
        for lon, lat in pts:
            local, ms = offline_label(national, lon, lat)
            nat_ms.append(ms)
            live = live_label(lon, lat)
            if local == live:
                agree += 1
            else:
                mismatches.append({"group": name, "lat": round(lat, 5), "lon": round(lon, 5),
                                   "live": live, "offline": local})
        results[name] = {"points": len(pts), "agree": agree, "pct": round(100 * agree / len(pts), 1)}
        print(name, results[name], flush=True)

    # 2. State files vs national, for points whose grid cell belongs to the state.
    coverage, state_ms = {}, []
    all_pts = [p for pts in groups.values() for p in pts]
    for st in SAMPLE_STATES:
        cells = set(index["states"][st]["cells"])
        conn = sqlite3.connect(out / "states" / f"public_lands_{st}.sqlite")
        # Extra random points inside the state's cells.
        extra = []
        cell_list = sorted(cells)
        for _ in range(300):
            c = rng.choice(cell_list)
            cx, cy = c // 10_000 - 1000, c % 10_000 - 1000
            extra.append(((cx + rng.random()) * pack2.CELL_DEG, (cy + rng.random()) * pack2.CELL_DEG))
        pts = [p for p in all_pts if pack2.cell_of(*p) in cells] + extra
        same = 0
        for lon, lat in pts:
            a, ms = offline_label(conn, lon, lat)
            state_ms.append(ms)
            b, _ = offline_label(national, lon, lat)
            same += a == b
        coverage[st] = {"points": len(pts), "same_as_national": same}
        print("coverage", st, coverage[st], flush=True)

    # 3. Speed: extra national timings on many random points.
    for _ in range(2000):
        x0, y0, x1, y1 = BOXES["Lower 48"]
        nat_ms.append(offline_label(national, rng.uniform(x0, x1), rng.uniform(y0, y1))[1])
    nat_ms.sort()
    state_ms.sort()
    speed = {
        "national": {"n": len(nat_ms), "median_ms": pct(nat_ms, 0.5), "p95_ms": pct(nat_ms, 0.95),
                     "max_ms": round(nat_ms[-1], 2)},
        "state": {"n": len(state_ms), "median_ms": pct(state_ms, 0.5), "p95_ms": pct(state_ms, 0.95),
                  "max_ms": round(state_ms[-1], 2)},
    }
    report = {"results": results, "coverage": coverage, "speed": speed, "mismatches": mismatches}
    (out / "accuracy.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "mismatches"}, indent=2))

    lines = ["## Offline v2 vs live", "", "| Sample | Points | Agree | % |", "|---|---|---|---|"]
    lines += [f"| {n} | {r['points']} | {r['agree']} | {r['pct']} |" for n, r in results.items()]
    lines += ["", "State files vs national: " + ", ".join(
        f"{st} {c['same_as_national']}/{c['points']}" for st, c in coverage.items())]
    lines += ["", f"Lookup speed: national {speed['national']}, state {speed['state']}", ""]
    if mismatches:
        lines += ["| Sample | Lat, Lon | Live | Offline |", "|---|---|---|---|"]
        lines += [f"| {m['group']} | {m['lat']}, {m['lon']} | {m['live']} | {m['offline']} |"
                  for m in mismatches[:40]]
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
