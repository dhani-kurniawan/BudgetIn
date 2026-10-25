/**
 * Perkecil & kompres foto (maks. sisi 1600px, JPEG) sebelum di-scan/diunggah.
 * Foto kamera HP bisa 5-10 MB; hasilnya biasanya < 500 KB, tetap terbaca untuk struk.
 */
export async function compressImage(file, { maxSide = 1600, quality = 0.82 } = {}) {
  if (!file || !file.type?.startsWith("image/")) throw new Error("File harus berupa gambar");

  const bitmap = await loadBitmap(file);
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale);
  const h = Math.round(bitmap.height * scale);

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff"; // PNG transparan -> latar putih
  ctx.fillRect(0, 0, w, h);
  ctx.drawImage(bitmap, 0, 0, w, h);
  bitmap.close?.();

  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
  if (!blob) throw new Error("Gagal memproses gambar");
  const base = (file.name || "bon").replace(/\.[^.]+$/, "");
  return new File([blob], `${base}.jpg`, { type: "image/jpeg" });
}

async function loadBitmap(file) {
  try {
    return await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    // Fallback untuk browser lama
    return await new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("Format gambar tidak didukung")); };
      img.src = url;
    });
  }
}
