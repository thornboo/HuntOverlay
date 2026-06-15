@echo off
setlocal

cd /d "%~dp0"

REM Usage: build_windows.bat [onedir|onefile|both] [clean] [nopause]
set "MODE=%~1"
if "%MODE%"=="" set "MODE=onedir"

set "PS_ARGS=-Mode "%MODE%""
set "NOPAUSE="

REM Scan remaining args for the optional clean / nopause flags.
:parse
shift
if "%~1"=="" goto run
if /i "%~1"=="clean"   set "PS_ARGS=%PS_ARGS% -Clean"
if /i "%~1"=="nopause" set "NOPAUSE=1"
goto parse

:run
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1" %PS_ARGS%
set "EXITCODE=%ERRORLEVEL%"

echo.
if not "%EXITCODE%"=="0" (
  echo Build failed with exit code %EXITCODE%.
) else (
  echo Build finished successfully.
)
echo.
if not defined NOPAUSE pause
exit /b %EXITCODE%
