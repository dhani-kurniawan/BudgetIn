import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/pencatatan_keuangan",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Koneksi DB tetap sehat untuk database serverless/hosting (idle bisa memutus koneksi)
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    if os.getenv("DB_SSL", "").lower() in ("1", "true", "yes"):
        import certifi

        # Wajib untuk database cloud seperti TiDB Cloud
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"ssl": {"ca": os.getenv("DB_SSL_CA", certifi.where())}}

    # Domain frontend yang boleh memanggil API (pisahkan dengan koma). "*" = semua (cukup untuk demo)
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)  # token login berlaku 12 jam

    # --- Email (verifikasi & reset password) ---
    # SMTP kosong = mode pengembangan: isi email (beserta tautannya) dicetak di terminal backend.
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_SECURITY = os.getenv("SMTP_SECURITY", "starttls").lower()  # starttls | ssl | none
    MAIL_FROM = os.getenv("MAIL_FROM", "") or os.getenv("SMTP_USER", "") or "noreply@budgetin.local"
    # Wajib verifikasi email sebelum login? Kosong = otomatis aktif kalau SMTP sudah diatur
    _req = os.getenv("REQUIRE_EMAIL_VERIFICATION", "").lower()
    REQUIRE_EMAIL_VERIFICATION = (_req in ("1", "true", "yes")) if _req else bool(os.getenv("SMTP_HOST", ""))
    VERIFY_TOKEN_HOURS = 24
    RESET_TOKEN_MINUTES = 30

    # Scan bon dengan AI (opsional). Kosong = pakai OCR di browser (Tesseract.js)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    # Upload (foto profil maks. 3 MB, foto bon maks. 5 MB; batas keras request 6 MB)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024

    # Retensi data transaksi (tahun)
    TRANSACTION_RETENTION_YEARS = 3
