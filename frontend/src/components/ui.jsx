export function Card({ title, sub, icon: Icon, actions, children, foot, className = "", bodyClass = "" }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="card-head">
          <div style={{ minWidth: 0 }}>
            {title && <h3 className="card-title">{Icon && <Icon size={15} />}{title}</h3>}
            {sub && <p className="card-sub">{sub}</p>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      <div className={`card-body ${bodyClass}`}>{children}</div>
      {foot && <footer className="card-foot">{foot}</footer>}
    </section>
  );
}

export function Badge({ tone = "", dot = false, children, className = "" }) {
  return (
    <span className={`badge ${tone} ${className}`}>
      {dot && <span className="dot" />}
      {children}
    </span>
  );
}

export function Meter({ label, value, max, display, ticks = [], color = "var(--brand)", thin }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="meter">
      {(label || display) && (
        <div className="meter-top"><span>{label}</span><b>{display}</b></div>
      )}
      <div className={`track ${thin ? "thin" : ""}`} role="meter" aria-valuenow={value} aria-valuemin={0}
        aria-valuemax={max} aria-label={label}>
        <div className="fill" style={{ width: `${pct}%`, background: color }} />
        {ticks.map((t) => <span key={t} className="tick" style={{ left: `${(t / max) * 100}%` }} />)}
      </div>
    </div>
  );
}

export function PageHead({ title, sub, children }) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {children}
    </div>
  );
}

export function statusColor(s) {
  return s === "action" ? "var(--action)" : s === "caution" ? "var(--caution)" : "var(--safe)";
}

export function scoreColor(v, caution = 0.3, action = 0.6) {
  return v >= action ? "var(--action)" : v >= caution ? "var(--caution)" : "var(--safe)";
}
