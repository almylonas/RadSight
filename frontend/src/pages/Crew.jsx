import { Fragment } from "react";
import { LuShieldCheck, LuUsers, LuCalendarRange } from "react-icons/lu";
import { Card, Meter, PageHead } from "../components/ui";
import { LocationBadge, Person, StatusBanner } from "../components/panels";
import TimeChart, { Legend } from "../charts/TimeChart";
import { Sparkline } from "../charts/Small";
import { fmt, fullTime, hhmm, dayLabel } from "../lib/format";

function outcome(text) {
  const m = text.match(/(postponed|aborts EVA.*|starts.*|back inside)$/);
  const s = m ? m[1] : text;
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const COLORS = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)"];

export default function Crew({ d, f, setIdx }) {
  const saved = f.crew.map((c) => Math.max(c.conventional - c.missionTrue, 0));
  const totalSaved = saved.reduce((a, b) => a + b, 0);
  const series = d.crew.flatMap((c, k) => [
    { key: c.id, label: c.name.split(" ")[1], data: c.mission_mSv, color: COLORS[k] },
    { key: `${c.id}-cv`, label: `${c.name.split(" ")[1]} (no warning)`, data: c.mission_conventional_mSv,
      color: COLORS[k], dash: true, width: 1.2 },
  ]);
  return (
    <>
      <PageHead title="Crew dose" sub="Personal dose for each astronaut, from simulated active dosimeters and the
        crew's location (cabin, EVA or shelter). Dashed lines show the same crew under conventional procedures
        with no early warning." />
      <StatusBanner d={d} f={f} compact />

      <div className="grid g-4">
        {f.crew.map((c, k) => (
          <Card key={c.id} className="crew-card">
            <div className="row" style={{ justifyContent: "space-between", alignItems: "start" }}>
              <Person c={c} />
              <LocationBadge loc={c.loc} />
            </div>
            <div className="row" style={{ justifyContent: "space-between", flexWrap: "nowrap" }}>
              <div>
                <div className="stat-label">Dose rate</div>
                <div className="stat-value" style={{ fontSize: 22 }}>{fmt(c.rate)}<small>µSv/h</small></div>
              </div>
              <Sparkline data={c.dose_rate_uSv_h} end={f.i} color={COLORS[k]} log />
            </div>
            <Meter label="Today" value={c.today} max={d.limits.daily_budget_mSv}
              display={`${fmt(c.today, 2)} / ${d.limits.daily_budget_mSv} mSv`}
              color={c.today > d.limits.daily_budget_mSv ? "var(--action)" : c.today > 0.6 * d.limits.daily_budget_mSv ? "var(--caution)" : "var(--safe)"} />
            <Meter label="Mission (30-day BFO)" value={c.mission} max={d.limits.bfo_30d_mGyEq}
              display={`${fmt(c.mission, 1)} / ${d.limits.bfo_30d_mGyEq}`} />
            <Meter label="Career" value={c.career} max={d.limits.career_mSv}
              display={`${fmt(c.career)} / ${d.limits.career_mSv} mSv`} />
          </Card>
        ))}
      </div>

      <div className="grid g-2-1">
        <Card title="Cumulative mission dose" sub="Solid: RadSight response · dashed: no early warning"
          icon={LuUsers}>
          <TimeChart times={d.times} series={series} height={280} unit="mSv" cursor={f.i}
            end={d.mode === "replay" ? f.i : undefined} onPick={setIdx} />
          <Legend series={series.filter((s) => !s.dash)} />
        </Card>
        <Card title="Dose avoided" sub="Versus conventional procedures, so far" icon={LuShieldCheck}>
          <div className="big-save">{fmt(totalSaved, 2)} mSv</div>
          <div className="muted" style={{ fontSize: 13 }}>
            Across the crew. The early warning moves people to shelter before the protons arrive and cancels
            EVAs instead of letting them run into the event.
          </div>
          <dl className="kv">
            {f.crew.map((c, k) => (
              <Fragment key={c.id}><dt>{c.name}</dt><dd>{fmt(saved[k], 2)} mSv</dd></Fragment>
            ))}
          </dl>
        </Card>
      </div>

      <Card title="EVA plan" sub="Planned extravehicular activity in this time window" icon={LuCalendarRange}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Activity</th><th>Crew</th><th>Planned window</th><th>Outcome</th></tr></thead>
            <tbody>
              {d.mission.eva_plan.map((e) => {
                const names = e.crew.map((id) => d.crew.find((c) => c.id === id).name).join(", ");
                const ev = d.events.filter((x) => x.kind === "crew" && x.i <= f.i &&
                  e.crew.some((id) => x.text.includes(d.crew.find((c) => c.id === id).name)) &&
                  (x.text.includes(e.label) || x.text.includes("aborts") || x.text.includes("back inside")) &&
                  x.t >= e.start.slice(0, 16) && x.t <= e.end.slice(0, 16));
                const last = ev[ev.length - 1];
                return (
                  <tr key={e.label + e.start}>
                    <td>{e.label}</td>
                    <td>{names}</td>
                    <td className="mono" style={{ fontSize: 12 }}>{dayLabel(e.start)} {hhmm(e.start)}–{hhmm(e.end)} UTC</td>
                    <td className="muted">{last ? outcome(last.text) : "Not started"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
      <p className="subtle" style={{ fontSize: 12, margin: 0 }}>Crew and dosimeter values are simulated. Frame time {fullTime(f.t)}.</p>
    </>
  );
}
