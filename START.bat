@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Orbital Atlas
set "VENV=.venv"
set "PY=%VENV%\Scripts\python.exe"
set "PYW=%VENV%\Scripts\pythonw.exe"

if exist "%PY%" goto :verify
set "BASEPY="
py -3.12 -c "import sys; print(sys.executable)" >nul 2>&1
if not errorlevel 1 set "BASEPY=py -3.12"
if not defined BASEPY (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 9)" >nul 2>&1
    if not errorlevel 1 set "BASEPY=python"
)
if not defined BASEPY goto :needpython
%BASEPY% -m venv "%VENV%"
if errorlevel 1 goto :fail
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

:verify
"%PY%" -c "import ursina, skyfield, sgp4, cv2, numpy, PIL, geonamescache" >nul 2>&1
if errorlevel 1 (
    "%PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
)
start "Orbital Atlas" "%PYW%" "%~dp0main.py" %*
exit /b 0

:needpython
echo Python 3.12+ is required. Install it from python.org and run START.bat again.
pause
exit /b 12

:fail
echo Setup failed. Run START_DEBUG.bat for details.
pause
exit /b 1
