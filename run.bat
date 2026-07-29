@echo off
REM --- Art Style Analyzer Launcher (Windows) ---
REM Double-click or run from Command Prompt.

cd /d "%~dp0"

REM 1. Find Python
set PYTHON=python
where %PYTHON% >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [41m[37m ERROR [0m Python not found.
        echo Install Python 3.9+ from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    set PYTHON=py
)

echo [92m✓[0m Using %PYTHON%

REM 2. Create virtual environment if missing
if not exist "venv" (
    echo [96m📦[0m Creating virtual environment...
    %PYTHON% -m venv venv
)

REM 3. Activate
call venv\Scripts\activate.bat

REM 4. Install dependencies if missing
if not exist "venv\.deps_installed" (
    echo [93m📥[0m Installing dependencies (one-time)...
    pip install -q -r requirements.txt
    type nul > venv\.deps_installed
    echo [92m✓[0m Dependencies installed
)

REM 5. Open browser and launch
echo.
echo [96m🚀[0m Starting Art Style Analyzer...
echo    Open http://localhost:5001 in your browser
echo.

timeout /t 2 >nul
start http://localhost:5001

python app.py
pause
