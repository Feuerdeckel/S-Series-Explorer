@echo off
setlocal
cd /d "%~dp0"
py "%~dp0launcher.py"
if errorlevel 1 (
    echo.
    echo S-Series Explorer konnte nicht gestartet werden.
    echo Bitte pruefen Sie, ob Python 3.11 oder neuer installiert ist.
    pause
    exit /b 1
)
endlocal
