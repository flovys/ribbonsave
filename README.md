# 🎀 RibbonSave — Media Downloader

Aplikasi web modern berbasis full-stack untuk mengunduh video dan audio dari berbagai platform media sosial ternama dengan tema estetika **Pink Aesthetic**.

![Theme](https://img.shields.io/badge/Theme-Coquette%20Pink-F48FB1?style=for-the-badge)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Frontend](https://img.shields.io/badge/Frontend-React%20+%20Vite%20+%20Tailwind-61DAFB?style=for-the-badge&logo=react&logoColor=black)

---

## ✨ Fitur Utama

- 🎀 **Desain Coquette Pink Aesthetic:**
  - Antarmuka *Glassmorphism* lembut dengan aksen warna *Blush Pink*, *Rose*, dan *Berry Pink*.
  - Tipografi elegan kombinasi font *Playfair Display* dan *Quicksand*.
  - Animasi pita bergoyang (*ribbon sway*), kilauan bintang (*sparkles* ✨), serta status unduhan interaktif.
- 🎬 **Multi-Platform Support:**
  - **YouTube:** Video hingga resolusi tinggi (1080p/720p/480p/360p) & konversi instan ke Audio MP3 (320kbps).
  - **TikTok:** Unduh video jernih tanpa watermark (*No Watermark*).
  - **Instagram:** Reels, video post, dan IG TV.
  - **X / Twitter & Facebook:** Deteksi resolusi otomatis dan unduhan langsung.
- ⚡ **Enkripsi & Challenge Solver:**
  - Terintegrasi dengan `yt-dlp` terbaru, `deno`/`node` runtime solver, dan dukungan `cookies.txt` untuk melewati verifikasi bot YouTube.
- 📜 **Riwayat Unduhan (Recent Downloads):**
  - Tersimpan aman di `localStorage` peramban Anda untuk akses cepat.

---

## 🏗️ Struktur Direktori Proyek

```text
VideoMusicDownloader/
├── run.bat                  # Script one-click launcher untuk Windows
├── README.md                # Dokumentasi proyek ini
├── backend/
│   ├── main.py              # Server FastAPI, streaming & integrasi yt-dlp
│   ├── requirements.txt     # Dependensi Python
│   └── cookies.txt          # (Opsional) Cookie YouTube untuk bypass bot check
└── frontend/
    ├── package.json         # Dependensi Node.js / React
    ├── vite.config.js       # Konfigurasi Vite & reverse-proxy API
    ├── tailwind.config.js   # Konfigurasi palet warna & tema coquette
    └── src/
        ├── App.jsx          # Komponen utama aplikasi
        ├── index.css        # Styling tema, gradasi, & scrollbar
        └── components/      # Navbar, InputCard, ResultCard, Loading, Footer
```

---

## 🚀 Cara Menjalankan Menggunakan File `.bat` (Paling Mudah)

Di dalam folder proyek ini sudah disediakan file launcher bernama **`run.bat`**. File ini memungkinkan Anda menjalankan seluruh aplikasi **hanya dengan 1 kali klik** tanpa perlu membuka dan mengetik perintah di terminal berulang kali.

### 📌 Langkah Menjalankannya:

1. **Buka File Explorer** di laptop Anda.
2. Masuk ke folder proyek:  
   `VideoMusicDownloader`
3. **Klik dua kali (Double-click)** pada file:
   ```text
   run.bat
   ```
4. **Selesai!** 
   - Dua jendela terminal CMD akan otomatis terbuka di latar belakang:
     1. `RibbonSave Backend` (Port `8000`)
     2. `RibbonSave Frontend` (Port `5173`)
   - Browser Anda akan otomatis terbuka dan memuat halaman:
     👉 **`http://localhost:5173`**

---

### 🔍 Apa yang Dilakukan oleh `run.bat`?

Berikut isi script yang ada di dalam `run.bat`:

```bat
@echo off
title RibbonSave
echo ===================================================
echo     🎀 RibbonSave - Starting Services... 🎀
echo ===================================================
echo.

echo [1/2] Menjalankan Backend (FastAPI :8000)...
start "RibbonSave Backend" cmd /k "cd /d %~dp0backend && python main.py"

echo [2/2] Menjalankan Frontend (Vite :5173)...
start "RibbonSave Frontend" cmd /k "cd /d %~dp0frontend && npx vite --port 5173"

echo.
echo ✅ Kedua server sedang berjalan!
echo Membuka aplikasi di browser (http://localhost:5173)...
timeout /t 3 /nobreak >nul
start http://localhost:5173
exit
```

* **`%~dp0`**: Memastikan path folder otomatis mendeteksi lokasi file `.bat` berada, sehingga script ini tetap bekerja meskipun folder dipindahkan.
* **`cmd /k`**: Menjaga jendela terminal tetap terbuka agar Anda dapat melihat log proses unduhan secara langsung.
* **`start http://localhost:5173`**: Otomatis meluncurkan browser bawaan Anda ke web RibbonSave setelah hitungan mundur 3 detik.

> [!TIP]
> **Cara Mematikan Aplikasi:**  
> Cukup tutup (*close* / klik tanda silang `X`) pada kedua jendela CMD `RibbonSave Backend` dan `RibbonSave Frontend`.

---

## 🛠️ Instalasi Pertama Kali (Prasyarat Sistem)

Sebelum menjalankan `run.bat` untuk pertama kali di komputer baru, pastikan dependensi berikut sudah terpasang:

### 1. Python 3.10+
Pastikan saat menginstal Python Anda mencentang opsi **"Add Python to PATH"**.
Instal dependensi backend:
```cmd
cd backend
pip install -r requirements.txt
```

### 2. Node.js 18+
Instal dependensi frontend:
```cmd
cd frontend
npm install
```

### 3. FFmpeg
Pastikan `ffmpeg` terinstal dan dikenali di sistem PATH, atau letakkan executable `ffmpeg.exe` di dalam folder backend.

---

## 🌐 Menjalankan Manual (Tanpa .bat)

Jika Anda ingin menjalankan masing-masing server secara terpisah lewat terminal:

1. **Terminal 1 (Backend):**
   ```bash
   cd backend
   python main.py
   ```
   *Backend aktif di:* `http://localhost:8000`

2. **Terminal 2 (Frontend):**
   ```bash
   cd frontend
   npm run dev
   ```
   *Frontend aktif di:* `http://localhost:5173`

---

## ☁️ Menjalankan di Server VPS

```bash
# 1. Install Dependensi & Jalankan Backend via PM2
cd ~/VideoMusicDownloader/backend
pip install -r requirements.txt --break-system-packages
pm2 start main.py --interpreter python3 --name "ribbonsave-backend"

# 2. Build Frontend (untuk dilayani langsung oleh DocumentRoot Apache2)
cd ~/VideoMusicDownloader/frontend
npm install
npm run build

# 3. Simpan daftar proses agar otomatis jalan saat VPS reboot
pm2 save
```

---

<p align="center">Made by RibbonSave 🎀</p>
