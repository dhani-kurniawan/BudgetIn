"""Buat semua tabel + kategori bawaan di database yang ditunjuk DATABASE_URL.
Dipakai untuk database online (mis. TiDB Cloud). Aman dijalankan berulang kali.

    python init_db.py
"""
from app import create_app

create_app()  # ensure_schema() dijalankan otomatis saat aplikasi dibuat
print("Database siap.")
