import { LuCalendarRange, LuTable } from "react-icons/lu";
import { Card, PageHead } from "../components/ui";
import { ForecastCard, ImminentCard, StatusBanner } from "../components/panels";
import TimeChart from "../charts/TimeChart";
import { dayLabel } from "../lib/format";

export default function Forecast({ d, f }) {
  const ol = d.outlook14;
  const times = ol.map((o) => `${o.date}T00:00Z`);
  const series = [{ key: "risk", label: "Risk score", data: ol.map((o) => o.score), color: "var(--brand)", area: true,
    fmt: (v) => v.toFixed(2) }];
  const thresholds = [
    { y: d.limits.caution, label: "Caution 0.3", color: "var(--caution)" },
    { y: d.limits.action, label: "Action 0.6", color: "var(--action)" },
  ];
  return (
    <>
      <PageHead title="Forecast" sub="Three horizons: imminent proton arrival (minutes), the next 24 hours,
        and a 14-day outlook for planning EVAs and surface operations." />
      <StatusBanner d={d} f={f} compact />

      <div className="grid g-2">
        <ImminentCard d={d} f={f} />
        <ForecastCard f={f} />
      </div>

      <div className="grid g-2-1">
        <Card title="14-day outlook" sub="Daily Space Weather Risk Score from NOAA's F10.7 and Ap forecast"
          icon={LuCalendarRange}>
          {ol.length ? (
            <TimeChart times={times} series={series} height={240} yMin={0} yMax={1} thresholds={thresholds}
              yFormat={(v) => v.toFixed(2)} />
          ) : <div className="subtle">No outlook available.</div>}
        </Card>
        <Card title="Outlook inputs" icon={LuTable}>
          <div className="table-wrap" style={{ maxHeight: 280, overflowY: "auto" }}>
            <table>
              <thead><tr><th>Day</th><th className="num">F10.7</th><th className="num">Ap</th><th className="num">Score</th></tr></thead>
              <tbody>
                {ol.map((o) => (
                  <tr key={o.date}>
                    <td>{dayLabel(`${o.date}T00:00Z`)}</td>
                    <td className="num">{o.f107}</td><td className="num">{o.ap}</td>
                    <td className="num" style={{ color: o.score >= 0.6 ? "var(--action)" : o.score >= 0.3 ? "var(--caution)" : "var(--safe)" }}>
                      {o.score.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <Card title="Impact table" sub="How flare forecasts translate into mission impact (RadSight model estimates).
        The highest row whose flare probability is reached is used." icon={LuTable}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Flare forecast</th><th className="num">Chance of SEP</th>
                <th className="num">HF radio blackout</th><th className="num">Spacecraft disruption</th></tr>
            </thead>
            <tbody>
              {d.impact_table.map((r) => (
                <tr key={r.row} className={r.row === f.fc.row ? "active-row" : ""}>
                  <td><b>{r.row}</b> at ≥{r.threshold}%{r.row === f.fc.row && <span className="subtle"> · active</span>}</td>
                  <td className="num">{r.sep}%</td><td className="num">{r.hf}%</td><td className="num">{r.disruption}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
