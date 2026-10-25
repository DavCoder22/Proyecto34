@echo off
cd /d "%~dp0"
echo ============================================
echo PoC BI - Despliegue local con Docker
echo ============================================
if not exist .env (
    echo [INFO] No existe .env. Copiando desde .env.example...
    copy .env.example .env
    echo [OK] .env creado. Puedes editarlo si deseas.
    echo.
)
echo [INFO] Levantando servicios: PostgreSQL + Jupyter + Apache Superset
echo [INFO] Esto puede tardar unos minutos la primera vez...
echo.
docker compose -f docker/docker-compose.yml up --build
pause
