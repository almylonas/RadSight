"""NOAA SWPC feeds (GOES particles, X-rays, flares, forecasts).

All endpoints are public JSON, refreshed every ~5 minutes, no key needed.
"""
from __future__ import annotations

from datetime import datetime, timezone

from radsight import config
from radsight.sources.http import fetch_json


def parse_time(s: str) -> datetime:
    s = s.replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"unknown time format: {s}")


def channel(records: list[dict], energy: str) -> list[tuple[datetime, float]]:
    """Pick one energy channel out of a GOES particle / X-ray file."""
    out = []
    for r in records:
        if r.get("energy") == energy and r.get("flux") is not None:
            out.append((parse_time(r["time_tag"]), float(r["flux"])))
    out.sort()
    return out


def latest_probabilities(records: list[dict]) -> dict:
    rec = max(records, key=lambda r: r["date"])
    return {
        "date": rec["date"],
        "m": float(rec["m_class_1_day"]),
        "x": float(rec["x_class_1_day"]),
        "proton": float(rec["10mev_protons_1_day"]),
    }


def forecast45(doc: dict, days: int = 14) -> dict:
    f107, ap, dates = {}, {}, []
    for r in doc["data"]:
        d = r["time"][:10]
        if r["metric"] == "f107":
            f107[d] = float(r["value"])
        elif r["metric"] == "ap":
            ap[d] = float(r["value"])
    dates = sorted(set(f107) & set(ap))[:days]
    return {"start": dates[0], "f107": [f107[d] for d in dates], "ap": [ap[d] for d in dates]}


def flares(records: list[dict]) -> list[dict]:
    out = []
    for r in records:
        if not r.get("max_class") or not r.get("max_time"):
            continue
        out.append({"begin": r["begin_time"][:16] + "Z", "peak": r["max_time"][:16] + "Z",
                    "class": r["max_class"]})
    return out


def fetch_all() -> dict:
    """Fetch every NOAA feed RadSight uses. Raises on network failure."""
    return {name: fetch_json(url) for name, url in config.NOAA.items()}
