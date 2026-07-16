' Version: 1.1.0
Option Explicit

Dim fso, shell, projectDir, launcherPath, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
launcherPath = fso.BuildPath(projectDir, "launcher.pyw")

command = "pyw """ & launcherPath & """"
shell.CurrentDirectory = projectDir
shell.Run command, 1, False
