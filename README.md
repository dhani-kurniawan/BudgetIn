# Budgetin — Web Pencatatan Keuangan

Flask + MySQL (backend) dan Vue.js (frontend).

---

## 1. Setup awal di komputer sendiri (Windows + Laragon)

### A. Install Laragon dan tools (sekali saja)

1. Unduh **Laragon Full** di https://laragon.org/download lalu install seperti
   biasa (lokasi default `C:\laragon`).
2. Buka Laragon. Klik kanan ikon Laragon di tray (pojok kanan bawah) →
   **Tools → Quick add**, lalu pasang **node** dan **python**.
3. Klik kanan ikon Laragon → **Terminal**, lalu cek:
   ```
   node -v
   python --version
   ```

> Selalu pakai **Terminal Laragon** (bukan CMD biasa) untuk semua perintah di bawah.

### B. Siapkan folder proyek

Ekstrak file zip proyek ke `C:\laragon\www`, sehingga foldernya menjadi
`C:\laragon\www\pencatatan-keuangan` (berisi folder `backend` dan `frontend`).

### C. Buat database

1. Di jendela Laragon klik **Start All** (tunggu MySQL berjalan).
2. Klik kanan ikon Laragon → **Database** (membuka HeidiSQL).
3. **File → Load SQL file** → pilih `backend\schema.sql` → klik **Execute**
   (ikon petir). Database `pencatatan_keuangan` akan muncul di panel kiri.

### D. Jalankan backend

Di Terminal Laragon:

```
cd C:\laragon\www\pencatatan-keuangan\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Buka `backend\.env`, isi:

```
DATABASE_URL=mysql+pymysql://root:@localhost:3306/pencatatan_keuangan
JWT_SECRET_KEY=isi-teks-acak-yang-panjang
FLASK_ENV=development
```

Lalu jalankan:

```
python run.py
```

Biarkan terminal ini tetap terbuka.

### E. Jalankan frontend

Buka **Terminal Laragon baru**:

```
cd C:\laragon\www\pencatatan-keuangan\frontend
npm install
npm run dev
```

Buka **http://localhost:5173** di browser, klik **Daftar di sini**, buat akun,
lalu login.

### F. Scan bon (opsional)

Tombol **Scan Bon** di header dan form transaksi membaca total, tanggal, dan
keterangan dari foto bon (kamera HP atau galeri).

- **Tanpa pengaturan:** dibaca langsung di browser (OCR). Butuh internet saat
  pertama kali dipakai, dan hasilnya perlu dicek lagi.
- **Lebih akurat:** isi `ANTHROPIC_API_KEY=...` di `backend\.env` (API key dari
  console.anthropic.com), lalu restart backend. Pemakaian API berbayar sesuai kuota.

### G. Email lupa password dan verifikasi (opsional)

Fitur **Lupa password?** (halaman login) dan verifikasi email mengirim tautan lewat email.

- **Tanpa pengaturan (mode uji):** email tidak benar-benar dikirim. Isinya
  (beserta tautannya) dicetak di **terminal backend**, tinggal salin tautannya ke browser.
- **Kirim email sungguhan:** isi `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
  `SMTP_PASSWORD`, dan `MAIL_FROM` di `backend\.env` (contoh Gmail ada di
  `.env.example`, pakai *App Password*), lalu restart backend.
- Verifikasi email baru **wajib** sebelum login kalau SMTP diisi. Atur manual
  dengan `REQUIRE_EMAIL_VERIFICATION=true` atau `false`.

### Lain kali mau lanjut

1. Klik **Start All** di Laragon.
2. Terminal 1: `cd C:\laragon\www\pencatatan-keuangan\backend`, lalu
   `venv\Scripts\activate`, lalu `python run.py`.
3. Terminal 2: `cd C:\laragon\www\pencatatan-keuangan\frontend`, lalu `npm run dev`.

---

## 2. Kalau mengubah kode atau database

### Upgrade dari versi sebelumnya

Kalau kamu menimpa folder proyek dengan versi baru:

1. Hentikan backend dan frontend (**Ctrl + C**).
2. Backend: `venv\Scripts\activate`, lalu `pip install -r requirements.txt`.
3. Frontend: `npm install`.
4. Jalankan lagi `python run.py` dan `npm run dev`.

