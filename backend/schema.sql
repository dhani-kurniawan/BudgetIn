-- Skema database Web Pencatatan Keuangan
-- Jalankan: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS pencatatan_keuangan
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE pencatatan_keuangan;

-- ============================================
-- Tabel users
-- ============================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(50) NULL UNIQUE,
    phone VARCHAR(30) NULL,
    profile_photo VARCHAR(255) NULL,          -- nama file di backend/uploads/profile
    last_login DATETIME NULL,                 -- disimpan dalam UTC
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    password_changed_at DATETIME NULL,        -- token login sebelum waktu ini tidak berlaku
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Tabel categories
-- is_default = kategori bawaan sistem (tampil ke semua user)
-- user_id NULL untuk kategori bawaan, diisi untuk kategori buatan user
-- ============================================
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    name VARCHAR(100) NOT NULL,
    type ENUM('income', 'expense') NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Tabel transactions
-- Menyimpan nominal asli (amount, currency_code) dan hasil konversi
-- ke rupiah (amount_idr) supaya dashboard & evaluasi target tetap
-- sederhana (semua kalkulasi pakai amount_idr).
-- ============================================
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    source_id INT NULL,                       -- sumber dana (kategori pemasukan) untuk pengeluaran
    type ENUM('income', 'expense') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,          -- nominal asli
    currency_code CHAR(3) NOT NULL DEFAULT 'IDR',
    exchange_rate DECIMAL(15, 6) NOT NULL DEFAULT 1,  -- kurs ke IDR saat input
    amount_idr DECIMAL(15, 2) NOT NULL,      -- amount * exchange_rate
    transaction_date DATE NOT NULL,
    note VARCHAR(255),
    receipt_image VARCHAR(255) NULL,          -- nama file foto bon (uploads/receipts/<user_id>/)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (source_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_tx_user_date (user_id, transaction_date)
);

-- ============================================
-- Tabel targets
-- type: expense_limit (batas pengeluaran per periode)
--       savings (target tabungan)
-- ============================================
CREATE TABLE targets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('expense_limit', 'savings') NOT NULL,
    name VARCHAR(100) NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    category_id INT NULL,                     -- opsional, khusus expense_limit
    note VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- ============================================
-- Kategori bawaan (contoh awal, bisa ditambah)
-- ============================================
INSERT INTO categories (user_id, name, type, is_default) VALUES
    (NULL, 'Makan', 'expense', TRUE),
    (NULL, 'Transport', 'expense', TRUE),
    (NULL, 'Tagihan', 'expense', TRUE),
    (NULL, 'Hiburan', 'expense', TRUE),
    (NULL, 'Belanja', 'expense', TRUE),
    (NULL, 'Kesehatan', 'expense', TRUE),
    (NULL, 'Lainnya', 'expense', TRUE),
    (NULL, 'Gaji', 'income', TRUE),
    (NULL, 'Bonus', 'income', TRUE),
    (NULL, 'Lainnya', 'income', TRUE);


-- Token sekali pakai untuk verifikasi email & reset password (yang disimpan hanya hash-nya)
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
