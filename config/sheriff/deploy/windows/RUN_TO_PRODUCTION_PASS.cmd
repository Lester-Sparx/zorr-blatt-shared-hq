@echo off
setlocal
cd /d "%~dp0"

echo === ZORR SHERIFF V1 - BASE-FIRST PRODUCTION ACTIVATION ===
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ZbSheriffV1.ps1" -Action Install
if errorlevel 1 goto :fail

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ZbSheriffV1.ps1" -Action Verify
if errorlevel 1 goto :fail

echo.
echo ========================================
echo SHERIFF V1 PRODUCTION = PASS
echo ========================================
pause
exit /b 0

:fail
echo.
echo ========================================
echo SHERIFF V1 PRODUCTION = FAIL - SEE BLOCKER
echo ========================================
pause
exit /b 1
