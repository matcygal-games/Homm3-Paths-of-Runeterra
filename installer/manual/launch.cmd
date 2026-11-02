@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" -LaunchCheck -NonInteractive
if errorlevel 1 (
  echo Launch stopped. Run setup.cmd and read the message above.
  pause
  exit /b 1
)
set "TEMP=%~dp0user\temp"
set "TMP=%~dp0user\temp"
cd /d "%~dp0app"
if errorlevel 1 exit /b 1
start "" "%~dp0app\VCMI_client.exe" --nointro
exit /b %ERRORLEVEL%
