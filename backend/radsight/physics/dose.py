"""Flux-to-dose model.

Converts GOES integral proton fluxes (>=10 MeV and >=100 MeV, in pfu =
particles cm^-2 s^-1 sr^-1) into a dose-equivalent rate at the blood-forming
organs for a crew member behind a given shielding.

Method (first-order, documented so it can be swapped for OLTARIS response
functions later):

1. Fit an integral power law J(>E) = J10 * (E/10)^-g between the two GOES
   channels, and steepen it by one index above 100 MeV (real SEP spectra roll
   over at high energy).
2. Each location has an effective cutoff energy: the proton energy whose range
   equals vehicle shielding + ~5 g/cm^2 of body self-shielding to the BFO.
3. Dose rate = 4*pi * J(>E_cut) * S(E_cut) * 1.602e-10 Gy per (MeV/g),
   with S the stopping power in water. Multiply by a quality factor of 1.5.
4. Add galactic cosmic rays: 1.84 mSv/day in free space (MSL/RAD cruise
   measurement), scaled per location (the Moon blocks half the sky).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MEV_PER_G_TO_GY = 1.602e-10
SEC_PER_HOUR = 3600.0
Q_SEP = 1.5
GCR_FREE_SPACE_uSv_h = 1.84e3 / 24.0  # MSL/RAD cruise, ~1.84 mSv/day

# GOES channel backgrounds that are mostly GCR / instrument floor, removed
# before computing SEP dose so GCR is not counted twice.
J10_BACKGROUND = 0.4
J100_BACKGROUND = 0.25


@dataclass(frozen=True)
class Shielding:
    key: str
    label: str
    areal_g_cm2: float      # vehicle / suit shielding
    e_cut_MeV: float        # effective cutoff at the BFO
    stopping_power: float   # MeV cm^2/g in water at e_cut
    gcr_factor: float       # relative to free space
    sep_factor: float       # 0.5 on the lunar surface (half the sky blocked)


SHIELDING: dict[str, Shielding] = {s.key: s for s in [
    Shielding("eva", "EVA suit (free space)", 0.5, 80, 8.6, 1.05, 1.0),
    Shielding("cabin", "Spacecraft cabin", 10, 140, 5.7, 1.0, 1.0),
    Shielding("shelter", "Storm shelter", 30, 230, 4.2, 0.9, 1.0),
    Shielding("surface_eva", "Lunar surface EVA", 0.5, 80, 8.6, 0.55, 0.5),
    Shielding("habitat", "Lunar habitat", 10, 140, 5.7, 0.5, 0.5),
    Shielding("surface_shelter", "Regolith shelter", 40, 260, 4.0, 0.4, 0.5),
]}


def spectral_index(j10: float, j100: float) -> float:
    j10 = max(j10, 1e-6)
    j100 = max(min(j100, j10), 1e-6)
    return max(math.log10(j10 / j100), 0.3)


def integral_flux(j10: float, j100: float, e_MeV: float) -> float:
    """Integral proton flux above e_MeV (pfu) from the two GOES channels."""
    if j10 <= 0:
        return 0.0
    g = spectral_index(j10, j100)
    if e_MeV <= 100:
        return j10 * (e_MeV / 10.0) ** (-g)
    j100_fit = j10 * 10.0 ** (-g)
    return j100_fit * (e_MeV / 100.0) ** (-(g + 1.0))


def sep_dose_rate_uSv_h(j10: float, j100: float, shield: Shielding) -> float:
    """SEP dose-equivalent rate behind `shield`, µSv/h."""
    j10_sep = max(j10 - J10_BACKGROUND, 0.0)
    j100_sep = max(j100 - J100_BACKGROUND, 0.0)
    if j10_sep <= 0:
        return 0.0
    j100_sep = max(j100_sep, j10_sep * 1e-3)
    j_cut = integral_flux(j10_sep, j100_sep, shield.e_cut_MeV)
    omni = 4.0 * math.pi * j_cut  # cm^-2 s^-1
    gy_per_s = omni * shield.stopping_power * MEV_PER_G_TO_GY
    return gy_per_s * SEC_PER_HOUR * 1e6 * Q_SEP * shield.sep_factor


def gcr_dose_rate_uSv_h(shield: Shielding) -> float:
    return GCR_FREE_SPACE_uSv_h * shield.gcr_factor


def dose_rate(j10: float, j100: float, location: str) -> dict[str, float]:
    shield = SHIELDING[location]
    sep = sep_dose_rate_uSv_h(j10, j100, shield)
    gcr = gcr_dose_rate_uSv_h(shield)
    return {"gcr": gcr, "sep": sep, "total": gcr + sep}
