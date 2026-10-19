import { LuDatabase, LuFlaskConical, LuInfo } from "react-icons/lu";
import { Badge, Card, PageHead } from "../components/ui";

const TONE = { live: "safe", snapshot: "brand", model: "caution", planned: "", simulated: "caution" };

export default function Sources({ d, origin }) {
  return (
    <>
      <PageHead title="Data and methods" sub="Where every number comes from, and how RadSight turns raw
        space-weather data into a crew decision." />
      <div className="note">
        <LuInfo size={15} />
        <div>
          {origin === "api" ? "Connected to the RadSight Python backend." :
            "Running on data bundled with the app. Start the Python backend to fetch NOAA and NASA data continuously."}
          {d.notes.map((n) => <div key={n}>{n}</div>)}
        </div>
      </div>
      <Card title="Data feeds" icon={LuDatabase}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Feed</th><th>Provider</th><th>Status</th><th>Latest</th><th>Cadence</th><th>Used for</th></tr></thead>
            <tbody>
              {d.sources.map((s) => (
                <tr key={s.name}>
                  <td>{s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a> : s.name}</td>
                  <td className="muted">{s.provider}</td>
                  <td><Badge tone={TONE[s.status]} dot={s.status === "live"} className={s.status === "live" ? "live" : ""}>{s.status}</Badge></td>
                  <td className="mono subtle" style={{ fontSize: 12 }}>{s.last || "–"}</td>
                  <td className="muted">{s.cadence}</td>
                  <td className="muted">{s.used_for}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      <div className="grid g-2">
        <Card title="Dose model" icon={LuFlaskConical}>
          <div className="prose">
            <p>The two GOES channels define an integral power-law spectrum, steepened above 100 MeV. Each
              location has a cutoff energy: the proton energy whose range matches vehicle shielding plus
              body self-shielding.</p>
          </div>
          <div className="formula">{`J(>E)  = J10 · (E/10)^-γ        γ = log10(J10 / J100)
Ḣ_SEP  = 4π · J(>E_cut) · S(E_cut) · 1.602e-10 Gy·g/MeV · Q
Ḣ_GCR  = 1.84 mSv/day × location factor   (MSL/RAD cruise)
Q = 1.5`}</div>
        </Card>
        <Card title="Risk score and status" icon={LuFlaskConical}>
          <div className="formula">{`flux      0.3 × log10(J10)          10 pfu → 0.3, 100 pfu → 0.6
imminent  warning 0.45 · alert 0.70
forecast  0.6 × P(SEP 24 h), max 0.55
dose      0.3 × cabin rate / budget rate
score     max(components)`}</div>
          <div className="prose">
            <p>Safe below {d.limits.caution}, Caution Needed below {d.limits.action}, Action Needed above.
              A status steps down only after 60 minutes below its threshold. The daily budget of
              {" "}{d.limits.daily_budget_mSv} mSv is NASA's 30-day blood-forming-organ limit
              ({d.limits.bfo_30d_mGyEq} mGy-Eq) spread over 30 days; the career limit is {d.limits.career_mSv} mSv.</p>
          </div>
        </Card>
      </div>
    </>
  );
}
