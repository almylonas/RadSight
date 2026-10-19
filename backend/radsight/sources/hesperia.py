"""HESPERIA REleASE (National Observatory of Athens) via ESA SWE.

The operational REleASE forecasts (proton flux at 15.8-39.8 and 28.2-50.1 MeV
from SOHO/EPHIN and ACE/EPAM electrons) are distributed through the ESA Space
Weather Service Network, which needs a registered account:
https://swe.ssa.esa.int/en/noa-hesperia-federated

Until credentials are configured RadSight runs its own REleASE-type detector
(radsight.risk.release) on the electron feed it has. Set ESA_SWE_TOKEN and
implement `fetch_alert` against the federated endpoint to switch over.
"""
from __future__ import annotations

import os

from radsight import config

STATUS = {
    "name": "HESPERIA REleASE",
    "provider": "National Observatory of Athens (ESA SWE federated)",
    "url": config.HESPERIA_RELEASE_URL,
}


def fetch_alert() -> dict | None:
    if not os.getenv("ESA_SWE_TOKEN"):
        return None
    raise NotImplementedError("Add the ESA SWE federated endpoint for your account here.")
