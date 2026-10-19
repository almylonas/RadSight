import math
from datetime import datetime, timedelta, timezone

import numpy as np

from radsight.physics.dose import SHIELDING, dose_rate, integral_flux
from radsight.physics.transport import warning_window_min
from radsight.risk.forecast import forecast_24h
from radsight.risk.release import run_detector
from radsight.risk.score import StatusTracker, components, score_and_driver
from radsight.scenarios import replay_timeline


def test_quiet_sun_is_gcr_only():
    r = dose_rate(0.4, 0.25, "cabin")
    assert r["sep"] == 0
    assert math.isclose(r["total"], 1840 / 24, rel_tol=1e-6)


def test_shielding_order_during_storm():
    rates = {k: dose_rate(1000, 60, k)["total"] for k in ("eva", "cabin", "shelter")}
    assert rates["eva"] > rates["cabin"] > rates["shelter"]


def test_integral_flux_matches_channels():
    assert math.isclose(integral_flux(100, 5, 10), 100)
    assert math.isclose(integral_flux(100, 5, 100), 5, rel_tol=1e-6)


def test_warning_window_is_tens_of_minutes():
    assert 20 < warning_window_min(30) < 45


def test_forecast_uses_impact_table():
    assert forecast_24h(80, 15, 10).active_row == "X1+"
    assert forecast_24h(10, 1, 1).active_row is None


def test_status_thresholds_and_hysteresis():
    c = components(150, "quiet", 0, 70)
    score, driver = score_and_driver(c)
    assert driver == "flux" and score >= 0.6
    tr = StatusTracker()
    assert tr.update(0.7, 10) == "action"
    assert tr.update(0.1, 10) == "action"     # held
    for _ in range(6):
        status = tr.update(0.1, 10)
    assert status == "safe"


def test_detector_fires_on_electron_onset():
    t0 = datetime(2020, 1, 1, tzinfo=timezone.utc)
    times = [t0 + timedelta(minutes=10 * i) for i in range(80)]
    e = np.ones(80)
    e[50:] = np.linspace(5, 500, 30)
    states = run_detector(times, e)
    assert states[40].level == "quiet"
    assert states[60].level in ("warning", "alert")


def test_replay_warns_before_protons():
    d = replay_timeline()
    first_action = d["risk"]["status"].index("action")
    first_s1 = next(i for i, v in enumerate(d["env"]["j10"]) if v >= 10)
    assert first_action < first_s1
    for c in d["crew"]:
        assert c["mission_mSv"][-1] <= c["mission_conventional_mSv"][-1]
