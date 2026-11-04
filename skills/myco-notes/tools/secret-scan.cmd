@echo off
REM secret-scan: Windows launcher for secret_scan.py
where python >nul 2>nul
if %errorlevel%==0 (python "%~dp0secret_scan.py" %*) else (py -3 "%~dp0secret_scan.py" %*)
exit /b %errorlevel%
