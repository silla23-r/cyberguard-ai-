@echo off
chcp 65001 > nul
title CyberGuard WhatsApp MCP Interactive Tester
color 0A
echo ================================================================
echo    CYBERGUARD AI — WHATSAPP MCP DEFENSE SUITE TESTER
echo    Quarantine, Danger Advisory & 1-Tap Permanent Block
echo ================================================================
echo.

cd /d "%~dp0backend"
set PYTHONIOENCODING=utf-8
python mcp_server/interactive_cli.py

pause

