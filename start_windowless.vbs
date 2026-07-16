' Version: 1.3.1
Option Explicit

Dim fso, shell, projectDir, logPath, publishedExe, projectFile, dotnetPath, command, quote
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
quote = Chr(34)

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
logPath = fso.BuildPath(projectDir, "startup.log")
publishedExe = fso.BuildPath(projectDir, "SSeriesExplorer.WinForms\bin\Release\net8.0-windows\win-x64\publish\S-Series-Explorer.exe")
projectFile = fso.BuildPath(projectDir, "SSeriesExplorer.WinForms\SSeriesExplorer.WinForms.csproj")
shell.CurrentDirectory = projectDir

If fso.FileExists(logPath) Then
    On Error Resume Next
    fso.DeleteFile logPath, True
    On Error GoTo 0
End If

If fso.FileExists(publishedExe) Then
    shell.Run """" & publishedExe & """", 1, False
    WScript.Quit 0
End If

If Not fso.FileExists(projectFile) Then
    WriteStartupError "Projektdatei wurde nicht gefunden: " & projectFile
    WScript.Quit 1
End If

dotnetPath = FindDotnet()
If dotnetPath = "" Then
    WriteStartupError "S-Series Explorer konnte nicht gestartet werden, weil .NET 8 Desktop Runtime oder .NET 8 SDK nicht gefunden wurde." & vbCrLf & vbCrLf & _
        "Bitte .NET 8 Desktop Runtime installieren oder eine veroeffentlichte EXE in SSeriesExplorer.WinForms\bin\Release\net8.0-windows\win-x64\publish verwenden." & vbCrLf & vbCrLf & _
        "Technischer Konsolenstart nach der Installation:" & vbCrLf & _
        "dotnet run --project """ & projectFile & """"
    WScript.Quit 1
End If

command = "cmd /c " & quote & quote & dotnetPath & quote & " run --project " & quote & projectFile & quote & " > " & quote & logPath & quote & " 2>&1" & quote
shell.Run command, 0, False

Function FindDotnet()
    Dim candidate, execResult
    candidate = fso.BuildPath(shell.ExpandEnvironmentStrings("%ProgramFiles%"), "dotnet\dotnet.exe")
    If fso.FileExists(candidate) Then
        FindDotnet = candidate
        Exit Function
    End If

    candidate = fso.BuildPath(shell.ExpandEnvironmentStrings("%ProgramFiles(x86)%"), "dotnet\dotnet.exe")
    If fso.FileExists(candidate) Then
        FindDotnet = candidate
        Exit Function
    End If

    On Error Resume Next
    Set execResult = shell.Exec("cmd /c where dotnet.exe")
    If Err.Number = 0 Then
        candidate = Trim(execResult.StdOut.ReadLine())
        If candidate <> "" And fso.FileExists(candidate) Then
            FindDotnet = candidate
            On Error GoTo 0
            Exit Function
        End If
    End If
    On Error GoTo 0

    FindDotnet = ""
End Function

Sub WriteStartupError(message)
    Dim stream
    Set stream = fso.CreateTextFile(logPath, True)
    stream.WriteLine message
    stream.Close
    shell.Popup message & vbCrLf & vbCrLf & "Details stehen in startup.log.", 0, "S-Series Explorer", 16
End Sub
