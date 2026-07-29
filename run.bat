@echo off
cd /d "%~dp0"

set PYTHON=python
where %PYTHON% >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python not found. Install Python 3.9+ from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    set PYTHON=py
)
echo [OK] Using %PYTHON%

if not exist "venv" (
    echo [..] Creating virtual environment...
    %PYTHON% -m venv venv
)

call venv\Scripts\activate.bat

if not exist "venv\.deps_installed" (
    echo [..] Installing dependencies ^(one-time^)...
    pip install -r requirements.txt
    if %ERRORLEVEL% equ 0 (
        type nul > venv\.deps_installed
        echo [OK] Dependencies installed
    ) else (
        echo [ERROR] pip install failed. See messages above.
        pause
        exit /b 1
    )
)

echo.
echo [START] Starting Art Style Analyzer...
echo    Open http://localhost:5001 in your browser
echo.

ping -n 3 127.0.0.1 >nul
start http://localhost:5001

python app.py
pause
