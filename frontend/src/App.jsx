import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  LuLayoutDashboard, LuUsers, LuActivity, LuCalendarClock, LuOrbit, LuDatabase,
  LuPlay, LuPause, LuSkipForward, LuRadio, LuHistory, LuLoaderCircle,
} from "react-icons/lu";
import { frameAt, loadTimeline } from "./lib/api";
import { fullTime, STATUS_LABEL } from "./lib/format";
import { Badge } from "./components/ui";
import Overview from "./pages/Overview";
import Crew from "./pages/Crew";
import Environment from "./pages/Environment";
import Forecast from "./pages/Forecast";
import Mission from "./pages/Mission";
import Sources from "./pages/Sources";
import { Analytics } from "@vercel/analytics/next";

const PAGES = [
  { id: "overview", label: "Overview", icon: LuLayoutDashboard, el: Overview },
  { id: "crew", label: "Crew dose", icon: LuUsers, el: Crew },
  { id: "environment", label: "Environment", icon: LuActivity, el: Environment },
  { id: "forecast", label: "Forecast", icon: LuCalendarClock, el: Forecast },
  { id: "mission", label: "Mission", icon: LuOrbit, el: Mission },
  { id: "sources", label: "Data & methods", icon: LuDatabase, el: Sources },
];

const SPEEDS = [
  { v: 1, label: "10 min/s" },
  { v: 6, label: "1 h/s" },
  { v: 18, label: "3 h/s" },
];

const REPLAY_START = "2017-09-10T13:00Z";

function readPage() {
  const h = typeof location !== "undefined" ? location.hash.replace("#", "") : "";
  return PAGES.some((p) => p.id === h) ? h : "overview";
}

function Logo() {
  return (
    <div className="logo">
      <div className="logo-mark">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" />
        </svg>
      </div>
      <div className="logo-word">Rad<span>Sight</span></div>
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState("live");
  const [state, setState] = useState({ data: null, origin: null, mode: null });
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [page, setPage] = useState(readPage);

  // load data whenever the mode changes
  useEffect(() => {
    let cancelled = false;
    setPlaying(false);
    loadTimeline(mode).then(({ data, origin }) => {
      if (cancelled) return;
      setState({ data, origin, mode });
      const start = mode === "replay" ? Math.max(data.times.indexOf(REPLAY_START), 0) : data.times.length - 1;
      setIdx(start);
      if (mode === "replay") setPlaying(true);
    });
    return () => { cancelled = true; };
  }, [mode]);

  // live mode: refresh from the backend every 5 minutes, following "now"
  const lastRef = useRef(0);
  lastRef.current = state.data ? state.data.times.length - 1 : 0;
  useEffect(() => {
    if (mode !== "live" || state.origin !== "api") return undefined;
    const id = setInterval(async () => {
      const { data, origin } = await loadTimeline("live");
      const prevLast = lastRef.current;
      setState({ data, origin, mode: "live" });
      setIdx((i) => (i >= prevLast ? data.times.length - 1 : i));
    }, 300000);
    return () => clearInterval(id);
  }, [mode, state.origin]);

  // playback
  useEffect(() => {
    if (!playing || !state.data) return undefined;
    const last = state.data.times.length - 1;
    const id = setInterval(() => {
      setIdx((i) => {
        if (i >= last) { setPlaying(false); return last; }
        return Math.min(i + speed, last);
      });
    }, 400);
    return () => clearInterval(id);
  }, [playing, speed, state.data]);

  useEffect(() => {
    const onHash = () => setPage(readPage());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = useCallback((id) => {
    setPage(id);
    try { history.replaceState(null, "", `#${id}`); } catch { /* sandboxed */ }
    window.scrollTo({ top: 0 });
  }, []);

  const d = state.data;
  const ready = d && state.mode === mode;
  const f = useMemo(() => (ready ? frameAt(d, Math.min(idx, d.times.length - 1)) : null), [ready, d, idx]);
  const Page = PAGES.find((p) => p.id === page).el;
  const last = d ? d.times.length - 1 : 0;
  const pick = useCallback((i) => { setPlaying(false); setIdx(i); }, []);

  const dataBadge = !ready ? null : mode === "replay" ? <Badge tone="caution">Replay · modelled storm</Badge>
    : state.origin === "api" ? <Badge tone="safe" dot className="live">Live · NOAA SWPC</Badge>
      : <Badge tone="brand">Snapshot · real data</Badge>;

  return (
    <div className="app">
      <aside className="sidebar">
        <Logo />
        <nav className="nav" aria-label="Pages">
          <div className="nav-label">Mission console</div>
          {PAGES.map((p) => (
            <button key={p.id} onClick={() => go(p.id)} aria-current={page === p.id ? "page" : undefined}>
              <p.icon size={16} />{p.label}
              {p.id === "overview" && f && f.status !== "safe" && (
                <span className="count" style={{ color: f.status === "action" ? "var(--action)" : "var(--caution)" }}>●</span>
              )}
            </button>
          ))}
        </nav>
        <div className="side-foot">
          {f && (
            <div className="mission-chip">
              <strong>LUNA-3</strong>
              <span>Mission day {f.geo.mission_day.toFixed(1)}</span>
              <span>4 crew · 2 orbit, 2 surface</span>
            </div>
          )}
          <div className="subtle" style={{ fontSize: 11, padding: "0 4px" }}>RadSight v1.0 · simulated crew</div>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="topbar-row">
            <div className="crumbs">
              <span>LUNA-3</span><span>/</span><strong>{PAGES.find((p) => p.id === page).label}</strong>
            </div>
            <div className="top-right">
              {dataBadge}
              {f && <span className="clock">{fullTime(f.t)}</span>}
              <div className="segmented" role="group" aria-label="Data mode">
                <button aria-pressed={mode === "live"} onClick={() => setMode("live")}><LuRadio size={14} />Live</button>
                <button aria-pressed={mode === "replay"} onClick={() => setMode("replay")}><LuHistory size={14} />Replay 2017 storm</button>
              </div>
            </div>
          </div>
          {ready && (
            <div className="scrubber">
              {mode === "replay" ? (
                <button className="icon-btn" onClick={() => { if (idx >= last) setIdx(0); setPlaying((p) => !p); }}
                  aria-label={playing ? "Pause replay" : "Play replay"}>
                  {playing ? <LuPause size={15} /> : <LuPlay size={15} />}
                </button>
              ) : (
                <button className="icon-btn" onClick={() => setIdx(last)} aria-label="Jump to latest"
                  title="Jump to latest"><LuSkipForward size={15} /></button>
              )}
              <input id="timeline" type="range" min={0} max={last} value={idx} aria-label="Timeline"
                onChange={(e) => { setPlaying(false); setIdx(Number(e.target.value)); }} />
              {mode === "replay" && (
                <select id="speed" className="btn" value={speed} onChange={(e) => setSpeed(Number(e.target.value))}
                  aria-label="Replay speed">
                  {SPEEDS.map((s) => <option key={s.v} value={s.v}>{s.label}</option>)}
                </select>
              )}
              {f && <Badge tone={f.status}>{STATUS_LABEL[f.status]}</Badge>}
            </div>
          )}
        </header>

        <main className="content">
          {ready ? <Page d={d} f={f} setIdx={pick} origin={state.origin} /> : (
            <div className="row muted" style={{ padding: 40 }}><LuLoaderCircle className="spin" />Loading data…</div>
          )}
        </main>
      </div>
    </div>
  );
}
