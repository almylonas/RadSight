export const STATUS_LABEL = { safe: "Safe", caution: "Caution Needed", action: "Action Needed" };

export const LOCATION_LABEL = {
  cabin: "Cabin",
  shelter: "Storm shelter",
  eva: "EVA",
  habitat: "Habitat",
  surface_eva: "Surface EVA",
  surface_shelter: "Regolith shelter",
};

export const LOCATION_TONE = {
  cabin: "", habitat: "", shelter: "brand", surface_shelter: "brand",
  eva: "caution", surface_eva: "caution",
};

export const DRIVER_LABEL = {
  flux: "Proton flux",
  imminent: "Imminent event",
  forecast: "24 h forecast",
  dose: "Dose rate",
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function parseT(iso) {
  return new Date(iso.endsWith("Z") ? iso : iso + "Z");
}

export function hhmm(iso) {
  return iso.slice(11, 16);
}

export function dayLabel(iso) {
  const d = parseT(iso);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
}

export function fullTime(iso) {
  return `${dayLabel(iso)} ${parseT(iso).getUTCFullYear()} · ${hhmm(iso)} UTC`;
}

export function fmt(v, digits = 1) {
  if (v == null || Number.isNaN(v)) return "–";
  const a = Math.abs(v);
  if (a >= 1000) return Math.round(v).toLocaleString("en-US");
  if (a >= 100) return v.toFixed(0);
  if (a >= 10) return v.toFixed(Math.min(digits, 1));
  if (a >= 1) return v.toFixed(digits);
  if (a === 0) return "0";
  return v.toPrecision(2);
}

export function pct(v) {
  return `${Math.round(v)}%`;
}

export function xrayClass(flux) {
  if (!flux) return "–";
  const classes = [["X", 1e-4], ["M", 1e-5], ["C", 1e-6], ["B", 1e-7], ["A", 1e-8]];
  for (const [c, base] of classes) {
    if (flux >= base) return `${c}${(flux / base).toFixed(1)}`;
  }
  return "A0.0";
}

export function sScale(j10) {
  if (j10 >= 10000) return "S4";
  if (j10 >= 1000) return "S3";
  if (j10 >= 100) return "S2";
  if (j10 >= 10) return "S1";
  return "S0";
}

export function initials(name) {
  return name.split(" ").map((p) => p[0]).join("").slice(0, 2);
}

export function duration(min) {
  if (min == null) return "–";
  const m = Math.max(0, Math.round(min));
  if (m < 60) return `${m} min`;
  return `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`;
}
