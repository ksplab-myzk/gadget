@echo off
setlocal
cd /d "%~dp0.."
if not exist "logs" mkdir "logs"
py -3 "space_weather\space_weather.py" %* >> "logs\space_weather_task.log" 2>&1
exit /b %errorlevel%
