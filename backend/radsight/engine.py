"""RadSight engine: environment in, dashboard timeline out.

`build_timeline` walks through the environment one time step at a time and,
using only information available at that moment, computes:

  * the imminent-event detector state (REleASE-type)
  * the 24 h impact forecast
  * the risk score, its driver and the crew status (with hysteresis)
  * every astronaut's location, dose rate and cumulative dose, for the
    RadSight response policy and for a conventional no-warning policy
  * an event log

The result is a columnar JSON-ready dict: the React frontend only renders it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from radsight import config
from radsight.physics.dose import SHIELDING, dose_rate
from radsight.physics.transport import warning_window_min
from radsight.risk.forecast import IMPACT_TABLE, forecast_24h, outlook_score
from radsight.risk.release import run_detector
from radsight.risk.score import (StatusTracker, components, score_and_driver,
                                 trigger_text)
from radsight.sim.crew import (CONVENTIONAL, CREW, NOMINAL, RADSIGHT, CrewState,
                               step_crew)
from radsight.sim.trajectory import LANDING_SITE, geometry

S_SCALE = [(10, "S1"), (100, "S2"), (1000, "S3"), (10000, "S4")]


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def _r(a, nd=3):
    return [round(float(v), nd) for v in a]


def _sig(a, digits=4):
    return [float(f"{float(v):.{digits}g}") for v in a]


def build_timeline(env: dict, *, mode: str, title: str, notes: list[str],
                   sources: list[dict], pre_mission_days: float | None = None) -> dict:
    times: list[datetime] = env["times"]
    n = len(times)
    step_min = (times[1] - times[0]).total_seconds() / 60 if n > 1 else 10.0
    j10, j100 = np.asarray(env["j10"], float), np.asarray(env["j100"], float)
    electrons = np.asarray(env["electrons"], float)
    mission_start: datetime = env["mission_start"]
    windows = env.get("eva_windows", [])

    release = run_detector(times, electrons)
    tracker = StatusTracker()

    out_status, out_score, out_driver, out_trigger = [], [], [], []
    comp = {k: [] for k in ("flux", "imminent", "forecast", "dose")}
    fc = {k: [] for k in ("sep", "hf", "disruption", "m", "x", "proton", "row")}
    rel = {k: [] for k in ("level", "eta", "peak", "ratio")}
    geo = []
    loc_rates = {k: [] for k in SHIELDING}
    events: list[dict] = []

    # crew bookkeeping for both policies
    pre_days = pre_mission_days if pre_mission_days is not None else \
        max((times[0] - mission_start).total_seconds() / 86400, 0)
    crew_out = {}
    states = {}
    for c in CREW:
        base_rate = dose_rate(0, 0, NOMINAL[c.base])["total"]
        start_dose = base_rate * 24 * pre_days / 1000.0  # mSv before the window
        crew_out[c.id] = {"loc": [], "rate": [], "cum": [], "cum_conv": [],
                          "reading": [], "start": start_dose}
        states[c.id] = {"rs": CrewState(NOMINAL[c.base]), "cv": CrewState(NOMINAL[c.base]),
                        "cum": start_dose, "cum_conv": start_dose}
    rng = np.random.default_rng(42)

    prev_status, prev_level, prev_s = "safe", "quiet", None
    for i, t in enumerate(times):
        r = release[i]
        f = forecast_24h(float(env["m_prob"][i]), float(env["x_prob"][i]),
                         float(env["proton_prob"][i]))
        cabin_rate = dose_rate(j10[i], j100[i], "cabin")["total"]
        c = components(j10[i], r.level, f.sep, cabin_rate)
        score, driver = score_and_driver(c)
        status = tracker.update(score, step_min)
        # the trigger shown is the driver of the current status
        out_status.append(status)
        out_score.append(round(score, 3))
        out_driver.append(driver)
        out_trigger.append(trigger_text(driver, j10[i], r.level, r.eta_min, f.sep, cabin_rate, score))
        for k, v in c.as_dict().items():
            comp[k].append(v)
        fc["sep"].append(f.sep); fc["hf"].append(f.hf_blackout); fc["disruption"].append(f.disruption)
        fc["m"].append(f.m_prob); fc["x"].append(f.x_prob); fc["proton"].append(f.proton_prob)
        fc["row"].append(f.active_row)
        rel["level"].append(r.level)
        rel["eta"].append(None if r.eta_min is None else round(r.eta_min, 1))
        rel["peak"].append(None if r.predicted_peak_pfu is None else round(r.predicted_peak_pfu, 1))
        rel["ratio"].append(round(r.electron_ratio, 2))
        geo.append(geometry(t, mission_start))
        for k in SHIELDING:
            loc_rates[k].append(round(dose_rate(j10[i], j100[i], k)["total"], 1))

        # ---- events
        ts = _iso(t)
        if r.level != prev_level and r.level != "quiet":
            events.append({"t": ts, "i": i, "kind": "imminent", "level": r.level,
                           "text": f"Electron onset: imminent-event {r.level.upper()}, "
                                   f"protons expected in ~{r.eta_min:.0f} min, "
                                   f"predicted peak ~{r.predicted_peak_pfu:,.0f} pfu"})
        s_now = next((s for thr, s in reversed(S_SCALE) if j10[i] >= thr), None)
        if s_now and s_now != prev_s and (prev_s is None or
                                          [x for _, x in S_SCALE].index(s_now) >
                                          [x for _, x in S_SCALE].index(prev_s)):
            events.append({"t": ts, "i": i, "kind": "flux", "level": "caution",
                           "text": f">=10 MeV protons reach NOAA {s_now} ({j10[i]:,.0f} pfu)"})
        if status != prev_status:
            events.append({"t": ts, "i": i, "kind": "status", "level": status,
                           "text": f"Status changed to {config.STATUS_TEXT[status]['label']}"})
        prev_status, prev_level, prev_s = status, r.level, s_now or prev_s

        # ---- crew
        dt_h = step_min / 60.0 if i > 0 else 0.0
        for cm in CREW:
            st = states[cm.id]
            for msg in step_crew(cm, st["rs"], t, RADSIGHT, status, j10[i], windows):
                events.append({"t": ts, "i": i, "kind": "crew", "level": status, "text": msg})
            step_crew(cm, st["cv"], t, CONVENTIONAL, status, j10[i], windows)
            rate = dose_rate(j10[i], j100[i], st["rs"].location)["total"]
            rate_cv = dose_rate(j10[i], j100[i], st["cv"].location)["total"]
            st["cum"] += rate * dt_h / 1000.0
            st["cum_conv"] += rate_cv * dt_h / 1000.0
            o = crew_out[cm.id]
            o["loc"].append(st["rs"].location)
            o["rate"].append(round(rate, 1))
            o["cum"].append(round(st["cum"], 3))
            o["cum_conv"].append(round(st["cum_conv"], 3))
            reading = st["cum"] * (1 + cm.dosimeter_bias) + rng.normal(0, 0.002)
            o["reading"].append(round(max(reading, 0), 3))

    # flare events
    for fl in env.get("flares", []):
        try:
            pk = datetime.strptime(fl["peak"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if times[0] <= pk <= times[-1]:
            i = min(range(n), key=lambda k: abs((times[k] - pk).total_seconds()))
            lvl = "action" if fl["class"].startswith("X") else "caution" if fl["class"].startswith("M") else "safe"
            events.append({"t": _iso(pk), "i": i, "kind": "flare", "level": lvl,
                           "text": f"{fl['class']} solar flare peak"})
    events.sort(key=lambda e: (e["i"], e["t"]))

    # dose since start of each UTC day
    day_index = [0] * n
    for i in range(1, n):
        day_index[i] = day_index[i - 1] if times[i].date() == times[i - 1].date() else i

    crew = []
    for cm in CREW:
        o = crew_out[cm.id]
        cum = o["cum"]
        # the window may start mid-day: add the nominal dose since midnight
        since_midnight_h = (times[0] - times[0].replace(hour=0, minute=0)).total_seconds() / 3600
        first_day_ref = cum[0] - dose_rate(0, 0, NOMINAL[cm.base])["total"] * since_midnight_h / 1000
        today = [round(cum[i] - (cum[day_index[i]] if day_index[i] > 0 else first_day_ref), 3)
                 for i in range(n)]
        crew.append({
            "id": cm.id, "name": cm.name, "role": cm.role, "agency": cm.agency,
            "base": cm.base, "prior_career_mSv": cm.prior_career_mSv,
            "location": o["loc"], "dose_rate_uSv_h": o["rate"],
            "mission_mSv": o["cum"], "mission_conventional_mSv": o["cum_conv"],
            "today_mSv": today, "dosimeter_mSv": o["reading"],
        })

    outlook = []
    ol = env.get("outlook")
    if ol:
        start = datetime.strptime(ol["start"], "%Y-%m-%d")
        sep_now = fc["sep"][-1] if mode == "live" else fc["sep"][0]
        for d, (f107, ap) in enumerate(zip(ol["f107"], ol["ap"])):
            outlook.append({"date": (start + timedelta(days=d)).strftime("%Y-%m-%d"),
                            "score": outlook_score(d, sep_now, f107, ap),
                            "f107": f107, "ap": ap})

    return {
        "mode": mode,
        "title": title,
        "notes": notes,
        "generated_at": _iso(datetime.now(timezone.utc)),
        "step_min": step_min,
        "times": [_iso(t) for t in times],
        "env": {
            "j10": _sig(j10), "j100": _sig(j100), "electrons": _sig(electrons),
            "xray": _sig(env["xray"]), "electron_label": env.get("electron_label", "Electrons"),
            "proton_note": env.get("proton_note"),
        },
        "risk": {"score": out_score, "status": out_status, "driver": out_driver,
                 "trigger": out_trigger, "components": comp},
        "forecast24": fc,
        "release": rel,
        "outlook14": outlook,
        "crew": crew,
        "events": events,
        "flares": env.get("flares", []),
        "donki_flares": env.get("donki_flares", []),
        "geometry": geo,
        "mission": {
            "name": "LUNA-3 (simulated lunar mission)",
            "start": _iso(mission_start),
            "landing_site": LANDING_SITE,
            "eva_plan": [{"crew": list(w.crew_ids), "start": _iso(w.start),
                          "end": _iso(w.end), "label": w.label} for w in windows],
        },
        "shielding": [{"key": s.key, "label": s.label, "areal_g_cm2": s.areal_g_cm2,
                       "e_cut_MeV": s.e_cut_MeV} for s in SHIELDING.values()],
        "location_rates_uSv_h": loc_rates,
        "limits": {
            "career_mSv": config.CAREER_LIMIT_mSv,
            "bfo_30d_mGyEq": config.BFO_30D_LIMIT_mGyEq,
            "daily_budget_mSv": round(config.DAILY_BUDGET_mSv, 2),
            "caution": config.CAUTION_THRESHOLD, "action": config.ACTION_THRESHOLD,
        },
        "status_text": config.STATUS_TEXT,
        "impact_table": [{"row": r, "threshold": thr, "sep": s, "hf": h, "disruption": d}
                         for r, thr, s, h, d in IMPACT_TABLE],
        "warning_window_min": round(warning_window_min(30.0), 1),
        "sources": sources,
    }
