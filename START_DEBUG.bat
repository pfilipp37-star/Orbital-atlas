@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call START.bat
".venv\Scripts\python.exe" main.py %*
echo.
pause
