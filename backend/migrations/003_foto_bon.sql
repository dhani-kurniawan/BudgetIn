-- Migrasi: foto bon/struk pada transaksi.
-- Hanya untuk database yang SUDAH ada. (Aplikasi juga menambahkan kolom ini otomatis saat start.)
USE pencatatan_keuangan;

ALTER TABLE transactions
  ADD COLUMN receipt_image VARCHAR(255) NULL AFTER note;
