@echo off
setlocal
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
py -3 "power_forecast\power_forecast.py" >> "logs\power_forecast_task.log" 2>&1
exit /b %errorlevel%