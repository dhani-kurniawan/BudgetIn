import hashlib
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required
from app import db
from app.models import User, AuthToken
from app.mailer import send_verification_email, send_reset_email
from app.utils import current_user_id, purge_old_transactions, read_image_upload, upload_dir, RateLimiter, json_body

auth_bp = Blueprint("auth", __name__)

login_limiter = RateLimiter(limit=8, window_seconds=15 * 60)  # maks. 8 kali gagal / 15 menit per email+IP
mail_limiter = RateLimiter(limit=3, window_seconds=3600)  # maks. 3 email (reset/verifikasi) per jam per alamat
mail_ip_limiter = RateLimiter(limit=15, window_seconds=3600)  # dan 15 permintaan per jam per IP
token_limiter = RateLimiter(limit=20, window_seconds=3600)  # percobaan token salah per IP
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,30}$")


def serialize_user(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "profile_photo": user.profile_photo,
        "photo_url": f"/uploads/profile/{user.profile_photo}" if user.profile_photo else None,
        "last_login": user.last_login.isoformat() + "Z" if user.last_login else None,
        "email_verified": bool(user.email_verified),
    }


# ---------- Token verifikasi email / reset password ----------
def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _issue_token(user, purpose, ttl: timedelta) -> str:
    """Buat token acak. Token lama untuk tujuan yang sama dibatalkan. Yang disimpan hanya hash-nya."""
    AuthToken.query.filter_by(user_id=user.id, purpose=purpose, used_at=None).delete()
    raw = secrets.token_urlsafe(32)
    db.session.add(AuthToken(user_id=user.id, purpose=purpose, token_hash=_hash(raw), expires_at=datetime.utcnow() + ttl))
    db.session.commit()
    return raw


def _consume_token(raw, purpose):
    """Return AuthToken yang valid (belum dipakai, belum kedaluwarsa) atau None."""
    if not isinstance(raw, str) or not (20 <= len(raw) <= 100):
        return None
    tok = AuthToken.query.filter_by(token_hash=_hash(raw), purpose=purpose).first()
    if not tok or tok.used_at or tok.expires_at < datetime.utcnow():
        return None
    return tok


def _send_verification(user):
    hours = current_app.config["VERIFY_TOKEN_HOURS"]
    raw = _issue_token(user, "verify_email", timedelta(hours=hours))
    send_verification_email(user, f"{current_app.config['FRONTEND_URL']}/verify-email?token={raw}", hours)


def _client_ip():
    return request.remote_addr or "-"


def _unique_username(base: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_.]", "", base)[:24] or "user"
    if len(base) < 3:
        base = base + "user"
    candidate, n = base, 1
    while User.query.filter_by(username=candidate).first():
        n += 1
        candidate = f"{base}{n}"
    return candidate


