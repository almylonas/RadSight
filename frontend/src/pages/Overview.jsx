import { LuActivity, LuHeartPulse, LuListChecks, LuRadiation, LuUsers } from "react-icons/lu";
import { Card, Badge } from "../components/ui";
import { CrewTable, DriversCard, EventLog, ForecastCard, ImminentCard, StatusBanner } from "../components/panels";
import TimeChart, { Legend } from "../charts/TimeChart";
import { Sparkline } from "../charts/Small";
import { fmt, pct, sScale } from "../lib/format";

export const PROTON_THRESHOLDS = [
  { y: 10, label: "S1 · 10 pfu", color: "var(--caution)" },
  { y: 100, label: "S2 · 100 pfu", color: "var(--action)" },
  { y: 1000, label: "S3 · 1,000 pfu", color: "var(--action)" },
];

export default function Overview({ d, f, setIdx }) {
  const maxToday = Math.max(...f.crew.map((c) => c.today));
  const maxMission = Math.max(...f.crew.map((c) => c.mission));
  const protonSeries = [
    { key: "p10", label: "≥10 MeV", data: d.env.j10, color: "var(--s1)", area: true },
    { key: "p100", label: "≥100 MeV", data: d.env.j100, color: "var(--s2)" },
  ];
  return (
    <>
      <StatusBanner d={d} f={f} />

      <div className="grid g-4">
        <section className="card kpi">
          <div className="stat-label"><LuRadiation size={14} />Cabin dose rate</div>
          <div className="row" style={{ justifyContent: "space-between", flexWrap: "nowrap" }}>
            <div className="stat-value">{fmt(f.cabinRate)}<small>µSv/h</small></div>
            <Sparkline data={d.location_rates_uSv_h.cabin} end={f.i} color="var(--s1)" log />
          </div>
          <div className="stat-meta">Budget pace {fmt(d.limits.daily_budget_mSv * 1000 / 24)} µSv/h</div>
        </section>
        <section className="card kpi">
          <div className="stat-label"><LuHeartPulse size={14} />Highest crew dose today</div>
          <div className="stat-value">{fmt(maxToday, 2)}<small>mSv</small></div>
          <div className="stat-meta">{pct((maxToday / d.limits.daily_budget_mSv) * 100)} of {d.limits.daily_budget_mSv} mSv daily budget</div>
        </section>
        <section className="card kpi">
          <div className="stat-label"><LuUsers size={14} />Highest mission dose</div>
          <div className="stat-value">{fmt(maxMission, 1)}<small>mSv</small></div>
          <div className="stat-meta">30-day BFO limit {d.limits.bfo_30d_mGyEq} mGy-Eq</div>
        </section>
        <section className="card kpi">
          <div className="stat-label"><LuActivity size={14} />≥10 MeV protons</div>
          <div className="row" style={{ justifyContent: "space-between", flexWrap: "nowrap" }}>
            <div className="stat-value">{fmt(f.j10)}<small>pfu</small></div>
            <Badge tone={f.j10 >= 100 ? "action" : f.j10 >= 10 ? "caution" : "safe"}>{sScale(f.j10)}</Badge>
          </div>
          <div className="stat-meta">≥100 MeV {fmt(f.j100)} pfu</div>
        </section>
      </div>

      <div className="grid g-3">
        <ImminentCard d={d} f={f} />
        <ForecastCard f={f} />
        <DriversCard d={d} f={f} />
      </div>

      <div className="grid g-2-1">
        <Card title="Solar proton flux" sub="GOES integral channels · click the chart to move the timeline"
          icon={LuActivity} actions={<Legend series={protonSeries} />}>
          <TimeChart times={d.times} series={protonSeries} log height={250} unit="pfu"
            thresholds={PROTON_THRESHOLDS} cursor={f.i} end={d.mode === "replay" ? f.i : undefined}
            onPick={setIdx} yMin={0.1} />
          {d.env.proton_note && <div className="subtle" style={{ fontSize: 12 }}>{d.env.proton_note}</div>}
        </Card>
        <Card title="Event log" sub="Latest first · click to jump" icon={LuListChecks}>
          <EventLog d={d} f={f} onPick={setIdx} limit={40} />
        </Card>
      </div>

      <Card title="Crew" sub="Simulated active dosimeters" icon={LuUsers}>
        <CrewTable d={d} f={f} />
      </Card>
    </>
  );
}
