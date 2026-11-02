@echo off
setlocal
if not exist "%~dp0app\Data\H3bitmap.lod" (
  echo Heroes III data could not be found. Restore the original installation at the location selected during setup.
  pause
  exit /b 2
)
if not exist "%~dp0app\Mp3\" (
  echo The Heroes III music directory could not be found. Restore the original installation selected during setup.
  pause
  exit /b 2
)
cd /d "%~dp0app"
start "" "%~dp0app\VCMI_client.exe" --nointro
