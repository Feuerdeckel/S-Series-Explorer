@echo off
rem Version: 1.5.0
setlocal
cd /d "%~dp0"

if exist "%SystemRoot%\System32\wscript.exe" (
    start "" "%SystemRoot%\System32\wscript.exe" "%~dp0start_windowless.vbs"
    endlocal
    exit /b 0
)

echo S-Series Explorer konnte nicht ohne Terminalfenster gestartet werden.
echo Windows Script Host ^(wscript.exe^) wurde nicht gefunden oder ist deaktiviert.
echo Technischer Konsolenstart: dotnet run --project "%~dp0SSeriesExplorer.WinForms\SSeriesExplorer.WinForms.csproj"
pause
exit /b 1
