"""Central configuration: data endpoints, dose limits and status thresholds."""
from __future__ import annotations

import os

# --- Data endpoints ---------------------------------------------------------
NOAA_BASE = "https://services.swpc.noaa.gov"
NOAA = {
    "protons": f"{NOAA_BASE}/json/goes/primary/integral-protons-1-day.json",
    "electrons": f"{NOAA_BASE}/json/goes/primary/integral-electrons-1-day.json",
    "xrays": f"{NOAA_BASE}/json/goes/primary/xrays-1-day.json",
    "flares": f"{NOAA_BASE}/json/goes/primary/xray-flares-7-day.json",
    "probabilities": f"{NOAA_BASE}/json/solar_probabilities.json",
    "forecast45": f"{NOAA_BASE}/json/45-day-forecast.json",
}
DONKI_BASE = "https://api.nasa.gov/DONKI"
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
HESPERIA_RELEASE_URL = (
    "https://www.hesperia.astro.noa.gr/index.php/results/real-time-prediction-tools/release-alert"
)

HTTP_TIMEOUT_S = 15
CACHE_TTL_S = 300  # NOAA updates every 5 min

# --- Dose limits (NASA-STD-3001) --------------------------------------------
CAREER_LIMIT_mSv = 600.0          # effective dose, career
BFO_30D_LIMIT_mGyEq = 250.0       # blood-forming organs, 30 days
BFO_1Y_LIMIT_mGyEq = 500.0        # blood-forming organs, 1 year
# RadSight daily budget: the 30-day BFO limit spread evenly over 30 days.
DAILY_BUDGET_mSv = BFO_30D_LIMIT_mGyEq / 30.0
BUDGET_RATE_uSv_h = DAILY_BUDGET_mSv * 1000.0 / 24.0

# --- Status levels ------------------------------------------------------------
CAUTION_THRESHOLD = 0.3
ACTION_THRESHOLD = 0.6
DOWNGRADE_HOLD_MIN = 60  # a status only steps down after 60 min below its threshold

STATUS_TEXT = {
    "safe": {
        "label": "Safe",
        "summary": "All radiation levels are within normal operational limits.",
        "action": "No action required. Continue standard operations.",
    },
    "caution": {
        "label": "Caution Needed",
        "summary": "Elevated particle levels detected. Cumulative dose is rising.",
        "action": "Monitor dose trend. Prepare for potential exposure mitigation. "
                  "Limit time in exposed zones.",
    },
    "action": {
        "label": "Action Needed",
        "summary": "Radiation exposure threshold exceeded or rapidly approaching.",
        "action": "Suspend EVA and outdoor activity. Move to shielded area immediately. "
                  "Log exposure time and notify radiation safety lead.",
    },
}
