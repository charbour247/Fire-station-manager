@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.11 or newer from python.org, including Tcl/Tk and the Python launcher.
  pause
  exit /b 1
)
py -3 app.py %*
if errorlevel 1 pause
