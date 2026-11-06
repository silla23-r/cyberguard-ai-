@echo off
chcp 65001 > nul
title CyberGuard WhatsApp MCP Stdio Server
cd /d "%~dp0backend"
set PYTHONIOENCODING=utf-8
python mcp_server/server.py

