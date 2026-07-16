' Version: 1.2.0
Option Explicit

Dim fso, shell, projectDir, command, logPath
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
logPath = fso.BuildPath(projectDir, "startup.log")
command = "cmd /c dotnet run --project """ & fso.BuildPath(projectDir, "SSeriesExplorer.WinForms\SSeriesExplorer.WinForms.csproj") & """ > """ & logPath & """ 2>&1"
shell.CurrentDirectory = projectDir
shell.Run command, 0, False
