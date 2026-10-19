"""Replay scenario modelled on the 10 September 2017 solar particle event.

Real anchors: an X8.2 flare from active region 12673 at the Sun's west limb
began around 15:35 UTC and peaked at 16:06 UTC on 10 Sep 2017. The >=10 MeV
protons reached NOAA S3 the next day and >100 MeV protons produced Ground
Level Enhancement 72.

The curves below are a smooth model with that timing and those magnitudes,
not the archived GOES measurements. Swap `replay_environment` for the NCEI
GOES archive to replay any historical event exactly.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from radsight.sim.crew import EvaWindow

UTC = timezone.utc
T0 = datetime(2017, 9, 9, 12, 0, tzinfo=UTC)
T_END = datetime(2017, 9, 12, 12, 0, tzinfo=UTC)
STEP_MIN = 10
MISSION_START = datetime(2017, 9, 5, 0, 0, tzinfo=UTC)

FLARE_START = datetime(2017, 9, 10, 15, 35, tzinfo=UTC)
FLARE_PEAK = datetime(2017, 9, 10, 16, 6, tzinfo=UTC)
ELECTRON_ONSET = datetime(2017, 9, 10, 16, 10, tzinfo=UTC)
P100_ONSET = datetime(2017, 9, 10, 16, 30, tzinfo=UTC)
P10_ONSET = datetime(2017, 9, 10, 16, 35, tzinfo=UTC)
ESP_PEAK = datetime(2017, 9, 11, 11, 45, tzinfo=UTC)


def _minutes(times: list[datetime], ref: datetime) -> np.ndarray:
    return np.array([(t - ref).total_seconds() / 60.0 for t in times])


def _rise_decay(m: np.ndarray, rise: float, decay: float) -> np.ndarray:
    x = np.clip(m, 0, None)
    y = (1 - np.exp(-x / rise)) ** 2 * np.exp(-x / decay)
    y[m < 0] = 0
    return y / y.max() if y.max() > 0 else y


def replay_environment(seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    n = int((T_END - T0).total_seconds() / 60 / STEP_MIN) + 1
    times = [T0 + timedelta(minutes=STEP_MIN * i) for i in range(n)]

    def noise(scale: float = 0.04) -> np.ndarray:
        return np.exp(rng.normal(0, scale, n))

    # X-rays (W/m^2, 0.1-0.8 nm): elevated C-class background + X8.2
    mf = _minutes(times, FLARE_START)
    mp = _minutes(times, FLARE_PEAK)
    xray = np.full(n, 2.2e-6)
    rise = (mf >= 0) & (mp < 0)
    xray[rise] += 8.2e-4 * (mf[rise] / 31.0) ** 2
    dec = mp >= 0
    xray[dec] += 8.2e-4 * (0.82 * np.exp(-mp[dec] / 35.0) + 0.18 * np.exp(-mp[dec] / 240.0))
    for hh, peak in [(-25.0, 3.1e-6), (-14.5, 1.2e-5), (-6.0, 4.0e-6), (30.5, 6.0e-6), (40.0, 2.8e-6)]:
        mm = _minutes(times, FLARE_PEAK) - hh * 60
        xray += peak * np.exp(-np.abs(mm) / 18.0)
    xray *= noise(0.03)

    # Relativistic electrons (proxy channel, pfu)
    me = _minutes(times, ELECTRON_ONSET)
    electrons = 1.0 + 950.0 * _rise_decay(me, 12.0, 320.0)
    electrons *= noise(0.05)

    # >=100 MeV protons (pfu)
    j100 = 0.25 + 68.0 * _rise_decay(_minutes(times, P100_ONSET), 55.0, 720.0)
    j100 *= noise(0.03)

    # >=10 MeV protons (pfu): prompt component + shock-accelerated (ESP) peak
    prompt = 380.0 * _rise_decay(_minutes(times, P10_ONSET), 110.0, 1100.0)
    ms = _minutes(times, ESP_PEAK)
    esp = np.where(ms < 0, np.exp(-(ms / 300.0) ** 2), np.exp(-ms / 600.0))
    esp[_minutes(times, P10_ONSET) < 0] = 0
    j10 = 0.4 + prompt + 1080.0 * esp
    j10 *= noise(0.03)

    # NOAA-style flare probabilities per frame (%): AR 12673 was already
    # flaring (X9.3 on 6 Sep), so the pre-event forecast is elevated.
    after = np.array([t >= FLARE_PEAK for t in times])
    m_prob = np.where(after, 75.0, 45.0)
    x_prob = np.where(after, 35.0, 10.0)
    proton_prob = np.where(after, 95.0, 15.0)

    flares = [
        {"begin": "2017-09-09T22:04Z", "peak": "2017-09-09T22:16Z", "class": "M1.1"},
        {"begin": "2017-09-10T15:35Z", "peak": "2017-09-10T16:06Z", "class": "X8.2"},
    ]

    eva_windows = [
        EvaWindow(("tanaka", "lindqvist"), datetime(2017, 9, 10, 14, 30, tzinfo=UTC),
                  datetime(2017, 9, 10, 21, 30, tzinfo=UTC), "Surface EVA 3"),
        EvaWindow(("okafor",), datetime(2017, 9, 11, 14, 0, tzinfo=UTC),
                  datetime(2017, 9, 11, 17, 0, tzinfo=UTC), "Antenna repair EVA"),
    ]

    outlook = {
        "f107": [182, 180, 178, 175, 170, 160, 150, 140, 132, 125, 120, 118, 115, 112],
        "ap": [30, 45, 60, 35, 20, 15, 12, 10, 8, 8, 10, 12, 10, 8],
        "start": "2017-09-10",
    }

    return {
        "times": times,
        "j10": j10, "j100": j100, "electrons": electrons, "xray": xray,
        "m_prob": m_prob, "x_prob": x_prob, "proton_prob": proton_prob,
        "flares": flares, "eva_windows": eva_windows, "outlook": outlook,
        "mission_start": MISSION_START,
        "electron_label": "Relativistic electrons (model, REleASE-type channel)",
    }
