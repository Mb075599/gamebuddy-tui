@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 "%SCRIPT_DIR%gcii_tui.py" %*
    exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python "%SCRIPT_DIR%gcii_tui.py" %*
    exit /b %ERRORLEVEL%
)

echo Python was not found in PATH.
echo Install Python 3 and try again.
exit /b 1
