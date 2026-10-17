@echo off
setlocal
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
py -3 "weather_plus.py" >> "logs\weather_plus_task.log" 2>&1
exit /b %errorlevel%