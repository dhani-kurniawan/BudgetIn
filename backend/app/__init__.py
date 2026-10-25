import os
import re

from flask import Flask, send_from_directory, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()
jwt = JWTManager()

WEAK_SECRETS = {
    "dev-secret-change-me",
    "ganti-dengan-kunci-rahasia-yang-panjang-dan-acak",
    "isi-teks-acak-yang-panjang",
}
PROFILE_FILE_RE = re.compile(r"^user_\d+_[0-9a-f]{12}\.(jpg|png|webp)$")


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # --- Kunci JWT: yang lemah/bawaan memungkinkan orang lain memalsukan token login ---
    secret = app.config["JWT_SECRET_KEY"]
    if secret in WEAK_SECRETS or len(secret) < 16:
        if os.getenv("FLASK_ENV") == "development":
            app.logger.warning("JWT_SECRET_KEY masih lemah. Ganti dengan teks acak yang panjang sebelum dipakai publik.")
        else:
            raise RuntimeError("JWT_SECRET_KEY belum diatur atau terlalu lemah (minimal 16 karakter acak).")

    db.init_app(app)
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def token_revoked(_header, payload):
        """Token yang terbit sebelum password terakhir diganti dianggap tidak berlaku."""
        from datetime import timezone
        from app.models import User

        user = db.session.get(User, int(payload["sub"]))
        if user is None:
            return True
        changed = user.password_changed_at
        return bool(changed and payload["iat"] < int(changed.replace(tzinfo=timezone.utc).timestamp()))
    CORS(app, origins=app.config["CORS_ORIGINS"])

    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "profile"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "receipts"), exist_ok=True)

    @app.route("/api/uploads/profile/<filename>")
    def profile_photo(filename):
        # Hanya nama file hasil upload kita sendiri yang boleh dilayani (cegah path traversal)
        if not PROFILE_FILE_RE.match(filename):
            abort(404)
        return send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"], "profile"), filename)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "Ukuran file terlalu besar"}), 413

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify({"error": e.name}), e.code

    @app.errorhandler(Exception)
    def unhandled(e):
        app.logger.exception("Kesalahan tidak terduga")  # detail hanya di log server
        return jsonify({"error": "Terjadi kesalahan pada server"}), 500

    from app.routes.auth import auth_bp
    from app.routes.categories import categories_bp
    from app.routes.transactions import transactions_bp
    from app.routes.targets import targets_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.scan import scan_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(targets_bp, url_prefix="/api/targets")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(scan_bp, url_prefix="/api/scan")

    from app.schema_sync import ensure_schema

    ensure_schema(app)
    return app
