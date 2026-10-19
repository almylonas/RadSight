"""List the ESA SWE HAPI datasets your account can read, and save the details.

    export ESA_SWE_CLIENT_ID=...  ESA_SWE_CLIENT_SECRET=...
    python scripts/esa_catalog.py              # list everything
    python scripts/esa_catalog.py ngrm proton  # only IDs containing these words

Writes esa_catalog.json (catalog + /info of the matching datasets).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from radsight.sources import esa_hapi  # noqa: E402


def main() -> None:
    if not esa_hapi.configured():
        sys.exit("Set ESA_SWE_CLIENT_ID and ESA_SWE_CLIENT_SECRET first.")
    words = [w.lower() for w in sys.argv[1:]]
    cat = esa_hapi.catalog()
    hits = [d for d in cat if all(w in (d["id"] + d.get("title", "")).lower() for w in words)]
    print(f"{len(cat)} datasets available, {len(hits)} match\n")
    details = []
    for d in hits:
        print(f"- {d['id']}\n    {d.get('title', '')}")
        if words:
            try:
                inf = esa_hapi.info(d["id"])
                params = [p["name"] + (f" [{p.get('units')}]" if p.get("units") else "") for p in inf["parameters"]]
                print(f"    {inf.get('startDate')} → {inf.get('stopDate')} · cadence {inf.get('cadence')}")
                print("    parameters: " + ", ".join(params[:12]) + (" …" if len(params) > 12 else ""))
                details.append({"id": d["id"], "info": inf})
            except Exception as exc:
                print(f"    (info failed: {exc})")
    out = Path("esa_catalog.json")
    out.write_text(json.dumps({"catalog": cat, "details": details}, indent=1))
    print(f"\nSaved {out.resolve()}")


if __name__ == "__main__":
    main()
