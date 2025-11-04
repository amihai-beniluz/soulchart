@echo off
title SoulChart Bot - Auto Restart
color 0A

REM עבור לתיקיית הפרויקט
cd /d "C:\Users\Amihai\MyCode\PycharmProjects\SoulChart"

REM צור תיקיית logs אם לא קיימת
if not exist "logs" mkdir logs

echo ========================================
echo   SoulChart Bot - Auto Restart Mode
echo ========================================
echo.
echo [*] Bot will restart automatically if crashed
echo [*] Logs saved to: logs\bot.log
echo [*] Press Ctrl+C to stop permanently
echo.
echo ========================================
echo.

:loop
echo [%date% %time%] Starting bot...
echo [%date% %time%] Starting bot... >> logs\bot.log

REM הפעל venv אם קיים
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [*] Virtual environment activated
)

REM הרץ את הבוט ושמור לוגים
python bot.py 2>> logs\bot.log

REM אם הגענו לכאן, הבוט קרס או נעצר
echo.
echo [%date% %time%] Bot stopped/crashed! >> logs\bot.log
echo [!] Bot stopped or crashed!
echo [*] Check logs\bot.log for details
echo [*] Restarting in 5 seconds...
echo.

timeout /t 5 /nobreak

goto loop