-- Migrasi: pengelompokan pengeluaran per sumber dana (Gaji, Bonus, dst).
-- Hanya untuk database yang SUDAH ada. Instalasi baru cukup memakai schema.sql terbaru.
-- Jalankan sekali lewat HeidiSQL pada database pencatatan_keuangan.

USE pencatatan_keuangan;

ALTER TABLE transactions
  ADD COLUMN source_id INT NULL AFTER category_id,
  ADD CONSTRAINT fk_tx_source FOREIGN KEY (source_id) REFERENCES categories(id) ON DELETE SET NULL;

-- Pengeluaran lama otomatis berstatus "Belum dikelompokkan" (source_id NULL).
-- Silakan atur sumber dananya lewat tombol edit di halaman Transaksi.
