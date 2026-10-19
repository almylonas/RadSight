"""Mission geometry: where the Moon is, and where the crew is around it.

Uses a low-precision lunar ephemeris (Meeus, ~0.3 deg / ~500 km), which is
plenty for a situational display.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

J2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
LLO_PERIOD_MIN = 118.0      # ~100 km low lunar orbit
LLO_ALTITUDE_KM = 100.0
LANDING_SITE = {"name": "Shackleton rim, lunar south pole", "lat": -89.5, "lon": 0.0}


def moon_position(t: datetime) -> dict[str, float]:
    d = (t - J2000).total_seconds() / 86400.0
    lon = math.radians((218.316 + 13.176396 * d) % 360)
    anomaly = math.radians((134.963 + 13.064993 * d) % 360)
    lon += math.radians(6.289) * math.sin(anomaly)
    dist = 385001.0 - 20905.0 * math.cos(anomaly)
    return {"ecl_lon_deg": math.degrees(lon) % 360, "distance_km": dist}


def geometry(t: datetime, mission_start: datetime) -> dict:
    moon = moon_position(t)
    orbit_phase = ((t - mission_start).total_seconds() / 60.0 / LLO_PERIOD_MIN) % 1.0
    return {
        "moon_lon_deg": round(moon["ecl_lon_deg"], 2),
        "earth_moon_km": round(moon["distance_km"]),
        "light_time_s": round(moon["distance_km"] / 299792.458, 2),
        "orbit_phase": round(orbit_phase, 4),
        "orbit_altitude_km": LLO_ALTITUDE_KM,
        "mission_day": round((t - mission_start).total_seconds() / 86400.0, 2),
    }
