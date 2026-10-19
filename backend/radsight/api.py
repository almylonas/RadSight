"""RadSight HTTP API (FastAPI).

Run:  uvicorn radsight.api:app --reload --port 8000

  GET /api/health    liveness
  GET /api/live      dashboard timeline from live NOAA + DONKI data (cached 5 min)
  GET /api/replay    dashboard timeline for the 10 Sep 2017 storm replay
"""
from __future__ import annotations

import asyncio
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from radsight import config
from radsight.scenarios import live_timeline, replay_timeline
from radsight.sources import donki, noaa

app = FastAPI(title="RadSight API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

_live_cache: dict = {"t": 0.0, "data": None}
_replay_cache: dict = {"data": None}


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


def _build_live() -> dict:
    raw = noaa.fetch_all()
    try:
        flr = donki.flares_raw()
    except Exception:  # DONKI is optional; DEMO_KEY is rate limited
        flr = []
    return live_timeline(raw, mode="live", donki_raw=flr)


@app.get("/api/live")
async def live() -> dict:
    if _live_cache["data"] and time.time() - _live_cache["t"] < config.CACHE_TTL_S:
        return _live_cache["data"]
    try:
        data = await asyncio.to_thread(_build_live)
    except Exception as exc:  # network or format problem upstream
        if _live_cache["data"]:
            return _live_cache["data"]
        raise HTTPException(status_code=502, detail=f"Upstream data unavailable: {exc}") from exc
    _live_cache.update(t=time.time(), data=data)
    return data


@app.get("/api/replay")
def replay() -> dict:
    if _replay_cache["data"] is None:
        _replay_cache["data"] = replay_timeline()
    return _replay_cache["data"]
