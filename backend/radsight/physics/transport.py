"""Particle travel times along the Parker spiral.

Near-relativistic electrons and protons are released together at the Sun,
but electrons travel at ~c while 30 MeV protons travel at ~0.25c. The gap
between their arrival times is the early-warning window that REleASE-type
systems exploit.
"""
from __future__ import annotations

import math

C_M_S = 2.998e8
AU_M = 1.496e11
PROTON_MASS_MeV = 938.272
ELECTRON_MASS_MeV = 0.511
PARKER_PATH_AU = 1.2  # nominal field-line length Sun -> Earth/Moon


def beta(kinetic_MeV: float, mass_MeV: float) -> float:
    gamma = 1.0 + kinetic_MeV / mass_MeV
    return math.sqrt(1.0 - 1.0 / gamma ** 2)


def travel_time_min(kinetic_MeV: float, mass_MeV: float, path_AU: float = PARKER_PATH_AU) -> float:
    return path_AU * AU_M / (beta(kinetic_MeV, mass_MeV) * C_M_S) / 60.0


def warning_window_min(proton_MeV: float = 30.0, electron_MeV: float = 1.0,
                       path_AU: float = PARKER_PATH_AU) -> float:
    """Minutes between electron arrival and proton arrival."""
    return (travel_time_min(proton_MeV, PROTON_MASS_MeV, path_AU)
            - travel_time_min(electron_MeV, ELECTRON_MASS_MeV, path_AU))
