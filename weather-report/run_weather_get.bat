@echo off
setlocal
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
py -3 "weather_get.py" >> "logs\weather_get_task.log" 2>&1
exit /b %errorlevel%