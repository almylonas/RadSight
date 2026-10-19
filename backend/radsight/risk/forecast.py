"""24-hour impact forecast and 14-day outlook.

The 24 h forecast translates flare probabilities (NOAA SWPC) into mission
impact with the RadSight impact table. The table values are RadSight model
estimates, not an official product.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# (flare class, probability threshold %, SEP %, HF radio blackout %, spacecraft disruption %)
IMPACT_TABLE = [
    ("M1+", 50, 7.5, 20.0, 10.0),
    ("M5+", 30, 25.0, 40.0, 32.0),
    ("X1+", 10, 45.0, 67.0, 60.0),
    ("X5+", 2, 85.0, 92.0, 92.0),
]


@dataclass
class Forecast24:
    m_prob: float
    x_prob: float
    proton_prob: float      # NOAA probability of a >=10 MeV proton event
    sep: float
    hf_blackout: float
    disruption: float
    active_row: str | None


def _class_probability(row: str, m: float, x: float) -> float:
    """Approximate probability for the table's flare-class rows from NOAA M/X."""
    if row == "M1+":
        return m
    if row == "M5+":
        return x + 0.3 * max(m - x, 0)
    if row == "X1+":
        return x
    return 0.1 * x  # X5+: roughly one in ten X-class flares reaches X5


def forecast_24h(m_prob: float, x_prob: float, proton_prob: float) -> Forecast24:
    active = None
    sep, hf, dis = 0.0, 0.0, 0.0
    for row, thr, s, h, d in IMPACT_TABLE:
        p = _class_probability(row, m_prob, x_prob)
        if p >= thr:
            active, sep, hf, dis = row, s, h, d
    if active is None:  # below the table: scale the first row
        frac = min(m_prob / IMPACT_TABLE[0][1], 1.0)
        sep, hf, dis = (IMPACT_TABLE[0][2] * frac, IMPACT_TABLE[0][3] * frac,
                        IMPACT_TABLE[0][4] * frac)
    sep = max(sep, proton_prob)
    return Forecast24(m_prob, x_prob, proton_prob, round(sep, 1), round(hf, 1),
                      round(dis, 1), active)


def outlook_score(day: int, sep_prob_now: float, f107: float, ap: float) -> float:
    """Daily risk score for the 14-day outlook (0 = low, 1 = high).

    Short-range flare risk fades with lead time; beyond that the outlook
    follows solar activity (F10.7) and geomagnetic activity (Ap) from the
    NOAA 45-day forecast.
    """
    short = 0.6 * (sep_prob_now / 100.0) * math.exp(-day / 3.0)
    activity = 0.0016 * max(f107 - 70.0, 0.0)
    geo = 0.004 * ap
    return round(min(max(short + activity + geo, 0.0), 1.0), 3)
