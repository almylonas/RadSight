"""NASA DONKI (Space Weather Database Of Notifications, Knowledge, Information).

Free API key from https://api.nasa.gov (DEMO_KEY works with low rate limits).
"""
from __future__ import annotations

from datetime import date, timedelta

from radsight import config
from radsight.sources.http import fetch_json


def _url(kind: str, days: int) -> str:
    end = date.today()
    start = end - timedelta(days=days)
    return (f"{config.DONKI_BASE}/{kind}?startDate={start}&endDate={end}"
            f"&api_key={config.NASA_API_KEY}")


def flares_raw(days: int = 30) -> list[dict]:
    return fetch_json(_url("FLR", days), ttl=3600) or []


def flares(days: int = 30) -> list[dict]:
    return parse_flares(flares_raw(days))


def sep_events(days: int = 30) -> list[dict]:
    data = fetch_json(_url("SEP", days), ttl=3600) or []
    return [{"id": r["sepID"], "time": r["eventTime"]} for r in data]


def parse_flares(records: list[dict]) -> list[dict]:
    return [{"id": r.get("flrID"), "begin": r.get("beginTime"), "peak": r.get("peakTime"),
             "class": r.get("classType"), "location": r.get("sourceLocation")}
            for r in records]
