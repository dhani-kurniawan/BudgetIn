/**
 * Ekstrak data dari teks hasil OCR struk (bahasa Indonesia / Inggris).
 * Heuristik: akurasinya bergantung kualitas foto dan OCR, jadi hasilnya selalu
 * ditampilkan di form untuk diperiksa user sebelum disimpan.
 */

const MONEY_RE = /\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?/g;

// Urutan = prioritas (yang paling pasti dulu). Hanya kata "total" yang dipercaya sebagai jumlah uang;
// "tunai/cash" sengaja tidak dipakai karena itu uang yang diserahkan, bukan total belanja.
const NOT_TOTAL = String.raw`(?!\s*(item|items|qty|barang|diskon|discount|hemat|pajak|ppn|tax|service|servis|disc))`;
const TOTAL_KEYS = [
  /grand\s*total/i,
  /total\s*(bayar|tagihan|belanja|pembayaran|akhir|harga|amount|due|price|payable)|amount\s*(due|payable)|balance\s*due|jumlah\s*(bayar|tagihan|total)|net\s*total|netto/i,
  new RegExp(String.raw`(?<!sub\s?)(?<!sub)\btotal\b` + NOT_TOTAL, "i"),
  /\bamount\b(?!\s*(paid|tendered))/i,
  /\bjumlah\b(?!\s*(item|barang|qty))/i,
];

const CATEGORY_HINTS = {
  Makan: [
    "restaurant", "restoran", "resto", "rumah makan", "food", "foods", "cafe", "café", "kafe", "coffee", "kopi", "warung", "warteg",
    "kedai", "depot", "bistro", "eatery", "diner", "kantin", "catering", "dapur", "kitchen", "bakery", "bakso", "soto", "nasi", "mie",
    "mi ayam", "ayam", "sate", "padang", "geprek", "seafood", "steak", "pizza", "burger", "sushi", "ramen", "juice", "jus", "boba",
    "chatime", "kfc", "mcd", "mcdonald", "starbucks", "dessert", "snack",
  ],
  Transport: ["spbu", "pertamina", "shell", "bensin", "pertalite", "pertamax", "parkir", "tol", "grab", "gojek", "bluebird", "kai", "tiket"],
  Belanja: ["indomaret", "alfamart", "alfa", "supermarket", "minimarket", "mart", "mall", "toko", "hypermart", "transmart", "giant", "uniqlo", "ace hardware", "miniso"],
  Kesehatan: ["apotek", "farmasi", "klinik", "rumah sakit", "kimia farma", "guardian", "k24", "century", "pharmacy"],
  Tagihan: ["pln", "pdam", "telkom", "indihome", "listrik", "pulsa", "bpjs", "internet"],
  Hiburan: ["bioskop", "xxi", "cgv", "netflix", "spotify", "game", "karaoke"],
};

/** "1.234.567" -> 1234567 ; "12,50" -> 12.5 ; "1,234.50" -> 1234.5 */
export function toNumber(str) {
  const s = String(str).trim();
  if (/^\d{1,3}(\.\d{3})+(,\d{1,2})?$/.test(s)) return parseFloat(s.replace(/\./g, "").replace(",", "."));
  if (/^\d{1,3}(,\d{3})+(\.\d{1,2})?$/.test(s)) return parseFloat(s.replace(/,/g, ""));
  if (/^\d+[.,]\d{1,2}$/.test(s)) return parseFloat(s.replace(",", "."));
  return parseFloat(s.replace(/[.,]/g, "")) || 0;
}

function numbersIn(line) {
  return (line.match(MONEY_RE) || []).map(toNumber).filter((n) => n > 0);
}

function findTotal(lines) {
  for (const key of TOTAL_KEYS) {
    const hits = [];
    lines.forEach((line, i) => {
      if (!key.test(line)) return;
      // angka bisa di baris yang sama atau baris sesudahnya (kolom struk sering terpisah)
      const nums = numbersIn(line).concat(numbersIn(lines[i + 1] || "").slice(0, 1));
      const own = numbersIn(line);
      if (own.length) hits.push(own[own.length - 1]);
      else if (nums.length) hits.push(nums[0]);
    });
    if (hits.length) return hits[hits.length - 1]; // total biasanya muncul paling bawah
  }
  return null; // tidak ada kata "total": jangan menebak, biarkan user mengisi manual
}

const MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, mei: 5, may: 5, jun: 6, jul: 7, agu: 8, aug: 8, ags: 8, sep: 9, okt: 10, oct: 10, nov: 11, des: 12, dec: 12 };

