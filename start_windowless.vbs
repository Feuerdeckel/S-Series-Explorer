' Version: 1.0.0
Option Explicit

Dim fso, shell, projectDir, launcherPath, logPath, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
launcherPath = fso.BuildPath(projectDir, "launcher.py")
logPath = fso.BuildPath(projectDir, "startup.log")

command = "cmd.exe /d /c cd /d """ & projectDir & """ && py """ & launcherPath & """ > """ & logPath & """ 2>&1"
shell.Run command, 0, False
