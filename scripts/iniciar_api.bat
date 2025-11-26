@echo off
echo Iniciando API Python...
cd /d "%~dp0\..\.."
python backend\api\run_api.py
pause
