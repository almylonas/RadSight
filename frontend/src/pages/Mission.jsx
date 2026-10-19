import { LuOrbit, LuShield } from "react-icons/lu";
import { Card, PageHead } from "../components/ui";
import { StatusBanner } from "../components/panels";
import { fmt, LOCATION_LABEL } from "../lib/format";

function CislunarMap({ geo, status }) {
  const W = 560, H = 320, ex = 120, ey = 170;
  const a = (geo.moon_lon_deg * Math.PI) / 180;
  const R = 330;  // Earth–Moon distance on screen (not to scale)
  const mx = ex + R * Math.cos(a * 0.25 - 0.15), my = ey - R * 0.32 * Math.sin(a * 0.25 - 0.15);
  const orbitR = 34;
  const ph = geo.orbit_phase * 2 * Math.PI;
  const sx = mx + orbitR * Math.cos(ph), sy = my + orbitR * 0.55 * Math.sin(ph);
  const c = status === "action" ? "var(--action)" : status === "caution" ? "var(--caution)" : "var(--safe)";
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Earth–Moon system with spacecraft position">
      <defs>
        <radialGradient id="earth" cx="0.4" cy="0.35"><stop offset="0" stopColor="#5aa9e6" /><stop offset="1" stopColor="#1d3d6b" /></radialGradient>
        <radialGradient id="moon" cx="0.4" cy="0.35"><stop offset="0" stopColor="#d4d4d8" /><stop offset="1" stopColor="#71717a" /></radialGradient>
      </defs>
      {/* sunlight from the right: incoming solar particles */}
      {[0, 1, 2, 3, 4, 5].map((k) => (
        <line key={k} x1={W - 6} x2={W - 60} y1={40 + k * 48} y2={40 + k * 48} stroke={c} strokeOpacity="0.35"
          strokeDasharray="2 6" />
      ))}
      <text x={W - 8} y={22} textAnchor="end" fill="var(--subtle)" fontSize="11" fontFamily="var(--mono)">→ Sun</text>
      <ellipse cx={ex} cy={ey} rx={R * 0.98} ry={R * 0.33} fill="none" stroke="var(--border-strong)" strokeDasharray="3 5" />
      <circle cx={ex} cy={ey} r="26" fill="url(#earth)" />
      <text x={ex} y={ey + 46} textAnchor="middle" fill="var(--muted)" fontSize="12">Earth</text>
      <line x1={ex} y1={ey} x2={mx} y2={my} stroke="var(--border-strong)" />
      <text x={(ex + mx) / 2} y={(ey + my) / 2 - 8} textAnchor="middle" fill="var(--subtle)" fontSize="11"
        fontFamily="var(--mono)">{fmt(geo.earth_moon_km)} km</text>
      <ellipse cx={mx} cy={my} rx={orbitR} ry={orbitR * 0.55} fill="none" stroke="var(--brand)" strokeOpacity="0.5" />
      <circle cx={mx} cy={my} r="13" fill="url(#moon)" />
      <text x={mx} y={my + 36} textAnchor="middle" fill="var(--muted)" fontSize="12">Moon</text>
      <circle cx={sx} cy={sy} r="5" fill={c} stroke="var(--bg)" strokeWidth="2" />
      <text x={sx - 9} y={sy - 8} textAnchor="end" fill="var(--fg)" fontSize="11">Crew vehicle</text>
      <rect x={mx - 3} y={my + 9} width="6" height="6" fill="var(--s3)" />
    </svg>
  );
}

export default function Mission({ d, f }) {
  const g = f.geo;
  const rates = d.location_rates_uSv_h;
  return (
    <>
      <PageHead title="Mission" sub={`${d.mission.name}. Two crew in low lunar orbit, two on the surface.`} />
      <StatusBanner d={d} f={f} compact />
      <div className="grid g-2-1">
        <Card title="Cislunar position" sub="Diagram, not to scale" icon={LuOrbit}>
          <CislunarMap geo={g} status={f.status} />
        </Card>
        <Card title="Mission data">
          <dl className="kv">
            <dt>Mission day</dt><dd>{fmt(g.mission_day, 1)}</dd>
            <dt>Earth–Moon distance</dt><dd>{fmt(g.earth_moon_km)} km</dd>
            <dt>One-way light time</dt><dd>{g.light_time_s} s</dd>
            <dt>Orbit altitude</dt><dd>{g.orbit_altitude_km} km</dd>
            <dt>Orbit phase</dt><dd>{Math.round(g.orbit_phase * 360)}°</dd>
            <dt>Moon ecliptic longitude</dt><dd>{g.moon_lon_deg.toFixed(1)}°</dd>
            <dt>Landing site</dt><dd style={{ fontFamily: "var(--font)" }}>{d.mission.landing_site.name}</dd>
          </dl>
          <div className="subtle" style={{ fontSize: 12 }}>
            Beyond the magnetosphere there is no geomagnetic shielding: solar particles reach the
            spacecraft directly. Only mass protects the crew.
          </div>
        </Card>
      </div>
      <Card title="Shielding" sub="Dose rate at the blood-forming organs right now, for every place the crew can be"
        icon={LuShield}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Location</th><th className="num">Shielding</th><th className="num">Protons stopped below</th>
                <th className="num">Dose rate</th><th>Crew here</th></tr>
            </thead>
            <tbody>
              {d.shielding.map((s) => {
                const here = f.crew.filter((c) => c.loc === s.key).map((c) => c.name.split(" ")[0]).join(", ");
                return (
                  <tr key={s.key}>
                    <td>{s.label}</td>
                    <td className="num">{s.areal_g_cm2} g/cm²</td>
                    <td className="num">{s.e_cut_MeV} MeV</td>
                    <td className="num">{fmt(rates[s.key][f.i])} µSv/h</td>
                    <td className="muted">{here || "–"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="subtle" style={{ fontSize: 12 }}>
          Cutoff includes ~5 g/cm² of body self-shielding. Lunar surface locations see half the sky,
          since the Moon blocks the rest. {Object.keys(LOCATION_LABEL).length} locations modelled.
        </div>
      </Card>
    </>
  );
}
