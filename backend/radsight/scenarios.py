"""Build the two dashboard scenarios: live data and the storm replay."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from radsight import config
from radsight.engine import build_timeline
from radsight.sim import storm
from radsight.sim.crew import EvaWindow
from radsight.sources import donki, noaa

LIVE_STEP_MIN = 10
LIVE_WINDOW_H = 24


def _resample(series: list[tuple[datetime, float]], grid: list[datetime], log: bool = True) -> np.ndarray:
    """Interpolate a time series onto the grid (log-linear), holding the ends."""
    if not series:
        return np.zeros(len(grid))
    ts = np.array([t.timestamp() for t, _ in series])
    vs = np.array([max(v, 1e-12) for _, v in series])
    g = np.array([t.timestamp() for t in grid])
    if log:
        return np.exp(np.interp(g, ts, np.log(vs)))
    return np.interp(g, ts, vs)


def sources_table(mode: str, raw_times: dict | None = None) -> list[dict]:
    rt = raw_times or {}
    live = mode == "live"
    snap = mode == "snapshot"

    def st(key: str) -> str:
        if live:
            return "live"
        if snap:
            return "snapshot"
        return "model"

    return [
        {"name": "GOES integral protons (>=10, >=100 MeV)", "provider": "NOAA SWPC",
         "url": config.NOAA["protons"], "cadence": "5 min", "status": st("protons"),
         "last": rt.get("protons"), "used_for": "Current SEP level, crew dose rate"},
        {"name": "GOES integral electrons (>=2 MeV)", "provider": "NOAA SWPC",
         "url": config.NOAA["electrons"], "cadence": "5 min", "status": st("electrons"),
         "last": rt.get("electrons"), "used_for": "Imminent-event detector input (proxy)"},
        {"name": "GOES X-ray flux (0.1-0.8 nm)", "provider": "NOAA SWPC",
         "url": config.NOAA["xrays"], "cadence": "1 min", "status": st("xrays"),
         "last": rt.get("xrays"), "used_for": "Flare detection and class"},
        {"name": "Flare list, last 7 days", "provider": "NOAA SWPC",
         "url": config.NOAA["flares"], "cadence": "event", "status": st("flares"),
         "last": rt.get("flares"), "used_for": "Event log"},
        {"name": "Solar flare and proton probabilities", "provider": "NOAA SWPC",
         "url": config.NOAA["probabilities"], "cadence": "daily", "status": st("probabilities"),
         "last": rt.get("probabilities"), "used_for": "24 h forecast"},
        {"name": "45-day F10.7 and Ap forecast", "provider": "NOAA SWPC",
         "url": config.NOAA["forecast45"], "cadence": "daily", "status": st("forecast45"),
         "last": rt.get("forecast45"), "used_for": "14-day outlook"},
        {"name": "DONKI flare catalogue", "provider": "NASA CCMC",
         "url": f"{config.DONKI_BASE}/FLR", "cadence": "event", "status": st("donki"),
         "last": rt.get("donki"), "used_for": "Flare history with source region"},
        {"name": "HESPERIA REleASE", "provider": "National Observatory of Athens / ESA SWE",
         "url": config.HESPERIA_RELEASE_URL, "cadence": "1 min", "status": "planned",
         "last": None, "used_for": "Imminent proton forecast (needs ESA SWE account)"},
        {"name": "EDRS-C / NGRM electron fluxes", "provider": "ESA SWE",
         "url": "https://swe.ssa.esa.int/en/sparc-geo-ngrm-r170-federated", "cadence": "5 min",
         "status": "planned", "last": None, "used_for": "Electron environment (needs ESA SWE account)"},
        {"name": "COMESEP alerts", "provider": "BIRA-IASB / ESA SWE",
         "url": "https://swe.ssa.esa.int/en/bira-comesep-federated", "cadence": "event",
         "status": "planned", "last": None, "used_for": "SEP and storm alerts (needs ESA SWE account)"},
        {"name": "Solar magnetic activity forecasting", "provider": "IRF Sweden / ESA SWE",
         "url": "https://swe.ssa.esa.int/en/irfu-federated", "cadence": "daily",
         "status": "planned", "last": None, "used_for": "Flare probabilities (needs ESA SWE account)"},
        {"name": "Crew dosimeters and schedule", "provider": "RadSight simulator",
         "url": None, "cadence": "1 min", "status": "simulated", "last": None,
         "used_for": "Personal dose (fictional crew)"},
    ]


def replay_timeline() -> dict:
    env = storm.replay_environment()
    notes = [
        "Replay of a storm modelled on the 10 September 2017 solar particle event "
        "(X8.2 flare, NOAA S3 protons). Curves are a smooth model with the real timing, "
        "not the archived GOES record.",
        "Crew, mission and dosimeter readings are simulated.",
    ]
    return build_timeline(env, mode="replay", title="Replay: 10 Sep 2017 storm",
                          notes=notes, sources=sources_table("replay"))


def live_timeline(raw: dict, *, mode: str = "live", donki_raw: list | None = None) -> dict:
    """Build the dashboard from NOAA feeds (fetched now, or from a snapshot file)."""
    p10 = noaa.channel(raw["protons"], ">=10 MeV")
    p100 = noaa.channel(raw["protons"], ">=100 MeV")
    el = noaa.channel(raw["electrons"], ">=2 MeV")
    xr = noaa.channel(raw["xrays"], "0.1-0.8nm")

    end = max(s[-1][0] for s in (p10, el, xr) if s)
    end = end.replace(minute=(end.minute // LIVE_STEP_MIN) * LIVE_STEP_MIN, second=0)
    n = LIVE_WINDOW_H * 60 // LIVE_STEP_MIN + 1
    grid = [end - timedelta(minutes=LIVE_STEP_MIN * (n - 1 - i)) for i in range(n)]

    probs = noaa.latest_probabilities(raw["probabilities"])
    ol = noaa.forecast45(raw["forecast45"])
    mission_start = (end - timedelta(days=6)).replace(hour=0, minute=0)
    eva = []
    for d in range(2):
        day = (end - timedelta(days=1 - d)).replace(hour=0, minute=0)
        eva.append(EvaWindow(("tanaka", "lindqvist"), day + timedelta(hours=13),
                             day + timedelta(hours=19), f"Surface EVA {5 + d}"))

    proton_note = None
    if p10 and (end - p10[-1][0]) > timedelta(hours=2):
        proton_note = (f"Latest proton reading in this data set is from "
                       f"{p10[-1][0]:%Y-%m-%d %H:%M} UTC; it is held constant.")

    env = {
        "times": grid,
        "j10": _resample(p10, grid), "j100": _resample(p100, grid),
        "electrons": _resample(el, grid), "xray": _resample(xr, grid),
        "m_prob": np.full(n, probs["m"]), "x_prob": np.full(n, probs["x"]),
        "proton_prob": np.full(n, probs["proton"]),
        "flares": noaa.flares(raw["flares"]),
        "donki_flares": donki.parse_flares(donki_raw or [])[-12:],
        "eva_windows": eva,
        "outlook": ol,
        "mission_start": mission_start,
        "electron_label": "GOES >=2 MeV electrons (proxy channel)",
        "proton_note": proton_note,
    }
    raw_times = {
        "protons": p10[-1][0].strftime("%Y-%m-%dT%H:%MZ") if p10 else None,
        "electrons": el[-1][0].strftime("%Y-%m-%dT%H:%MZ") if el else None,
        "xrays": xr[-1][0].strftime("%Y-%m-%dT%H:%MZ") if xr else None,
        "flares": env["flares"][-1]["peak"] if env["flares"] else None,
        "probabilities": probs["date"],
        "forecast45": raw["forecast45"].get("issued", ol["start"]),
        "donki": env["donki_flares"][-1]["peak"] if env["donki_flares"] else None,
    }
    notes = [
        "Space-weather values are real NOAA SWPC / NASA DONKI data.",
        "GOES electrons at geostationary orbit stand in for the REleASE electron "
        "channel until ESA SWE access is configured.",
        "Crew, mission and dosimeter readings are simulated.",
    ]
    if mode == "snapshot":
        notes.insert(0, f"Snapshot of real data captured {end:%Y-%m-%d %H:%M} UTC. "
                        "Run the Python backend for continuously updated data.")
    if proton_note:
        notes.append(proton_note)
    title = "Live data" if mode == "live" else "Data snapshot"
    return build_timeline(env, mode=mode, title=title, notes=notes,
                          sources=sources_table(mode, raw_times))
