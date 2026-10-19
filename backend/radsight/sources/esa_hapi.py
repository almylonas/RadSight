"""ESA Space Weather Service Network: HAPI server client (machine-to-machine).

Setup (once):
  1. Log in to https://swe.ssa.esa.int
  2. Request M2M credentials via the OIDC client self-enrolment app:
     https://sso.s2p.esa.int/oidc-console/swe/
  3. Put them in the environment:
       export ESA_SWE_CLIENT_ID=...
       export ESA_SWE_CLIENT_SECRET=...

Tokens last a few minutes and there is no refresh token, so a new one is
requested automatically when the cached one is about to expire.
Server limits: max 100,000 data elements / ~12 MB per /data response.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

HAPI_BASE = "https://swe.ssa.esa.int/hapi"
TOKEN_URL = "https://sso.s2p.esa.int/realms/swe/protocol/openid-connect/token"
SCOPE = "swe_hapiserver"

_token: dict = {"value": None, "expires": 0.0}


def configured() -> bool:
    return bool(os.getenv("ESA_SWE_CLIENT_ID") and os.getenv("ESA_SWE_CLIENT_SECRET"))


def access_token() -> str:
    if _token["value"] and time.time() < _token["expires"] - 30:
        return _token["value"]
    body = urllib.parse.urlencode({
        "client_id": os.environ["ESA_SWE_CLIENT_ID"],
        "client_secret": os.environ["ESA_SWE_CLIENT_SECRET"],
        "grant_type": "client_credentials",
        "scope": SCOPE,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as r:
        tok = json.loads(r.read())
    _token.update(value=tok["access_token"], expires=time.time() + float(tok.get("expires_in", 300)))
    return _token["value"]


def _get(path: str, params: dict | None = None):
    url = f"{HAPI_BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(2):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token()}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 401 and attempt == 0:
                _token["value"] = None  # expired: get a new token and retry once
                continue
            raise


def catalog() -> list[dict]:
    return _get("catalog")["catalog"]


def info(dataset: str) -> dict:
    return _get("info", {"dataset": dataset})


def data(dataset: str, start: str, stop: str, parameters: list[str] | None = None) -> dict:
    """Time series as HAPI JSON: {'parameters': [...], 'data': [[time, v1, ...], ...]}."""
    p = {"dataset": dataset, "start": start, "stop": stop, "format": "json"}
    if parameters:
        p["parameters"] = ",".join(parameters)
    return _get("data", p)
