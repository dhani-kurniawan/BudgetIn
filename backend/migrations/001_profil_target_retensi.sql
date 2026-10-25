-- Migrasi untuk database yang SUDAH dibuat dari schema.sql versi lama.
-- (Instalasi baru cukup pakai schema.sql terbaru, tidak perlu file ini.)
-- Jalankan sekali saja lewat HeidiSQL pada database pencatatan_keuangan.

USE pencatatan_keuangan;

ALTER TABLE users
  ADD COLUMN username VARCHAR(50) NULL UNIQUE AFTER password_hash,
  ADD COLUMN phone VARCHAR(30) NULL AFTER username,
  ADD COLUMN profile_photo VARCHAR(255) NULL AFTER phone,
  ADD COLUMN last_login DATETIME NULL AFTER profile_photo;

-- Isi username untuk user lama dari bagian depan email
UPDATE users SET username = CONCAT(SUBSTRING_INDEX(email, '@', 1), id) WHERE username IS NULL;

ALTER TABLE targets
  ADD COLUMN category_id INT NULL AFTER period_end,
  ADD COLUMN note VARCHAR(255) NULL AFTER category_id,
  ADD CONSTRAINT fk_targets_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

CREATE INDEX idx_tx_user_date ON transactions (user_id, transaction_date);
