import { useMemo, useState } from "react";
import { useWidth } from "./useWidth";
import { dayLabel, fmt, hhmm, parseT } from "../lib/format";

const PAD = { l: 50, r: 14, t: 12, b: 26 };

function logDomain(values, min, max) {
  const pos = values.filter((v) => v > 0);
  const lo = min ?? Math.pow(10, Math.floor(Math.log10(Math.min(...pos))));
  const hi = max ?? Math.pow(10, Math.ceil(Math.log10(Math.max(...pos) * 1.05)));
  return [lo, hi === lo ? lo * 10 : hi];
}

function niceMax(v) {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  const m = v / p;
  return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p;
}

function supText(v) {
  const e = Math.round(Math.log10(v));
  if (e >= -2 && e <= 4) return fmt(v);
  return `1e${e}`;
}

/**
 * Time-series chart.
 * series: [{ key, label, data:number[], color, dash?, area? }]
 * thresholds: [{ y, label, color }]
 * bands: [{ from, to, label }] horizontal bands (e.g. X-ray classes)
 */
export default function TimeChart({
  times, series, log = false, height = 220, thresholds = [], bands = [],
  cursor, yMin, yMax, unit = "", yFormat, onPick, end,
}) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState(null);
  const n = end != null ? end + 1 : times.length;

  const all = series.flatMap((s) => s.data.slice(0, n));
  const [lo, hi] = useMemo(() => {
    if (log) return logDomain(all.concat(thresholds.map((t) => t.y)), yMin, yMax);
    return [yMin ?? 0, yMax ?? niceMax(Math.max(...all, ...thresholds.map((t) => t.y)) * 1.08)];
  }, [all.length, log, yMin, yMax, series]); // eslint-disable-line react-hooks/exhaustive-deps

  const w = width - PAD.l - PAD.r;
  const h = height - PAD.t - PAD.b;
  const total = times.length;
  const x = (i) => PAD.l + (total <= 1 ? 0 : (i / (total - 1)) * w);
  const y = (v) => {
    if (log) {
      const lv = Math.log10(Math.max(v, lo));
      return PAD.t + h - ((lv - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo))) * h;
    }
    return PAD.t + h - ((v - lo) / (hi - lo)) * h;
  };
  const clampY = (v) => Math.min(Math.max(y(v), PAD.t), PAD.t + h);

  const ticks = useMemo(() => {
    if (log) {
      const out = [];
      for (let e = Math.ceil(Math.log10(lo)); e <= Math.floor(Math.log10(hi)); e++) out.push(10 ** e);
      return out;
    }
    return [0, 0.25, 0.5, 0.75, 1].map((f) => lo + f * (hi - lo));
  }, [lo, hi, log]);

  // ticks on round UTC hours or days, as many as fit
  const xTicks = useMemo(() => {
    if (total < 2) return [0];
    const maxTicks = Math.max(2, Math.floor(w / 80));
    const stepMin = (parseT(times[1]) - parseT(times[0])) / 60000;
    const span = stepMin * (total - 1);
    const cands = [60, 120, 180, 360, 720, 1440, 2880, 4320, 10080];
    const step = cands.find((c) => span / c <= maxTicks) || cands[cands.length - 1];
    const out = [];
    times.forEach((t, i) => {
      const d = parseT(t);
      const m = d.getUTCHours() * 60 + d.getUTCMinutes();
      const day = Math.floor(d.getTime() / 86400000);
      if (step >= 1440 ? m === 0 && day % (step / 1440) === 0 : m % step === 0) out.push(i);
    });
    return out;
  }, [total, w, times]);

  const paths = series.map((s) => {
    let d = "";
    for (let i = 0; i < n; i++) d += `${i ? "L" : "M"}${x(i).toFixed(1)},${clampY(s.data[i]).toFixed(1)}`;
    const area = s.area && n > 1 ? `${d}L${x(n - 1).toFixed(1)},${PAD.t + h}L${x(0).toFixed(1)},${PAD.t + h}Z` : null;
    return { ...s, d, area };
  });

  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * width;
    const i = Math.round(((px - PAD.l) / w) * (total - 1));
    setHover(i >= 0 && i < n ? i : null);
  };
  const onClick = () => { if (hover != null && onPick) onPick(hover); };

  const yf = yFormat || ((v) => (log ? supText(v) : fmt(v)));
  const hi_ = hover;

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${width} ${height}`} height={height} role="img"
        onMouseMove={onMove} onMouseLeave={() => setHover(null)} onClick={onClick}
        style={{ cursor: onPick ? "crosshair" : "default" }}>
        <defs>
          {paths.filter((p) => p.area).map((p) => (
            <linearGradient key={p.key} id={`g-${p.key}`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor={p.color} stopOpacity="0.28" />
              <stop offset="1" stopColor={p.color} stopOpacity="0.02" />
            </linearGradient>
          ))}
        </defs>
        {bands.map((b) => (
          <g key={b.label}>
            <text x={width - PAD.r - 2} y={(clampY(b.from) + clampY(b.to)) / 2 + 4} textAnchor="end"
              className="axis-text" style={{ fontWeight: 600 }}>{b.label}</text>
          </g>
        ))}
        {ticks.map((v) => (
          <g key={v}>
            <line className="grid-line" x1={PAD.l} x2={width - PAD.r} y1={y(v)} y2={y(v)} />
            <text className="axis-text" x={PAD.l - 8} y={y(v) + 4} textAnchor="end">{yf(v)}</text>
          </g>
        ))}
        {xTicks.map((i) => {
          const label = hhmm(times[i]) === "00:00" ? dayLabel(times[i]) : hhmm(times[i]);
          const anchor = x(i) < PAD.l + 16 ? "start" : x(i) > width - PAD.r - 16 ? "end" : "middle";
          return (
            <text key={i} className="axis-text" x={x(i)} y={height - 6} textAnchor={anchor}
              style={label.length > 5 ? { fill: "var(--muted)" } : undefined}>{label}</text>
          );
        })}
        {thresholds.map((t) => (t.y > lo && t.y < hi ? (
          <g key={t.label}>
            <line x1={PAD.l} x2={width - PAD.r} y1={y(t.y)} y2={y(t.y)} stroke={t.color}
              strokeDasharray="4 4" strokeOpacity="0.7" />
            <text x={PAD.l + 6} y={y(t.y) - 5} fill={t.color} className="thr-text">{t.label}</text>
          </g>
        ) : null))}
        {paths.map((p) => p.area && <path key={`a-${p.key}`} d={p.area} fill={`url(#g-${p.key})`} />)}
        {paths.map((p) => (
          <path key={p.key} d={p.d} fill="none" stroke={p.color} strokeWidth={p.width || 1.8}
            strokeDasharray={p.dash ? "5 4" : undefined} strokeLinejoin="round" />
        ))}
        {n < total && (
          <rect x={x(n - 1)} y={PAD.t} width={Math.max(x(total - 1) - x(n - 1), 0)} height={h}
            fill="var(--panel-2)" opacity="0.55" />
        )}
        {cursor != null && (
          <g>
            <line x1={x(cursor)} x2={x(cursor)} y1={PAD.t} y2={PAD.t + h} stroke="var(--fg)" strokeOpacity="0.5" />
            {paths.map((p) => (
              <circle key={p.key} cx={x(cursor)} cy={clampY(p.data[cursor])} r="3.5" fill={p.color}
                stroke="var(--panel)" strokeWidth="1.5" />
            ))}
          </g>
        )}
        {hi_ != null && (
          <line x1={x(hi_)} x2={x(hi_)} y1={PAD.t} y2={PAD.t + h} stroke="var(--brand-fg)" strokeOpacity="0.6" strokeDasharray="2 3" />
        )}
      </svg>
      {hi_ != null && (
        <div className="chart-tip" style={{
          left: Math.min(Math.max((x(hi_) / width) * 100, 0), 100) + "%",
          top: 6,
          transform: `translateX(${x(hi_) > width * 0.6 ? "calc(-100% - 10px)" : "10px"})`,
        }}>
          <div className="t">{dayLabel(times[hi_])} {hhmm(times[hi_])} UTC</div>
          {series.map((s) => (
            <div className="r" key={s.key}>
              <span><i style={{ width: 8, height: 8, borderRadius: 2, background: s.color, display: "inline-block" }} />{s.label}</span>
              <span className="num">{s.fmt ? s.fmt(s.data[hi_]) : fmt(s.data[hi_])}{unit && ` ${unit}`}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function Legend({ series }) {
  return (
    <div className="legend">
      {series.map((s) => (
        <span key={s.key} style={{ color: s.color }}>
          <i className={s.dash ? "dash" : ""} style={{ background: s.color }} />
          <span style={{ color: "var(--muted)" }}>{s.label}</span>
        </span>
      ))}
    </div>
  );
}
