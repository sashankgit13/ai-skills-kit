@echo off
rem Double-click to start the guided AI setup on Windows.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\setup.py
  goto end
)
where python >nul 2>nul
if %errorlevel%==0 (
  python tools\setup.py
  goto end
)
echo Python 3.9 or newer is needed and was not found.
echo Please install it from https://www.python.org/downloads/ or ask IT for help.
:end
echo.
pause
