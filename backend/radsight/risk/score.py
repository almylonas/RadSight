"""Space Weather Risk Score and crew status.

The score is the maximum of four components, so the most urgent driver
decides the status and is reported as the trigger:

  flux      current >=10 MeV proton flux   0.3 per decade (10 pfu = 0.3, 100 pfu = 0.6)
  imminent  imminent-event detector        warning 0.45, alert 0.7
  forecast  24 h SEP probability           0.6 x probability, capped at 0.55
  dose      cabin dose rate vs budget      0.3 x (rate / budget rate)

Status: Safe < 0.3 <= Caution Needed < 0.6 <= Action Needed.
A status only steps down after DOWNGRADE_HOLD_MIN minutes below threshold.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from radsight import config


@dataclass
class RiskComponents:
    flux: float
    imminent: float
    forecast: float
    dose: float

    def as_dict(self) -> dict[str, float]:
        return {k: round(v, 3) for k, v in self.__dict__.items()}


def components(j10: float, release_level: str, sep_prob: float,
               cabin_rate_uSv_h: float) -> RiskComponents:
    flux = 0.3 * math.log10(j10) if j10 > 1 else 0.0
    imminent = {"quiet": 0.0, "warning": 0.45, "alert": 0.7}[release_level]
    forecast = min(0.6 * sep_prob / 100.0, 0.55)
    dose = 0.3 * cabin_rate_uSv_h / config.BUDGET_RATE_uSv_h
    clip = lambda v: min(max(v, 0.0), 1.0)  # noqa: E731
    return RiskComponents(clip(flux), clip(imminent), clip(forecast), clip(dose))


def score_and_driver(c: RiskComponents) -> tuple[float, str]:
    d = c.as_dict()
    driver = max(d, key=d.get)
    return d[driver], driver


def raw_status(score: float) -> str:
    if score >= config.ACTION_THRESHOLD:
        return "action"
    if score >= config.CAUTION_THRESHOLD:
        return "caution"
    return "safe"


RANK = {"safe": 0, "caution": 1, "action": 2}


class StatusTracker:
    """Applies hysteresis so the status does not flicker at a threshold."""

    def __init__(self) -> None:
        self.status = "safe"
        self.below_min = 0.0

    def update(self, score: float, step_min: float) -> str:
        target = raw_status(score)
        if RANK[target] >= RANK[self.status]:
            self.status, self.below_min = target, 0.0
        else:
            self.below_min += step_min
            if self.below_min >= config.DOWNGRADE_HOLD_MIN:
                self.status, self.below_min = target, 0.0
        return self.status


def trigger_text(driver: str, j10: float, release_level: str, eta: float | None,
                 sep_prob: float, cabin_rate: float, score: float = 1.0) -> str:
    if score < config.CAUTION_THRESHOLD:
        return (f"No solar particle event in progress. Galactic cosmic rays only "
                f"({cabin_rate:,.0f} µSv/h in the cabin).")
    if driver == "flux":
        scale = "S3" if j10 >= 1000 else "S2" if j10 >= 100 else "S1" if j10 >= 10 else "below S1"
        return f"Proton flux {j10:,.0f} pfu at >=10 MeV (NOAA {scale})."
    if driver == "imminent":
        when = f" Protons expected in ~{eta:.0f} min." if eta else " Protons arriving."
        return f"Relativistic electron onset detected ({release_level}).{when}"
    if driver == "forecast":
        return f"{sep_prob:.0f}% chance of a solar particle event in the next 24 h."
    if driver == "dose":
        return f"Cabin dose rate {cabin_rate:,.0f} µSv/h, above the daily budget pace."
    return "No significant solar particle activity."
