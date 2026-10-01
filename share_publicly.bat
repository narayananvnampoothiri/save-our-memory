@echo off
title Save Our Memory - Public Sharing Link
color 0B

echo ==============================================================
echo       Save Our Memory - Instant Public Phone Sharing Link
echo ==============================================================
echo.
echo Starting secure public tunnel...
echo Anyone anywhere in the world can open this link on their phone!
echo.

:: Ensure cloudflared is present
if not exist "cloudflared.exe" (
    echo Downloading cloudflared...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
)

:: Run tunnel
.\cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
