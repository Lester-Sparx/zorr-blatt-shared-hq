@echo off
setlocal
cd /d "%~dp0\.."
where task >nul 2>nul || (echo RECOVERY_BLOCKED: task not found & exit /b 2)
task -t recovery/Taskfile.yml recover
exit /b %ERRORLEVEL%
