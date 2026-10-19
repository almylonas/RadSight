// Score gauge and sparkline.
const STATUS_COLOR = { safe: "var(--safe)", caution: "var(--caution)", action: "var(--action)" };

function arc(cx, cy, r, a0, a1) {
  const p = (a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  const [x0, y0] = p(a0);
  const [x1, y1] = p(a1);
  return `M${x0},${y0} A${r},${r} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${x1},${y1}`;
}

export function ScoreGauge({ score, caution = 0.3, action = 0.6, size = 190 }) {
  const cx = size / 2, cy = size * 0.56, r = size * 0.4;
  const a = (v) => Math.PI + v * Math.PI;
  const segs = [[0, caution, "var(--safe)"], [caution, action, "var(--caution)"], [action, 1, "var(--action)"]];
  const needle = a(Math.min(Math.max(score, 0), 1));
  return (
    <svg viewBox={`0 0 ${size} ${size * 0.66}`} width={size} role="img"
      aria-label={`Risk score ${score.toFixed(2)}`}>
      {segs.map(([s, e, c]) => (
        <path key={s} d={arc(cx, cy, r, a(s) + 0.012, a(e) - 0.012)} stroke={c} strokeWidth="10"
          fill="none" strokeOpacity={score >= s && score < e + (e === 1 ? 0.01 : 0) ? 1 : 0.28} strokeLinecap="butt" />
      ))}
      {[0, caution, action, 1].map((v) => (
        <text key={v} x={cx + (r + 16) * Math.cos(a(v))} y={cy + (r + 16) * Math.sin(a(v)) + 4}
          textAnchor="middle" fill="var(--subtle)" fontSize="10" fontFamily="var(--mono)">{v}</text>
      ))}
      <line x1={cx} y1={cy} x2={cx + (r - 4) * Math.cos(needle)} y2={cy + (r - 4) * Math.sin(needle)}
        stroke="var(--fg)" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="5" fill="var(--fg)" />
    </svg>
  );
}

export function Sparkline({ data, end, color = "var(--brand)", width = 120, height = 32, log = false }) {
  const n = end != null ? end + 1 : data.length;
  const vals = data.slice(Math.max(0, n - 72), n).map((v) => (log ? Math.log10(Math.max(v, 1e-9)) : v));
  if (vals.length < 2) return null;
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const span = hi - lo || 1;
  const pts = vals.map((v, i) => [(i / (vals.length - 1)) * width, height - 3 - ((v - lo) / span) * (height - 6)]);
  const d = pts.map(([px, py], i) => `${i ? "L" : "M"}${px.toFixed(1)},${py.toFixed(1)}`).join("");
  const [lx, ly] = pts[pts.length - 1];
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <path d={`${d}L${width},${height}L0,${height}Z`} fill={color} opacity="0.12" />
      <path d={d} fill="none" stroke={color} strokeWidth="1.6" />
      <circle cx={lx} cy={ly} r="2.6" fill={color} />
    </svg>
  );
}

export { STATUS_COLOR };
