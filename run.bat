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
