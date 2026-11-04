@echo off
REM bootstrap: Windows launcher for bootstrap.py
where python >nul 2>nul
if %errorlevel%==0 (python "%~dp0bootstrap.py" %*) else (py -3 "%~dp0bootstrap.py" %*)
exit /b %errorlevel%
