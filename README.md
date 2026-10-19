# RadSight

Radiation made visible. Protection made possible.

A space-radiation console for crewed lunar missions. RadSight combines existing
space-weather feeds into one decision for the crew: **Safe**, **Caution Needed** or
**Action Needed**. It works on three timescales: imminent proton arrival
(10 min – 1 h), a 24 h forecast, and each astronaut's accumulated dose.

```
radsight/
├── backend/                 Python: data, physics, risk engine, simulation, API
│   ├── radsight/
│   │   ├── config.py        endpoints, NASA dose limits, status thresholds and texts
│   │   ├── sources/         NOAA SWPC, NASA DONKI, HESPERIA REleASE (ESA SWE) clients
│   │   ├── physics/         flux-to-dose model, particle travel times
│   │   ├── risk/            imminent-event detector, 24 h forecast, risk score + status
│   │   ├── sim/             crew and dosimeters, EVA plans, 2017 storm replay, trajectory
│   │   ├── engine.py        environment in → dashboard timeline out
│   │   ├── scenarios.py     live-data and replay scenarios
│   │   └── api.py           FastAPI app
│   ├── scripts/export_snapshot.py   writes the frontend's fallback data
│   ├── data/                captured real-data snapshot
│   └── tests/
└── frontend/                React (Vite): renders the timeline the backend computes
```

## Run it

Backend (Python 3.11+), in its own virtual environment so it can't change
packages your other projects depend on:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn radsight.api:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, /api is proxied to :8000
```

Without the backend running, the frontend uses the bundled data in
`frontend/src/data/`. Refresh it with `python backend/scripts/export_snapshot.py`.

ESA Space Weather data (HAPI server): request M2M credentials at
https://sso.s2p.esa.int/oidc-console/swe/, then

```bash
export ESA_SWE_CLIENT_ID=...  ESA_SWE_CLIENT_SECRET=...
python scripts/esa_catalog.py            # what your account can read
python scripts/esa_catalog.py ngrm       # details for matching datasets
```

Optional environment variables: `NASA_API_KEY` (DONKI, defaults to `DEMO_KEY`),
`ESA_SWE_TOKEN` (to switch to the operational HESPERIA REleASE feed),
`VITE_API_URL` (frontend, if the API runs on another host).

## API

| Route | Returns |
|---|---|
| `GET /api/live` | 24 h timeline from live NOAA SWPC and NASA DONKI data (cached 5 min) |
| `GET /api/replay` | 72 h replay of a storm modelled on the 10 Sep 2017 event |
| `GET /api/health` | `{"ok": true}` |

## What is real and what is simulated

* **Real:** GOES protons, electrons and X-rays, the flare list, flare and proton
  probabilities, and the 45-day F10.7/Ap forecast (NOAA SWPC); the flare catalogue
  (NASA DONKI).
* **Modelled:** the replay storm, which uses the real timing of the 10 Sep 2017 X8.2
  flare and its S3 proton event but smooth curves, not the archived GOES record.
* **Simulated:** the crew, their schedule and dosimeters, and the LUNA-3 mission.
* **Planned:** HESPERIA REleASE, EDRS-C/NGRM, COMESEP and IRF forecasts through the
  ESA Space Weather Service Network (needs an account). Until then the backend runs
  its own REleASE-type detector, with GOES electrons as a stand-in input.

## Method in brief

* **Dose:** power-law proton spectrum from the GOES ≥10 and ≥100 MeV channels,
  cutoff energy per shielding location (suit, cabin, shelter, habitat, regolith), dose =
  4π·J(>E_cut)·S(E_cut), quality factor 1.5, plus 1.84 mSv/day of galactic cosmic rays
  (MSL/RAD), halved on the lunar surface.
* **Risk score:** the maximum of four components: proton flux, imminent event, 24 h
  forecast and dose rate. Thresholds are 0.3 (Caution) and 0.6 (Action), and the status
  steps down only after 60 min.
* **Limits:** 600 mSv career and 250 mGy-Eq 30-day BFO (NASA-STD-3001). The daily
  budget is 250/30 = 8.33 mSv.
* **Response:** at Action Needed the crew go to the shelter (EVA ingress takes 30 min).
  The dashboard compares this with conventional procedures (shelter after an hour at
  S2, with no early warning) and reports the dose avoided.

Run the tests with `pip install -r requirements-dev.txt` then `pytest` (in `backend`).

## Deploy to Vercel

**One project (recommended).** `vercel.json` at the repository root uses Vercel
Services (beta) to deploy both parts together on one domain: `/api/...` goes to the
FastAPI backend, everything else to the React frontend.

1. Import the repository at vercel.com/new. Leave *Root Directory* as the folder that
   contains `vercel.json` (the repo root) and leave the preset as Vercel detects it.
2. Optional: add `NASA_API_KEY` and the ESA variables under Environment Variables.
3. Deploy. No `VITE_API_URL` is needed: the frontend calls `/api` on its own domain.

**Two projects (fallback).** Delete `vercel.json`, then import the repo twice: once with
*Root Directory* `backend` (preset FastAPI) and once with `frontend` (preset Vite,
environment variable `VITE_API_URL=https://<backend>.vercel.app`).
