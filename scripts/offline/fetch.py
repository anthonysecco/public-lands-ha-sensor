"""Download raw boundaries from the official services (Phase 0 spike v2).

Writes gzipped JSON lines ({"a": attributes, "r": rings}) so later build
steps can run without downloading again. Uses the same gentle, adaptive
paging as build_pack.py.

Usage: python fetch.py RAW_DIR
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from build_pack import PADUS_LAYER, SMA_LAYER, pages  # noqa: E402


def fetch(path: Path, layer: str, where: str, fields: str, start: int) -> int:
    n = 0
    with gzip.open(path, "wt", encoding="utf-8") as out:
        for feats in pages(layer, where, fields, start_size=start):
            for f in feats:
                rings = (f.get("geometry") or {}).get("rings")
                if rings:
                    out.write(json.dumps({"a": f["attributes"], "r": rings}, separators=(",", ":")) + "\n")
                    n += 1
    return n


def main() -> None:
    raw = Path(sys.argv[1] if len(sys.argv) > 1 else "raw")
    raw.mkdir(parents=True, exist_ok=True)
    n1 = fetch(
        raw / "padus.jsonl.gz", PADUS_LAYER, "1=1",
        "FeatClass,Unit_Nm,Pub_Access,Mang_Type,Mang_Name,Des_Tp,GIS_Acres,State_Nm", 2000,
    )
    n2 = fetch(
        raw / "sma.jsonl.gz", SMA_LAYER, "ADMIN_AGENCY_CODE NOT IN ('PVT','UND')",
        "ADMIN_AGENCY_CODE,ADMIN_ST", 50,
    )
    print(f"PAD-US {n1:,} records, BLM {n2:,} records")


if __name__ == "__main__":
    main()
