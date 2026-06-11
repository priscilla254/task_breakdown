' Launches the Gantt app with no visible window.
' Put a shortcut to THIS file in your Startup folder (Win+R -> shell:startup)
' so the app is always running after you log in.
Set shell = CreateObject("WScript.Shell")
projectDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
python = shell.ExpandEnvironmentStrings("%USERPROFILE%") & "\anaconda3\python.exe"
shell.CurrentDirectory = projectDir
shell.Run """" & python & """ -m uvicorn main:app --host 127.0.0.1 --port 8000", 0, False