Akun yang sudah ada otomatis dianggap terverifikasi.
Kolom database baru ditambahkan **otomatis** saat backend start, jadi error
`Unknown column ...` tidak lagi muncul hanya karena lupa menjalankan migrasi.

### A. Mengubah kode

| Yang diubah | Yang perlu dilakukan |
|---|---|
| File frontend (`.vue`, `.css`, `.js` di folder `frontend\src`) | Simpan file. Tampilan di browser otomatis ter-update. Kalau belum berubah, tekan **Ctrl + F5**. |
| File backend (`.py` di folder `backend\app`) | Simpan file. Server Flask otomatis restart sendiri. Kalau tidak, di terminal backend tekan **Ctrl + C**, lalu jalankan lagi `python run.py`. |
| `backend\.env` | Simpan, lalu restart backend (**Ctrl + C**, `python run.py`). |
| Menambah library backend (`requirements.txt` berubah) | Di terminal backend (venv aktif): `pip install -r requirements.txt`, lalu restart backend. |
| Menambah library frontend (`package.json` berubah) | Di terminal frontend: **Ctrl + C**, `npm install`, lalu `npm run dev`. |

Kalau muncul error setelah mengubah kode, baca pesan error di terminal tempat
backend/frontend berjalan, dan di tab **Console** browser (tekan **F12**).

### B. Mengubah database (menambah tabel atau kolom)

1. **Backup dulu.** Di HeidiSQL: klik kanan database `pencatatan_keuangan` →
   **Export database as SQL** → simpan file `.sql`-nya.
2. **Ubah model** di `backend\app\models.py` (tambah kolom atau tabel baru).
3. **Buat file migrasi** di folder `backend\migrations\` dengan nomor
   berurutan, misalnya `003_nama_perubahan.sql`:
   ```sql
   USE pencatatan_keuangan;

   ALTER TABLE transactions
     ADD COLUMN nama_kolom VARCHAR(100) NULL;
   ```
4. **Jalankan migrasi.** Di HeidiSQL: **File → Load SQL file** → pilih file
   migrasi tadi → klik **Execute** (ikon petir). Jalankan **sekali saja**.
5. **Perbarui `backend\schema.sql`** dengan struktur terbaru, supaya instalasi
   baru langsung memakai struktur yang sama.
6. **Restart backend** (**Ctrl + C**, `python run.py`) lalu tes di browser.

### C. Menerima perubahan dari teman (tanpa Git)

1. Minta teman mengirim **file yang diubah** (atau zip proyek terbaru) beserta
   **file migrasi baru** kalau ada perubahan database.
2. Timpa file yang berubah di folder proyekmu. Jangan menimpa `backend\.env`
   dan folder `backend\venv` milikmu.
3. Jalankan file migrasi baru di HeidiSQL (lihat B.4), **urut dari nomor
   terkecil** yang belum pernah kamu jalankan.
4. Kalau `requirements.txt` atau `package.json` berubah, jalankan install ulang
   (lihat tabel A), lalu restart backend dan frontend.

### D. Mengulang database dari awal

Berguna kalau data percobaan sudah berantakan (**semua data akan hilang**):

1. Di HeidiSQL, klik kanan database `pencatatan_keuangan` → **Drop**.
2. **File → Load SQL file** → pilih `backend\schema.sql` → **Execute**.
3. Restart backend, lalu daftar akun baru di web.

### Error yang sering muncul

| Pesan error | Penyebab dan solusi |
|---|---|
| `Unknown column '...' in 'field list'` | Restart backend (kolom ditambahkan otomatis saat start). Kalau masih muncul, jalankan file migrasi di `backend\migrations` (lihat B.4). |
| `Table '...' doesn't exist` | Database belum dibuat. Jalankan `schema.sql` (lihat bagian 1.C). |
| `Access denied for user 'root'` | Password di `DATABASE_URL` pada `.env` tidak cocok dengan MySQL Laragon. |
| `Address already in use` | Server lama masih berjalan. Tutup terminal lamanya atau restart Laragon. |
