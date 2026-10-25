@echo off
cd /d "%~dp0\02_etl"
python profile.py
if %errorlevel% neq 0 ( echo ERROR & pause & exit /b %errorlevel% )
echo Reporte: ..\06_calidad\profile_report.md
pause