@auth_bp.route("/register", methods=["POST"])
def register():
    data = json_body()
    name = data.get("name") if isinstance(data.get("name"), str) else ""
    name = name.strip()
    email = data.get("email") if isinstance(data.get("email"), str) else ""
    email = email.strip().lower()
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "name, email, dan password wajib diisi"}), 400
    if not isinstance(password, str):
        return jsonify({"error": "Data tidak valid"}), 400
    if len(name) > 100 or len(email) > 150 or not EMAIL_RE.match(email):
        return jsonify({"error": "Nama/email tidak valid"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password minimal 8 karakter"}), 400
    if len(password.encode("utf-8")) > 72:
        return jsonify({"error": "Password terlalu panjang (maksimal 72 byte)"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email sudah terdaftar"}), 409

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        username=_unique_username(email.split("@")[0]),
    )
    db.session.add(user)
    db.session.commit()
    _send_verification(user)

    return jsonify({
        "message": "Registrasi berhasil. Kami mengirim email verifikasi, cek inbox (atau folder spam).",
        "user_id": user.id,
        "verification_required": bool(current_app.config["REQUIRE_EMAIL_VERIFICATION"]),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = json_body()
    email = data.get("email") if isinstance(data.get("email"), str) else ""
    email = email.strip().lower()
    password = data.get("password") or ""

    if not isinstance(password, str):
        return jsonify({"error": "Email atau password salah"}), 401

    limiter_key = f"{request.remote_addr}|{email}"
    if login_limiter.blocked(limiter_key):
        return jsonify({"error": "Terlalu banyak percobaan login. Coba lagi dalam 15 menit."}), 429

    user = User.query.filter_by(email=email).first()
    if (
        not user
        or len(password.encode("utf-8")) > 72
        or not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
    ):
        login_limiter.hit(limiter_key)
        return jsonify({"error": "Email atau password salah"}), 401

    login_limiter.reset(limiter_key)
    if current_app.config["REQUIRE_EMAIL_VERIFICATION"] and not user.email_verified:
        return jsonify({
            "error": "Email kamu belum diverifikasi. Cek inbox untuk tautan verifikasi.",
            "code": "EMAIL_NOT_VERIFIED",
        }), 403
    user.last_login = datetime.utcnow()
    db.session.commit()
    purge_old_transactions(user.id)  # retensi 3 tahun (termasuk foto bon)

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "user": serialize_user(user)}), 200


@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    ip = _client_ip()
    if token_limiter.blocked(ip):
        return jsonify({"error": "Terlalu banyak percobaan. Coba lagi nanti."}), 429
    tok = _consume_token(json_body().get("token"), "verify_email")
    if not tok:
        token_limiter.hit(ip)
        return jsonify({"error": "Tautan verifikasi tidak valid atau sudah kedaluwarsa. Minta tautan baru dari halaman login."}), 400
    user = db.session.get(User, tok.user_id)
    user.email_verified = True
    tok.used_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Email berhasil diverifikasi. Silakan login."}), 200


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Kirim ulang email verifikasi. Respons selalu sama agar tidak bisa dipakai menebak email yang terdaftar."""
    email = json_body().get("email")
    email = email.strip().lower() if isinstance(email, str) else ""
    generic = jsonify({"message": "Jika email terdaftar dan belum diverifikasi, tautan verifikasi baru sudah dikirim."}), 200
    ip = _client_ip()
    if not EMAIL_RE.match(email) or mail_ip_limiter.blocked(ip) or mail_limiter.blocked(email):
        return generic
    mail_ip_limiter.hit(ip)
    mail_limiter.hit(email)
    user = User.query.filter_by(email=email).first()
    if user and not user.email_verified:
        _send_verification(user)
    return generic


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Minta tautan reset password. Respons selalu sama (tidak membocorkan apakah email terdaftar)."""
    email = json_body().get("email")
    email = email.strip().lower() if isinstance(email, str) else ""
    generic = jsonify({"message": "Jika email terdaftar, tautan untuk mengatur ulang password sudah dikirim. Cek inbox atau folder spam."}), 200
    ip = _client_ip()
    if not EMAIL_RE.match(email) or mail_ip_limiter.blocked(ip) or mail_limiter.blocked(email):
        return generic
    mail_ip_limiter.hit(ip)
    mail_limiter.hit(email)
    user = User.query.filter_by(email=email).first()
    if user:
        minutes = current_app.config["RESET_TOKEN_MINUTES"]
        raw = _issue_token(user, "reset_password", timedelta(minutes=minutes))
        send_reset_email(user, f"{current_app.config['FRONTEND_URL']}/reset-password?token={raw}", minutes)
    return generic


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = json_body()
    ip = _client_ip()
    if token_limiter.blocked(ip):
        return jsonify({"error": "Terlalu banyak percobaan. Coba lagi nanti."}), 429
    password = data.get("password")
    if not isinstance(password, str) or len(password) < 8:
        return jsonify({"error": "Password baru minimal 8 karakter"}), 400
    if len(password.encode("utf-8")) > 72:
        return jsonify({"error": "Password terlalu panjang (maksimal 72 byte)"}), 400

    tok = _consume_token(data.get("token"), "reset_password")
    if not tok:
        token_limiter.hit(ip)
        return jsonify({"error": "Tautan reset tidak valid atau sudah kedaluwarsa. Minta tautan baru."}), 400

    user = db.session.get(User, tok.user_id)
    user.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user.password_changed_at = datetime.utcnow()  # semua token login lama dicabut
    user.email_verified = True  # sudah terbukti menerima email di alamat ini
    tok.used_at = datetime.utcnow()
    AuthToken.query.filter_by(user_id=user.id, purpose="reset_password", used_at=None).delete()
    db.session.commit()
    login_limiter.reset(f"{ip}|{user.email}")
    return jsonify({"message": "Password berhasil diubah. Silakan login dengan password baru."}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = db.session.get(User, current_user_id())
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404
    return jsonify(serialize_user(user)), 200


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_me():
    user = db.session.get(User, current_user_id())
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404
    data = json_body()
    email_changed = False
    password_changed = False

    if "name" in data:
        name = str(data["name"] or "").strip()
        if not name or len(name) > 100:
            return jsonify({"error": "Nama wajib diisi (maksimal 100 karakter)"}), 400
        user.name = name

    if "username" in data:
        username = str(data["username"] or "").strip()
        if not USERNAME_RE.match(username):
            return jsonify({"error": "Username 3-30 karakter (huruf, angka, titik, underscore)"}), 400
        taken = User.query.filter(User.username == username, User.id != user.id).first()
        if taken:
            return jsonify({"error": "Username sudah dipakai"}), 409
        user.username = username

    if "email" in data:
        email = str(data["email"] or "").strip().lower()
        if len(email) > 150 or not EMAIL_RE.match(email):
            return jsonify({"error": "Format email tidak valid"}), 400
        taken = User.query.filter(User.email == email, User.id != user.id).first()
        if taken:
            return jsonify({"error": "Email sudah terdaftar"}), 409
        if email != user.email:
            user.email = email
            user.email_verified = False
            email_changed = True

    if "phone" in data:
        user.phone = str(data["phone"] or "").strip()[:30] or None

    new_password = data.get("new_password")
    if new_password:
        current = data.get("current_password") or ""
        if not isinstance(current, str) or len(current.encode("utf-8")) > 72 or not bcrypt.checkpw(current.encode("utf-8"), user.password_hash.encode("utf-8")):
            return jsonify({"error": "Password saat ini salah"}), 400
        if not isinstance(new_password, str) or len(new_password) < 8:
            return jsonify({"error": "Password baru minimal 8 karakter"}), 400
        if len(new_password.encode("utf-8")) > 72:
            return jsonify({"error": "Password terlalu panjang (maksimal 72 byte)"}), 400
        user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.password_changed_at = datetime.utcnow()  # sesi/token lama di perangkat lain jadi tidak berlaku
        password_changed = True

    db.session.commit()
    if email_changed:
        _send_verification(user)
    body = serialize_user(user)
    if password_changed:
        body["access_token"] = create_access_token(identity=str(user.id))  # token baru untuk sesi ini
    return jsonify(body), 200


def _photo_dir():
    return upload_dir("profile")


def _remove_photo_file(filename):
    if not filename:
        return
    path = os.path.join(_photo_dir(), os.path.basename(filename))
    if os.path.isfile(path):
        os.remove(path)


@auth_bp.route("/me/photo", methods=["POST"])
@jwt_required()
def upload_photo():
    user = db.session.get(User, current_user_id())
    file = request.files.get("photo")
    if not file or not file.filename:
        return jsonify({"error": "File foto tidak ditemukan"}), 400

    # Jenis file ditentukan dari ISI file (bukan dari nama/header), SVG ditolak
    data, ext, err = read_image_upload(file, 3 * 1024 * 1024)
    if err:
        return jsonify({"error": err}), 400

    filename = f"user_{user.id}_{uuid.uuid4().hex[:12]}.{ext}"
    with open(os.path.join(_photo_dir(), filename), "wb") as f:
        f.write(data)

    _remove_photo_file(user.profile_photo)
    user.profile_photo = filename
    db.session.commit()
    return jsonify(serialize_user(user)), 200


@auth_bp.route("/me/photo", methods=["DELETE"])
@jwt_required()
def delete_photo():
    user = db.session.get(User, current_user_id())
    _remove_photo_file(user.profile_photo)
    user.profile_photo = None
    db.session.commit()
    return jsonify(serialize_user(user)), 200
