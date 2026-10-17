@echo off
setlocal
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
py -3 "weather_get.py" >> "logs\weather_get_task.log" 2>&1
py -3 "weather_plus.py" >> "logs\weather_plus_task.log" 2>&1
py -3 "calendar_sun.py" >> "logs\calendar_sun_task.log" 2>&1
py -3 "disaster_info\disaster_info.py" >> "logs\disaster_info_task.log" 2>&1
py -3 "power_forecast\power_forecast.py" >> "logs\power_forecast_task.log" 2>&1

exit /b %errorlevel%