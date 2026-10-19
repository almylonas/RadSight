import { LuTriangleAlert, LuShieldCheck, LuOctagonAlert, LuZap, LuCalendarClock } from "react-icons/lu";
import { Badge, Card, Meter, scoreColor } from "./ui";
import { ScoreGauge } from "../charts/Small";
import { DRIVER_LABEL, LOCATION_LABEL, LOCATION_TONE, STATUS_LABEL, dayLabel, duration, fmt, hhmm, initials, pct } from "../lib/format";

const STATUS_ICON = { safe: LuShieldCheck, caution: LuTriangleAlert, action: LuOctagonAlert };

export function StatusBanner({ d, f, compact = false }) {
  const text = d.status_text[f.status];
  const Icon = STATUS_ICON[f.status];
  const maxToday = Math.max(...f.crew.map((c) => c.today));
  if (compact) {
    return (
      <div className={`banner compact ${f.status}`} role="status">
        <div className="banner-main">
          <span className="status-pill"><Icon size={15} />{STATUS_LABEL[f.status]}</span>
          <span style={{ minWidth: 0 }}>{text.action}</span>
        </div>
        <div className="banner-side">
          <span className="subtle" style={{ fontSize: 12 }}>Risk score</span>
          <span className="num" style={{ fontSize: 18, fontWeight: 600 }}>{f.score.toFixed(2)}</span>
        </div>
      </div>
    );
  }
  return (
    <div className={`banner ${f.status}`} role="status" aria-live="polite">
      <div className="banner-main">
        <div className="banner-top">
          <span className="status-pill"><Icon size={16} />{STATUS_LABEL[f.status]}</span>
          <span className="subtle" style={{ fontSize: 12 }}>Driven by {DRIVER_LABEL[f.driver].toLowerCase()}</span>
        </div>
        <h2>{text.summary}</h2>
        <dl className="banner-rows">
          <dt>Trigger</dt><dd>{f.trigger}</dd>
          <dt>Latest reading</dt>
          <dd>
            <span className="num">{fmt(maxToday, 2)} mSv</span> today, highest crew member (
            {pct((maxToday / d.limits.daily_budget_mSv) * 100)} of the {d.limits.daily_budget_mSv} mSv daily budget)
          </dd>
          <dt>Action</dt><dd style={{ fontWeight: 550 }}>{text.action}</dd>
        </dl>
      </div>
      <div className="banner-side">
        <ScoreGauge score={f.score} caution={d.limits.caution} action={d.limits.action} />
        <div className="num" style={{ fontSize: 22, fontWeight: 600, marginTop: -6 }}>{f.score.toFixed(2)}</div>
        <div className="subtle" style={{ fontSize: 12 }}>Space Weather Risk Score</div>
      </div>
    </div>
  );
}

export function ImminentCard({ d, f }) {
  const { level, eta, peak, ratio } = f.rel;
  const active = level !== "quiet";
  return (
    <Card title="Imminent event" sub="10 min to 1 h ahead · REleASE method" icon={LuZap}
      actions={<Badge tone={level === "alert" ? "action" : level === "warning" ? "caution" : "safe"} dot>
        {level === "quiet" ? "Quiet" : level === "warning" ? "Warning" : "Alert"}</Badge>}>
      <div className="release-gauge" aria-label={`Detector level ${level}`}>
        {["quiet", "warning", "alert"].map((l) => (
          <div key={l} className={l === level ? `on ${l}` : ""}>{l[0].toUpperCase() + l.slice(1)}</div>
        ))}
      </div>
      {active ? (
        <div className="row" style={{ justifyContent: "space-between", alignItems: "end" }}>
          <div>
            <div className="stat-label">Proton arrival</div>
            <div className="countdown">{eta > 0 ? duration(eta) : "Arriving"}</div>
          </div>
          <dl className="kv" style={{ minWidth: 150 }}>
            <dt>Predicted peak</dt><dd>{fmt(peak)} pfu</dd>
            <dt>Electron rise</dt><dd>×{fmt(ratio)}</dd>
          </dl>
        </div>
      ) : (
        <div className="muted" style={{ fontSize: 13 }}>
          No relativistic electron onset. Electrons travel at ~c, protons at ~0.25c, so an onset
          gives about <b className="num" style={{ color: "var(--fg)" }}>{Math.round(d.warning_window_min)} min</b> of
          warning before 30 MeV protons arrive.
          <div className="subtle" style={{ marginTop: 6 }}>Electron enhancement now ×{fmt(ratio)} (alarm at ×4).</div>
        </div>
      )}
    </Card>
  );
}

