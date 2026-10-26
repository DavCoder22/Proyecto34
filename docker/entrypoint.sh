#!/usr/bin/env bash
set -e

if [[ -n "${DATABASE_URL:-}" && "${RUN_ETL_ON_START:-1}" != "0" ]]; then
    echo "[poc] DATABASE_URL detectada: ejecutando ETL y carga a PostgreSQL..."
    if python /home/jovyan/work/02_etl/main.py; then
        python /home/jovyan/work/04_dashboard/build_dashboard.py || true
    else
        echo "[poc] Aviso: el ETL falló; Jupyter continuará."
    fi
fi

exec "$@"
