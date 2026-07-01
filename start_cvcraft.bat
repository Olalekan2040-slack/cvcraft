@echo off
title CVCraft — Resume Builder
color 0A

cd /d "%~dp0"

echo.
echo  ===============================================
echo    CVCraft — AI Resume Builder
echo    Starting development server...
echo  ===============================================
echo.

:: Activate virtual environment
call "%~dp0venv\Scripts\activate.bat"
if errorlevel 1 (
    echo  [ERROR] Virtual environment not found.
    echo  Expected: %~dp0venv\Scripts\activate.bat
    pause
    exit /b 1
)

:: Wait briefly then open browser
echo  Opening http://127.0.0.1:8000 in your browser...
echo  Press Ctrl+C in this window to stop the server.
echo.
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: Start server (output stays visible in this window)
python manage.py runserver 127.0.0.1:8000

echo.
echo  Server stopped. Press any key to close.
pause >nul
