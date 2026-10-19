"""Write the dashboard data the frontend falls back to when no backend runs.

    python scripts/export_snapshot.py            # try live NOAA data, else bundled snapshot
    python scripts/export_snapshot.py --offline  # bundled snapshot only

Output: ../frontend/src/data/snapshot.json and replay.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from radsight.scenarios import live_timeline, replay_timeline  # noqa: E402
from radsight.sources import donki, noaa  # noqa: E402

OUT = ROOT.parent / "frontend" / "src" / "data"
BUNDLED = ROOT / "data" / "snapshot_2026-10-19.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    live = None
    if not args.offline:
        try:
            raw = noaa.fetch_all()
            try:
                flr = donki.flares_raw()
            except Exception:
                flr = []
            live = live_timeline(raw, mode="snapshot", donki_raw=flr)
            print("snapshot: live NOAA data")
        except Exception as exc:
            print(f"live fetch failed ({exc}); using bundled snapshot")
    if live is None:
        b = json.loads(BUNDLED.read_text())
        live = live_timeline(b["noaa"], mode="snapshot", donki_raw=b["donki_flr"])
        print(f"snapshot: bundled data from {b['captured']}")

    (OUT / "snapshot.json").write_text(json.dumps(live, separators=(",", ":")))
    (OUT / "replay.json").write_text(json.dumps(replay_timeline(), separators=(",", ":")))
    print(f"wrote {OUT}/snapshot.json and replay.json")


if __name__ == "__main__":
    main()
