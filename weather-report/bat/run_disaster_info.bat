@echo off
setlocal
cd /d "%~dp0.."
if not exist "logs" mkdir "logs"
py -3 "disaster_info\disaster_info.py" >> "logs\disaster_info_task.log" 2>&1
exit /b %errorlevel%