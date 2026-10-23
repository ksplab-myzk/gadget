@echo off
setlocal
cd /d "%~dp0.."
set "DEST_DIR=D:\Programming\digital-signage\imagesC\card"
if not exist "logs" mkdir "logs"
py -3 "weather_get.py" >> "logs\weather_get_task.log" 2>&1
py -3 "weather_plus.py" >> "logs\weather_plus_task.log" 2>&1
py -3 "calendar_sun.py" >> "logs\calendar_sun_task.log" 2>&1
py -3 "disaster_info\disaster_info.py" >> "logs\disaster_info_task.log" 2>&1
py -3 "power_forecast\power_forecast.py" >> "logs\power_forecast_task.log" 2>&1
py -3 "notice_board\notice_board.py" >> "logs\notice_board_task.log" 2>&1

if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"
copy /Y "output\weather.png" "%DEST_DIR%\weather.png" >nul
if errorlevel 1 exit /b 1
copy /Y "output\airquality.png" "%DEST_DIR%\airquality.png" >nul
if errorlevel 1 exit /b 1
copy /Y "output\calendar_sun.png" "%DEST_DIR%\calendar_sun.png" >nul
if errorlevel 1 exit /b 1
copy /Y "output\disaster_info.png" "%DEST_DIR%\disaster_info.png" >nul
if errorlevel 1 exit /b 1
copy /Y "output\power_forecast.png" "%DEST_DIR%\power_forecast.png" >nul
if errorlevel 1 exit /b 1
copy /Y "output\notice_board.png" "%DEST_DIR%\notice_board.png" >nul
if errorlevel 1 exit /b 1

exit /b %errorlevel%