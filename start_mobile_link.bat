@echo off
title StatSkill AI Mobile Link Generator
cd /d "%~dp0"
echo ========================================================
echo Starting StatSkill AI Mobile Link Generator...
echo ========================================================
cloudflared.exe tunnel --url http://localhost:8000 --metrics 127.0.0.1:0
pause
