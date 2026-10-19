// Loads a dashboard timeline from the Python backend, falling back to the
// bundled data (exported by backend/scripts/export_snapshot.py) when the
// backend is not reachable.
import snapshot from "../data/snapshot.json";
import replay from "../data/replay.json";

const API_BASE =
  (typeof window !== "undefined" && window.RADSIGHT_API) ||
  (import.meta.env && import.meta.env.VITE_API_URL) ||
  "";

const BUNDLED = { live: snapshot, replay };

export async function loadTimeline(mode) {
  const path = mode === "live" ? "/api/live" : "/api/replay";
  try {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 5000);
    const res = await fetch(`${API_BASE}${path}`, { signal: ctl.signal });
    clearTimeout(timer);
    if (res.ok && (res.headers.get("content-type") || "").includes("json")) {
      return { data: await res.json(), origin: "api" };
    }
  } catch {
    // backend not running: use bundled data
  }
  return { data: BUNDLED[mode], origin: "bundled" };
}

// Everything the pages need about one moment of the timeline.
export function frameAt(d, i) {
  const crew = d.crew.map((c) => ({
    ...c,
    loc: c.location[i],
    rate: c.dose_rate_uSv_h[i],
    mission: c.dosimeter_mSv[i],
    missionTrue: c.mission_mSv[i],
    conventional: c.mission_conventional_mSv[i],
    today: c.today_mSv[i],
    career: c.prior_career_mSv + c.dosimeter_mSv[i],
  }));
  return {
    i,
    t: d.times[i],
    status: d.risk.status[i],
    score: d.risk.score[i],
    driver: d.risk.driver[i],
    trigger: d.risk.trigger[i],
    comps: Object.fromEntries(Object.entries(d.risk.components).map(([k, v]) => [k, v[i]])),
    fc: Object.fromEntries(Object.entries(d.forecast24).map(([k, v]) => [k, v[i]])),
    rel: Object.fromEntries(Object.entries(d.release).map(([k, v]) => [k, v[i]])),
    geo: d.geometry[i],
    j10: d.env.j10[i],
    j100: d.env.j100[i],
    electrons: d.env.electrons[i],
    xray: d.env.xray[i],
    cabinRate: d.location_rates_uSv_h.cabin[i],
    crew,
  };
}
