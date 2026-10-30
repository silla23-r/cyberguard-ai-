@echo off
title CyberGuard AI Launcher
color 0B
echo ================================================================
echo           SHIELD ON: Starting CyberGuard AI Server...
echo ================================================================
echo.

cd /d "%~dp0backend"

echo [1/2] Checking Python dependencies...
python -m pip install -r requirements.txt --quiet

echo [2/2] Launching CyberGuard AI Server...
echo.
echo Opening browser to http://localhost:8000 ...
start http://localhost:8000

python main.py

pause

