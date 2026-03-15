@echo off
:: Force the code page to UTF-8
chcp 65001 > nul

title SenseVoice ASR Service

echo ======================================================
echo [INFO] Starting SenseVoice ASR Service...
echo [INFO] URL: http://127.0.0.1:18080
echo [INFO] Docs: http://127.0.0.1:18080/docs
echo ======================================================

:: Use python -m uvicorn for better compatibility in conda
python -m uvicorn service.app:app --host 127.0.0.1 --port 18080 --reload

if %errorlevel% neq 0 (
    echo [ERROR] Service failed to start.
    pause
)