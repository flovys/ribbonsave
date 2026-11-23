# RibbonSave — Media Downloader

Aplikasi web modern berbasis full-stack untuk mengunduh video, audio, dan foto/carousel dari berbagai platform media sosial ternama dengan tema estetika **Coquette Pink Aesthetic**.

![Theme](https://img.shields.io/badge/Theme-Coquette%20Pink-F48FB1?style=for-the-badge)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Frontend](https://img.shields.io/badge/Frontend-React%20+%20Vite%20+%20Tailwind-61DAFB?style=for-the-badge&logo=react&logoColor=black)

---

## ✨ Fitur Utama

- 🎀 **Desain Coquette Pink Aesthetic:**
  - Antarmuka *Glassmorphism* lembut dengan aksen warna *Blush Pink*, *Rose*, dan *Berry Pink*.
  - Tipografi elegan kombinasi font *Playfair Display* dan *Quicksand*.
  - Animasi pita bergoyang (*ribbon sway*), kilauan bintang (*sparkles* ✨), serta status unduhan interaktif.
- 🎬 **Multi-Platform Media & Video Support:**
  - **TikTok:** Unduh video tanpa watermark (*No Watermark*), audio MP3, serta foto slide/carousel.
  - **Instagram:** Reels, video post, foto feed, dan carousel gambar HD.
  - **X / Twitter:** Video, audio, dan gambar beresolusi tinggi.
  - **Facebook:** Video reels, post, dan gambar/album.
- 🖼️ **Ekstraksi Multi-Foto Universal & Preview Thumbnail:**
  - **TikTok:** Ekstraksi seluruh slide foto (*slideshow* / `imagePost`).
  - **Instagram:** Ekstraksi seluruh foto postingan *carousel* resolusi HD.
  - **X / Twitter:** Ekstraksi multi-gambar (hingga 4 foto per tweet) resolusi asli (`orig`).
  - **Facebook:** Ekstraksi multi-foto album dan postingan foto Facebook HD.
  - **Visual Thumbnail Preview:** Setiap slide foto di daftar unduhan kini memiliki cuplikan gambar visual nyata, nomor urut slide (`Slide X/N`), serta badge resolusi & format.
  - **Interactive Lightbox Modal Preview:** Klik thumbnail mana pun untuk melihat foto ukuran penuh dengan navigasi slide (panah `←` / `→`) dan tombol unduh langsung.
- 📦 **Tombol Universal "Download All (.ZIP)":**
  - Banner kartu Coquette Pink otomatis tampil jika postingan memiliki lebih dari 1 foto.
  - Pengunduhan paralel cepat multi-threaded (`ThreadPoolExecutor`) dengan penamaan terstruktur rapi (`Judul_01.jpg`, `Judul_02.jpg`, dst.).
  - Mengemas seluruh slide foto ke dalam 1 berkas arsip `.ZIP` terkompresi secara instan dengan *streaming chunk* langsung ke browser.
- 🎵 **Ekstraksi Audio MP3:**
  - Pilihan mengunduh audio murni berkecepatan 320kbps dari video maupun slide musik.
- 📜 **Riwayat Unduhan (Recent Downloads):**
  - Tersimpan aman di `localStorage` peramban Anda untuk akses cepat, lengkap dengan label tipe (`🎬 Video`, `🎵 Audio`, `🖼️ Gambar`, dan `📦 Arsip Foto (.ZIP)`).

---

## 🏗️ Struktur Direktori Proyek

```text
ribbonsave/
├── run.bat                  # Script one-click launcher untuk Windows
├── README.md                # Dokumentasi proyek ini
├── backend/
│   ├── main.py              # Server FastAPI, streaming chunk, ZIP packager & yt-dlp patch
│   └── requirements.txt     # Dependensi Python
└── frontend/
    ├── package.json         # Dependensi Node.js / React
    ├── vite.config.js       # Konfigurasi Vite & reverse-proxy API
    ├── tailwind.config.js   # Konfigurasi palet warna & tema coquette
    └── src/
        ├── App.jsx          # Komponen utama aplikasi & handler unduhan ZIP
        ├── index.css        # Styling tema, gradasi, & scrollbar
        └── components/      # Navbar, InputCard, ResultCard, Loading, Footer, RecentDownloads
```

---

## 🚀 Cara Menjalankan Menggunakan File `.bat` (Paling Mudah)

Di dalam folder proyek ini sudah disediakan file launcher bernama **`run.bat`**. File ini memungkinkan Anda menjalankan seluruh aplikasi **hanya dengan 1 kali klik** tanpa perlu membuka dan mengetik perintah di terminal berulang kali.

### 📌 Langkah Menjalankannya:

1. **Buka File Explorer** di laptop Anda.
2. Masuk ke folder proyek:  
   `ribbonsave`
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
echo      RibbonSave - Starting Services... 
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

# 2. Build Frontend (untuk dilayani langsung oleh Apache2)
cd ~/VideoMusicDownloader/frontend
npm install
npm run build

# 3. Simpan daftar proses agar otomatis jalan saat VPS reboot
pm2 save
```

---

<p align="center">Made by RibbonSave 🎀</p>
