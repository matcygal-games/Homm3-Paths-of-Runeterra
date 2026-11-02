@echo off
call "%~dp0/conanvcvars.bat"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] %~dp0/conanvcvars.bat failed with code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
call "%~dp0/conanbuildenv-release-x86_64.bat"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] %~dp0/conanbuildenv-release-x86_64.bat failed with code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)