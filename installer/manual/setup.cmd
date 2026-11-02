@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
set "PATHS_RESULT=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %PATHS_RESULT%
