@echo off
setlocal
cd /d "%~dp0.."
if not exist "logs" mkdir "logs"
py -3 "notice_board\notice_board.py" >> "logs\notice_board_task.log" 2>&1
exit /b %errorlevel%
