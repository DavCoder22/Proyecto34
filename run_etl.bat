@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set LOGDIR=06_calidad
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set RUNLOG=%LOGDIR%\run_etl_log.txt
echo ============================================ > "%RUNLOG%"
echo PoC ETL - Ejecucion %date% %time% >> "%RUNLOG%"
echo ============================================ >> "%RUNLOG%"

echo [1/5] Reconocimiento de datos (profiling)...
python 02_etl\profile.py >> "%RUNLOG%" 2>&1
if %errorlevel% neq 0 ( echo ERROR profiling & type "%RUNLOG%" & pause & exit /b %errorlevel% )

echo [2/5] Extraccion (raw -> staging)...
echo (incluido en pipeline) >> "%RUNLOG%"

echo [3/5] Pipeline ETL completo (clean, homologate, validate, transform, load)...
python 02_etl\main.py >> "%RUNLOG%" 2>&1
if %errorlevel% neq 0 ( echo ERROR pipeline & type "%RUNLOG%" & pause & exit /b %errorlevel% )

echo [4/5] Verificacion del DW...
python -c "import sqlite3; c=sqlite3.connect('03_dw/dw.db'); [print(t, c.execute('select count(*) from '+t).fetchone()[0]) for t in ['DimCliente','DimSucursal','DimProducto','DimTiempo','FactVentas']]" >> "%RUNLOG%" 2>&1
if %errorlevel% neq 0 ( echo ERROR verificacion & pause & exit /b %errorlevel% )

echo [5/5] Aplicando vistas KPI...
python -c "import sqlite3; c=sqlite3.connect('03_dw/dw.db'); c.executescript(open('04_dashboard/kpi_views.sql').read()); c.commit(); print('Vistas OK')" >> "%RUNLOG%" 2>&1

echo. >> "%RUNLOG%"
echo EJECUCION COMPLETADA >> "%RUNLOG%"
echo ============================================ >> "%RUNLOG%"

echo.
echo === ETL COMPLETADO ===
echo Log: %RUNLOG%
echo DW: 03_dw\dw.db
echo Reporte profiling: 06_calidad\profile_report.md
echo Log rechazos: 06_calidad\log_rechazos.csv
echo.
type "%RUNLOG%" | findstr /i "OK\|filas\|rechazados\|Ventas fact\|Vistas"
pause