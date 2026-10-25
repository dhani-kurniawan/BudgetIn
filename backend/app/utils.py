import math
import os
import threading
import time
from datetime import date, datetime, timedelta

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity

MAX_AMOUNT = 9_999_999_999_999.0  # batas kolom DECIMAL(15,2) dengan sisa aman


def json_body() -> dict:
    """Body JSON sebagai dict. Body yang bukan objek JSON dianggap kosong (bukan error 500)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def current_user_id() -> int:
    """Identity JWT disimpan sebagai string (syarat library JWT terbaru)."""
    return int(get_jwt_identity())


def retention_cutoff() -> date:
    years = current_app.config.get("TRANSACTION_RETENTION_YEARS", 3)
    today = date.today()
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # 29 Februari
        return today.replace(year=today.year - years, day=28)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def date_arg(name):
    """Ambil query param tanggal (YYYY-MM-DD). Return (date_iso | None, error | None)."""
    raw = request.args.get(name)
    if not raw:
        return None, None
    try:
        return parse_date(raw).isoformat(), None
    except ValueError:
        return None, f"Parameter {name} harus berformat YYYY-MM-DD"


def finite_number(value, minimum=0.0, maximum=MAX_AMOUNT):
    """Konversi ke float yang valid (bukan NaN/Infinity, > minimum, <= maximum). None kalau tidak valid."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v <= minimum or v > maximum:
        return None
    return v


# ---------- Upload gambar ----------
def detect_image_ext(data: bytes):
    """Cek jenis gambar dari isi file (magic bytes), bukan dari nama/header yang bisa dipalsukan."""
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def read_image_upload(file_storage, max_bytes):
    """Return (bytes, ext, error)."""
    data = file_storage.read(max_bytes + 1)
    if len(data) > max_bytes:
        return None, None, f"Ukuran gambar maksimal {max_bytes // (1024 * 1024)} MB"
    ext = detect_image_ext(data)
    if not ext:
        return None, None, "File harus berupa gambar JPG, PNG, atau WEBP"
    return data, ext, None


def upload_dir(*parts):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], *parts)


def receipt_dir(user_id):
    d = upload_dir("receipts", str(int(user_id)))
    os.makedirs(d, exist_ok=True)
    return d


def delete_receipt_file(user_id, filename):
    if not filename:
        return
    path = os.path.join(upload_dir("receipts", str(int(user_id))), os.path.basename(filename))
    if os.path.isfile(path):
        os.remove(path)


# ---------- Retensi ----------
def purge_old_transactions(user_id) -> int:
    """Hapus transaksi (beserta foto bonnya) yang lebih lama dari batas retensi."""
    from app import db
    from app.models import Transaction

    old = Transaction.query.filter(
        Transaction.user_id == user_id, Transaction.transaction_date < retention_cutoff()
    ).all()
    for t in old:
        delete_receipt_file(user_id, t.receipt_image)
        db.session.delete(t)
    if old:
        db.session.commit()
    return len(old)


# ---------- Pembatas laju sederhana (di memori) ----------
class RateLimiter:
    def __init__(self, limit, window_seconds):
        self.limit, self.window = limit, window_seconds
        self._hits, self._lock = {}, threading.Lock()

    def _recent(self, key):
        now = time.time()
        hits = [t for t in self._hits.get(key, []) if now - t < self.window]
        self._hits[key] = hits
        return hits

    def blocked(self, key) -> bool:
        with self._lock:
            return len(self._recent(key)) >= self.limit

    def hit(self, key):
        with self._lock:
            self._recent(key).append(time.time())

    def reset(self, key):
        with self._lock:
            self._hits.pop(key, None)
