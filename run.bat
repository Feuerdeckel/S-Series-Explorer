@echo off
rem Version: 1.4.0
setlocal
cd /d "%~dp0"

if exist "%SystemRoot%\System32\wscript.exe" (
    start "" "%SystemRoot%\System32\wscript.exe" "%~dp0start_windowless.vbs"
    endlocal
    exit /b 0
)

echo S-Series Explorer konnte nicht ohne Terminalfenster gestartet werden.
echo Windows Script Host ^(wscript.exe^) wurde nicht gefunden oder ist deaktiviert.
echo Technischer Konsolenstart: py "%~dp0launcher.py"
pause
exit /b 1
