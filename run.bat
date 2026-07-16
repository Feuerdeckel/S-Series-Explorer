@echo off
rem Version: 1.1.0
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pyw "%~dp0launcher.py"
    endlocal
    exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0launcher.py"
    endlocal
    exit /b 0
)

echo S-Series Explorer konnte nicht ohne Terminalfenster gestartet werden.
echo Bitte pruefen Sie, ob Python 3.11 oder neuer inklusive pyw/pythonw installiert ist.
echo Alternativ kann der technische Konsolenstart mit "py launcher.py" verwendet werden.
pause
exit /b 1
