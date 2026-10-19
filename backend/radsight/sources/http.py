"""Tiny cached JSON fetcher (standard library only)."""
from __future__ import annotations

import json
import time
import urllib.request

from radsight import config

_cache: dict[str, tuple[float, object]] = {}


def fetch_json(url: str, ttl: float = config.CACHE_TTL_S):
    now = time.time()
    hit = _cache.get(url)
    if hit and now - hit[0] < ttl:
        return hit[1]
    req = urllib.request.Request(url, headers={"User-Agent": "RadSight/1.0"})
    with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT_S) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    _cache[url] = (now, data)
    return data
