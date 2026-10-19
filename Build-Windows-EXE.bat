@echo off
cd /d "%~dp0"
py -3 -m pip install pyinstaller
if errorlevel 1 goto failed
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name StationDesk app.py
if errorlevel 1 goto failed
 echo EXE created in dist\StationDesk.exe
 echo For a timeclock shortcut, use dist\StationDesk.exe --timeclock
 pause
 exit /b 0
:failed
 echo Build failed. Review the errors above.
 pause
 exit /b 1
