"""Sinkronisasi struktur database saat aplikasi start.

Kalau kamu menarik kode versi baru tetapi lupa menjalankan file migrasi SQL, kolom baru
(mis. transactions.source_id) otomatis ditambahkan di sini, jadi tidak muncul error
"Unknown column ...". Hanya MENAMBAH tabel/kolom yang belum ada; tidak pernah menghapus data.
"""
from sqlalchemy import inspect, text

from app import db

DEFAULT_CATEGORIES = [
    ("Makan", "expense"), ("Transport", "expense"), ("Tagihan", "expense"),
    ("Hiburan", "expense"), ("Belanja", "expense"), ("Kesehatan", "expense"),
    ("Lainnya", "expense"), ("Gaji", "income"), ("Bonus", "income"), ("Lainnya", "income"),
]


def ensure_schema(app):
    from app.models import Category, User

    with app.app_context():
        try:
            db.create_all()  # membuat tabel yang belum ada (tidak mengubah tabel yang sudah ada)
            insp = inspect(db.engine)
            quote = db.engine.dialect.identifier_preparer.quote
            added = []

            for table in db.metadata.sorted_tables:
                existing = {c["name"] for c in insp.get_columns(table.name)}
                for col in table.columns:
                    if col.name in existing:
                        continue
                    col_type = col.type.compile(dialect=db.engine.dialect)
                    with db.engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {quote(table.name)} ADD COLUMN {quote(col.name)} {col_type} NULL"))
                    added.append(f"{table.name}.{col.name}")

            if added:
                app.logger.warning("Database diperbarui otomatis, kolom ditambahkan: %s", ", ".join(added))

            # Pengguna lama belum punya username -> isi dari bagian depan email
            missing = User.query.filter(User.username.is_(None)).all()
            for u in missing:
                base = "".join(ch for ch in u.email.split("@")[0] if ch.isalnum() or ch in "._")[:24] or "user"
                u.username = f"{base}{u.id}"
            if missing:
                db.session.commit()
            if "users.email_verified" in added:
                # Akun yang sudah ada sebelum fitur ini dianggap terverifikasi (agar tidak terkunci)
                with db.engine.begin() as conn:
                    conn.execute(text("UPDATE users SET email_verified = 1"))
            if "users.username" in added:
                try:
                    with db.engine.begin() as conn:
                        conn.execute(text("CREATE UNIQUE INDEX uq_users_username ON users (username)"))
                except Exception:
                    pass

            # Kategori bawaan untuk database kosong
            if Category.query.filter_by(is_default=True).count() == 0:
                for name, type_ in DEFAULT_CATEGORIES:
                    db.session.add(Category(user_id=None, name=name, type=type_, is_default=True))
                db.session.commit()
        except Exception as exc:  # jangan menjatuhkan server hanya karena sinkronisasi gagal
            db.session.rollback()
            app.logger.error("Sinkronisasi struktur database gagal: %s", exc)
