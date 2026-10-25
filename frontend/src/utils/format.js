export const CURRENCIES = ["IDR", "USD", "EUR", "SGD", "MYR", "JPY", "GBP", "AUD", "CNY", "SAR", "KRW", "THB"];

export const CURRENCY_SYMBOLS = {
  IDR: "Rp", USD: "$", EUR: "€", SGD: "S$", MYR: "RM", JPY: "¥", GBP: "£",
  AUD: "A$", CNY: "CN¥", SAR: "SR", KRW: "₩", THB: "฿",
};
export const CURRENCY_NAMES = {
  IDR: "Rupiah", USD: "Dolar AS", EUR: "Euro", SGD: "Dolar Singapura", MYR: "Ringgit Malaysia", JPY: "Yen Jepang",
  GBP: "Poundsterling", AUD: "Dolar Australia", CNY: "Yuan Tiongkok", SAR: "Riyal Saudi", KRW: "Won Korea", THB: "Baht Thailand",
};
export const currencySymbol = (code) => CURRENCY_SYMBOLS[code] || code;
export const currencyName = (code) => CURRENCY_NAMES[code] || code;

export function formatNumber(value, digits = 0) {
  return new Intl.NumberFormat("id-ID", { maximumFractionDigits: digits }).format(value ?? 0);
}

export function formatRupiah(value) {
  return "Rp " + formatNumber(Math.round(value ?? 0));
}

/** Format ringkas untuk sumbu grafik: 1,5 jt / 250 rb */
export function formatCompact(value) {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${+(value / 1_000_000_000).toFixed(1)} M`;
  if (abs >= 1_000_000) return `${+(value / 1_000_000).toFixed(1)} jt`;
  if (abs >= 1_000) return `${+(value / 1_000).toFixed(0)} rb`;
  return String(value);
}

export function toISODate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function todayISO() {
  return toISODate(new Date());
}

/** Batas tanggal terlama yang diizinkan (retensi 3 tahun). */
export function retentionMinISO() {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 3);
  return toISODate(d);
}

export function formatDate(iso) {
  if (!iso) return "-";
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(iso) {
  if (!iso) return "Belum ada data";
  return new Date(iso).toLocaleString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function monthRange(offset = 0) {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth() + offset, 1);
  const end = new Date(now.getFullYear(), now.getMonth() + offset + 1, 0);
  return { start: toISODate(start), end: toISODate(end) };
}

export function initials(name = "") {
  return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0]?.toUpperCase() || "").join("") || "?";
}
