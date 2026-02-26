@echo off
echo Iniciando API Python...
cd /d "%~dp0\..\.."
py backend\api\run_api.py
pause
