"""Imminent-event detector (10 min - 1 h horizon).

Follows the principle of HESPERIA REleASE (Posner 2007; Malandraki & Crosby
2018): relativistic electrons from a solar eruption arrive tens of minutes
before the protons, and the electron rise predicts the proton intensity.

The operational REleASE system uses SOHO/EPHIN and ACE/EPAM electrons and is
reached through the ESA SWE federated service. This module reproduces the
logic on any electron channel so RadSight works with whatever feed it has;
plug the federated alert in via `sources.hesperia` when access is granted.

Levels mirror the REleASE gauge: quiet / warning / alert.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from radsight.physics.transport import warning_window_min

ONSET_RATIO = 4.0         # flux above this multiple of background = onset
BACKGROUND_WINDOW_H = 6
WARNING_PEAK_PFU = 10.0   # predicted >10 MeV peak that triggers a warning
ALERT_PEAK_PFU = 100.0    # ... and an alert
RESET_AFTER_H = 12


@dataclass
class ReleaseState:
    level: str                 # quiet | warning | alert
    onset: datetime | None
    eta_min: float | None      # minutes until predicted proton arrival
    predicted_peak_pfu: float | None
    electron_ratio: float


def predicted_proton_peak(electron_ratio: float) -> float:
    """Empirical scaling: the >10 MeV peak grows with the electron enhancement."""
    if electron_ratio <= 1:
        return 0.0
    return 10 ** (0.95 * math.log10(electron_ratio) + 0.25)


def _level(predicted: float) -> str:
    if predicted >= ALERT_PEAK_PFU:
        return "alert"
    if predicted >= WARNING_PEAK_PFU:
        return "warning"
    return "quiet"


def run_detector(times: list[datetime], electrons: np.ndarray) -> list[ReleaseState]:
    """Evaluate the detector at every time step, using only past data."""
    step_s = (times[1] - times[0]).total_seconds() if len(times) > 1 else 600.0
    window = max(int(BACKGROUND_WINDOW_H * 3600 / step_s), 3)
    lead = warning_window_min(30.0)

    states: list[ReleaseState] = []
    onset: datetime | None = None
    bg_onset = 1.0
    peak_ratio = 1.0
    for i, t in enumerate(times):
        if onset is None:
            hist = electrons[max(0, i - window):i]
            bg = float(np.median(hist)) if len(hist) else float(electrons[0])
        else:
            bg = bg_onset
        ratio = float(electrons[i]) / max(bg, 1e-9)
        rising = i >= 1 and electrons[i] > electrons[i - 1]

        if onset is None and ratio >= ONSET_RATIO and rising:
            onset, bg_onset, peak_ratio = t, bg, ratio

        if onset is None:
            states.append(ReleaseState("quiet", None, None, None, ratio))
            continue

        elapsed = (t - onset).total_seconds() / 60
        if ratio < 1.5 and elapsed > RESET_AFTER_H * 60:
            onset, peak_ratio = None, 1.0
            states.append(ReleaseState("quiet", None, None, None, ratio))
            continue

        peak_ratio = max(peak_ratio, ratio)
        predicted = predicted_proton_peak(peak_ratio)
        states.append(ReleaseState(_level(predicted), onset, max(lead - elapsed, 0.0),
                                   predicted, ratio))
    return states