export function ForecastCard({ f }) {
  const rows = [
    ["Solar particle event", f.fc.sep],
    ["HF radio blackout (R2+)", f.fc.hf],
    ["Spacecraft disruption", f.fc.disruption],
  ];
  return (
    <Card title="24 h forecast" sub="NOAA flare probabilities → mission impact" icon={LuCalendarClock}
      actions={f.fc.row ? <Badge tone="brand">{f.fc.row} row</Badge> : <Badge>Below table</Badge>}>
      {rows.map(([label, v]) => (
        <Meter key={label} label={label} value={v} max={100} display={pct(v)}
          color={scoreColor(v / 100, 0.2, 0.5)} />
      ))}
      <div className="row subtle" style={{ fontSize: 12, gap: 14 }}>
        <span>M-class <b className="num" style={{ color: "var(--fg)" }}>{pct(f.fc.m)}</b></span>
        <span>X-class <b className="num" style={{ color: "var(--fg)" }}>{pct(f.fc.x)}</b></span>
        <span>≥10 MeV protons <b className="num" style={{ color: "var(--fg)" }}>{pct(f.fc.proton)}</b></span>
      </div>
    </Card>
  );
}

export function DriversCard({ d, f }) {
  return (
    <Card title="Risk drivers" sub="The highest component sets the status">
      {Object.entries(f.comps).map(([k, v]) => (
        <Meter key={k} label={DRIVER_LABEL[k]} value={v} max={1} display={v.toFixed(2)}
          ticks={[d.limits.caution, d.limits.action]} color={scoreColor(v, d.limits.caution, d.limits.action)} />
      ))}
    </Card>
  );
}

export function EventLog({ d, f, onPick, limit }) {
  let events = d.events;
  const past = events.filter((e) => e.i <= f.i);
  const shown = limit ? past.slice(-limit).reverse() : events;
  return (
    <div className="events">
      {shown.length === 0 && <div className="subtle" style={{ padding: 8 }}>No events yet.</div>}
      {shown.map((e, k) => (
        <button key={k} className={`event ${e.i > f.i ? "future" : ""}`} onClick={() => onPick?.(e.i)}
          title="Jump to this moment">
          <time>{e.t.slice(0, 10) !== f.t.slice(0, 10) ? <span className="ev-day">{dayLabel(e.t)}</span> : null}{hhmm(e.t)}</time>
          <i className={e.kind === "crew" ? "brand" : e.level} />
          <span>{e.text}</span>
        </button>
      ))}
    </div>
  );
}

export function LocationBadge({ loc }) {
  return <Badge tone={LOCATION_TONE[loc]} className="loc">{LOCATION_LABEL[loc]}</Badge>;
}

export function Person({ c }) {
  return (
    <div className="person">
      <div className="avatar">{initials(c.name)}</div>
      <div style={{ minWidth: 0 }}>
        <div className="person-name">{c.name}</div>
        <div className="person-role">{c.role} · {c.agency} · {c.base === "orbit" ? "Lunar orbit" : "Surface"}</div>
      </div>
    </div>
  );
}

export function CrewTable({ d, f }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Crew member</th><th>Location</th><th className="num">Dose rate</th>
            <th className="num">Today</th><th className="num">Mission</th><th style={{ minWidth: 150 }}>Career (600 mSv limit)</th>
          </tr>
        </thead>
        <tbody>
          {f.crew.map((c) => (
            <tr key={c.id}>
              <td><Person c={c} /></td>
              <td><LocationBadge loc={c.loc} /></td>
              <td className="num">{fmt(c.rate)} µSv/h</td>
              <td className="num" style={{ color: c.today > d.limits.daily_budget_mSv ? "var(--action)" : undefined }}>
                {fmt(c.today, 2)} mSv</td>
              <td className="num">{fmt(c.mission, 2)} mSv</td>
              <td>
                <Meter value={c.career} max={d.limits.career_mSv} display={`${fmt(c.career)} mSv`} thin
                  color={c.career / d.limits.career_mSv > 0.8 ? "var(--caution)" : "var(--brand)"} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
