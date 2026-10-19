import { LuActivity, LuSun, LuZap, LuTable } from "react-icons/lu";
import { Card, Badge, PageHead } from "../components/ui";
import { StatusBanner } from "../components/panels";
import TimeChart, { Legend } from "../charts/TimeChart";
import { PROTON_THRESHOLDS } from "./Overview";
import { dayLabel, fmt, hhmm, xrayClass } from "../lib/format";

const XRAY_THRESHOLDS = [
  { y: 1e-5, label: "M · R1 radio blackout", color: "var(--caution)" },
  { y: 1e-4, label: "X · R3 radio blackout", color: "var(--action)" },
];

function classTone(c) {
  if (!c) return "";
  return c[0] === "X" ? "action" : c[0] === "M" ? "caution" : "";
}

export default function Environment({ d, f, setIdx }) {
  const end = d.mode === "replay" ? f.i : undefined;
  const protons = [
    { key: "p10", label: "≥10 MeV", data: d.env.j10, color: "var(--s1)", area: true },
    { key: "p100", label: "≥100 MeV", data: d.env.j100, color: "var(--s2)" },
  ];
  const electrons = [{ key: "e", label: "Electrons", data: d.env.electrons, color: "var(--s3)", area: true }];
  const xray = [{ key: "x", label: "0.1–0.8 nm", data: d.env.xray, color: "var(--s5)", area: true, fmt: xrayClass }];
  const flares = [...d.flares].reverse().slice(0, 14);
  return (
    <>
      <PageHead title="Radiation environment" sub="The measurements behind the status: solar protons that
        deliver dose, electrons that give early warning, and X-rays that mark the flare." />
      <StatusBanner d={d} f={f} compact />

      <div className="grid g-3">
        <section className="card kpi">
          <div className="stat-label"><LuActivity size={14} />≥10 MeV protons</div>
          <div className="stat-value">{fmt(f.j10)}<small>pfu</small></div>
          <div className="stat-meta">≥100 MeV {fmt(f.j100)} pfu</div>
        </section>
        <section className="card kpi">
          <div className="stat-label"><LuZap size={14} />Electron enhancement</div>
          <div className="stat-value">×{fmt(f.rel.ratio)}</div>
          <div className="stat-meta">{d.env.electron_label}</div>
        </section>
        <section className="card kpi">
          <div className="stat-label"><LuSun size={14} />X-ray flux</div>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div className="stat-value">{xrayClass(f.xray)}</div>
            <Badge tone={classTone(xrayClass(f.xray))}>{f.xray.toExponential(1)} W/m²</Badge>
          </div>
          <div className="stat-meta">GOES 0.1–0.8 nm long channel</div>
        </section>
      </div>

      <Card title="Solar proton flux" sub="Integral flux, particles cm⁻² s⁻¹ sr⁻¹ (pfu) · NOAA S-scale"
        icon={LuActivity} actions={<Legend series={protons} />}>
        <TimeChart times={d.times} series={protons} log height={260} unit="pfu" yMin={0.1}
          thresholds={PROTON_THRESHOLDS} cursor={f.i} end={end} onPick={setIdx} />
        {d.env.proton_note && <div className="subtle" style={{ fontSize: 12 }}>{d.env.proton_note}</div>}
      </Card>

      <div className="grid g-2">
        <Card title="Electrons" sub={d.env.electron_label} icon={LuZap}>
          <TimeChart times={d.times} series={electrons} log height={200} unit="pfu"
            cursor={f.i} end={end} onPick={setIdx} />
        </Card>
        <Card title="Solar X-rays" sub="Flare class from peak flux" icon={LuSun}>
          <TimeChart times={d.times} series={xray} log height={200} unit="W/m²" yMin={1e-7} yMax={1e-3}
            thresholds={XRAY_THRESHOLDS} cursor={f.i} end={end} onPick={setIdx} />
        </Card>
      </div>

      <div className="grid g-2">
        <Card title="Recent flares" sub="NOAA SWPC flare list" icon={LuTable}>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Peak</th><th>Begin</th><th>Class</th></tr></thead>
              <tbody>
                {flares.map((fl) => (
                  <tr key={fl.peak + fl.class}>
                    <td className="mono" style={{ fontSize: 12 }}>{dayLabel(fl.peak)} {hhmm(fl.peak)}</td>
                    <td className="mono subtle" style={{ fontSize: 12 }}>{hhmm(fl.begin)}</td>
                    <td><Badge tone={classTone(fl.class)}>{fl.class}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Flare catalogue" sub="NASA DONKI, with source region" icon={LuTable}>
          {d.donki_flares.length === 0 ? (
            <div className="subtle">No DONKI records for this period. The replay uses the 2017 event only.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th>Peak</th><th>Class</th><th>Region</th></tr></thead>
                <tbody>
                  {[...d.donki_flares].reverse().map((fl) => (
                    <tr key={fl.id}>
                      <td className="mono" style={{ fontSize: 12 }}>{fl.peak ? `${dayLabel(fl.peak)} ${hhmm(fl.peak)}` : "–"}</td>
                      <td><Badge tone={classTone(fl.class)}>{fl.class}</Badge></td>
                      <td className="mono subtle" style={{ fontSize: 12 }}>{fl.location}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
