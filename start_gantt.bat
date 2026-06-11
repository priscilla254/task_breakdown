@echo off
rem Start the Tasks Gantt app and open it in the browser.
rem Double-click this file, or put a shortcut to it in shell:startup.

cd /d "%~dp0"

rem If the app is already running, just open the browser.
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel%==0 (
    start "" http://127.0.0.1:8000
    exit /b 0
)

start "" http://127.0.0.1:8000

rem Prefer Anaconda python (matches your environment); fall back to PATH.
if exist "%USERPROFILE%\anaconda3\python.exe" (
    "%USERPROFILE%\anaconda3\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn main:app --host 127.0.0.1 --port 8000
)