function iso(y, m, d) {
  if (y < 100) y += 2000;
  if (y < 2000 || m < 1 || m > 12 || d < 1 || d > 31) return null;
  const dt = new Date(y, m - 1, d);
  if (dt.getMonth() !== m - 1) return null;
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

export function findDate(text) {
  let m;
  if ((m = text.match(/\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b/))) return iso(+m[1], +m[2], +m[3]);
  if ((m = text.match(/\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}|\d{2})\b/))) return iso(+m[3], +m[2], +m[1]);
  if ((m = text.match(/\b(\d{1,2})\s*([A-Za-z]{3})[a-z]*\.?\s*(\d{4}|\d{2})\b/))) {
    const mon = MONTHS[m[2].toLowerCase()];
    if (mon) return iso(+m[3], mon, +m[1]);
  }
  return null;
}

function findCurrency(text) {
  if (/\bRp\b|\bIDR\b/i.test(text)) return "IDR";
  if (/\bUSD\b|US\$|\$\s?\d/.test(text)) return "USD";
  if (/\bSGD\b|S\$/.test(text)) return "SGD";
  if (/\bMYR\b|\bRM\s?\d/.test(text)) return "MYR";
  if (/\bEUR\b|€/.test(text)) return "EUR";
  if (/\bJPY\b|¥/.test(text)) return "JPY";
  return "IDR";
}

function findMerchant(lines) {
  for (const line of lines.slice(0, 6)) {
    const letters = (line.match(/[A-Za-z]/g) || []).length;
    if (letters >= 4 && letters / line.length > 0.55 && !/struk|bon|nota|invoice|receipt|kasir|tanggal|date/i.test(line)) {
      return line.replace(/\s+/g, " ").trim().slice(0, 40);
    }
  }
  return null;
}

function matchCategory(t) {
  for (const [name, words] of Object.entries(CATEGORY_HINTS)) {
    if (words.some((w) => new RegExp(`\\b${w}`).test(t))) return name;
  }
  return null;
}

// Nama toko lebih menentukan daripada isi belanja (mis. Indomaret jual roti, tetap "Belanja")
function findCategoryName(merchant, text) {
  return (merchant && matchCategory(merchant.toLowerCase())) || matchCategory(text.toLowerCase());
}

const SKIP_ITEM = /total|subtotal|sub\s*total|tunai|cash|kembali|change|ppn|pajak|tax|service|servis|diskon|discount|bayar|payment|kartu|card|debit|kredit|qris|npwp|telp|tel\b|kasir|cashier|\bno\b|nomor|tanggal|date|\bjam\b|time|struk|invoice|receipt|terima kasih|thank|alamat|jl\.|jalan|amount|paid|tendered|\bksr\b|\btgl\b|\bokt\b|pcs total/i;

/** Baris yang berbentuk "NAMA BARANG ... harga" dianggap item belanja. */
function findItems(lines) {
  const items = [];
  for (const line of lines) {
    if (SKIP_ITEM.test(line) || /\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4}/.test(line) || findDate(line)) continue;
    const nums = numbersIn(line);
    const name = line.replace(MONEY_RE, " ").replace(/[xX×@]\s*/g, " ").replace(/\s+/g, " ").replace(/[^\p{L}\p{N}\s.&'-]/gu, "").trim();
    const letters = (name.match(/\p{L}/gu) || []).length;
    if (nums.length && letters >= 4) items.push(name.slice(0, 30));
    if (items.length >= 8) break;
  }
  return items;
}

function findPayment(text) {
  if (/qris/i.test(text)) return "QRIS";
  if (/gopay|ovo|dana|shopeepay|linkaja/i.test(text)) return "E-wallet";
  if (/kredit|credit/i.test(text)) return "Kartu kredit";
  if (/debit/i.test(text)) return "Debit";
  if (/\b(tunai|cash)\b/i.test(text)) return "Tunai";
  return null;
}

export function parseReceiptText(raw) {
  const lines = String(raw || "")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  const text = lines.join("\n");
  const merchant = findMerchant(lines);
  const items = findItems(lines.slice(merchant ? 1 : 0));
  const payment = findPayment(text);
  // Semua hasil scan selain jumlah/kategori/tanggal masuk ke Catatan
  const note = [merchant, items.length ? `Item: ${items.join(", ")}` : null, payment ? `Bayar: ${payment}` : null]
    .filter(Boolean)
    .join(" | ")
    .slice(0, 255);
  return {
    amount: findTotal(lines),
    currency: findCurrency(text),
    date: findDate(text),
    note: note || null,
    category_name: findCategoryName(merchant, text),
  };
}
