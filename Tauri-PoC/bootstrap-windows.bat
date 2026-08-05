@echo off
setlocal

cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap-windows.ps1" -InstallSystemDependencies %*
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
  echo Tauri bootstrap and build validation finished successfully.
) else (
  echo Tauri bootstrap or build validation failed with exit code %EXITCODE%.
)
echo.
pause
exit /b %EXITCODE%
