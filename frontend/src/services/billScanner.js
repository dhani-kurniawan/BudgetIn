import api from "./api";
import { compressImage } from "../utils/image";
import { parseReceiptText } from "./receiptParser";

/** "claude" = dibaca server dengan AI (butuh API key), "browser" = OCR di browser. */
async function getEngine() {
  try {
    const { data } = await api.get("/scan/engine");
    return data.engine;
  } catch {
    return "browser";
  }
}

async function browserOcr(file, onProgress) {
  // Dimuat hanya saat dibutuhkan (library cukup besar); data bahasa diunduh sekali lalu di-cache browser
  const { createWorker } = await import("tesseract.js");
  const worker = await createWorker(["ind", "eng"], 1, {
    logger: (m) => {
      if (m.status === "recognizing text") onProgress?.(Math.round(m.progress * 100));
    },
  });
  try {
    const { data } = await worker.recognize(file);
    return parseReceiptText(data.text);
  } finally {
    await worker.terminate();
  }
}

/**
 * Baca foto bon. Hasil: { file, engine, amount, currency, date, note, category_id?, category_name? }
 * `file` adalah foto yang sudah dikompres (dipakai juga sebagai lampiran transaksi).
 */
export async function scanBill(rawFile, onProgress) {
  const file = await compressImage(rawFile);
  const engine = await getEngine();

  if (engine === "claude") {
    try {
      const fd = new FormData();
      fd.append("image", file);
      const { data } = await api.post("/scan/bill", fd);
      return { ...data, file };
    } catch (err) {
      if (err.response?.status === 429) throw new Error(err.response.data.error);
      // gagal di server (jaringan/kuota) -> coba OCR di browser
    }
  }
  const parsed = await browserOcr(file, onProgress);
  return { ...parsed, engine: "browser", is_receipt: true, file };
}
