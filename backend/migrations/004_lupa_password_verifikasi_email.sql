-- Migrasi: lupa password & verifikasi email.
-- Hanya untuk database yang SUDAH ada. (Aplikasi juga menambahkan ini otomatis saat start.)
USE pencatatan_keuangan;

ALTER TABLE users
  ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN password_changed_at DATETIME NULL;

-- Akun yang sudah ada dianggap terverifikasi agar tidak terkunci
UPDATE users SET email_verified = TRUE;

CREATE TABLE IF NOT EXISTS auth_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    purpose VARCHAR(20) NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
