@echo off
chcp 65001 >nul
title Побег из тёмного лабиринта
cd /d "%~dp0"

echo ============================================
echo   ЗАПУСК ИГРЫ: Побег из тёмного лабиринта
echo ============================================
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Игра завершилась с кодом %errorlevel%
    pause
)