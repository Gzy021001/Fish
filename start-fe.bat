@echo off
:loop
echo [%date% %time%] Starting Vite dev server...
call npm run dev
echo [%date% %time%] Vite crashed, restarting in 2 seconds...
timeout /t 2 >nul
goto loop
