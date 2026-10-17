@echo off
setlocal
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
py -3 "calendar_sun.py" >> "logs\calendar_sun_task.log" 2>&1
exit /b %errorlevel%