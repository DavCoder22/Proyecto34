#!/usr/bin/env bash
set -e

echo "[superset] Inicializando base de metadatos..."
attempt=0
until superset db upgrade; do
    attempt=$((attempt + 1))
    if [[ "$attempt" -ge 30 ]]; then
        echo "[superset] No se pudo inicializar la base de metadatos."
        exit 1
    fi
    echo "[superset] Reintentando en 2s ($attempt/30)..."
    sleep 2
done

if [[ "${SUPERSET_CREATE_ADMIN:-1}" != "0" ]]; then
    : "${SUPERSET_ADMIN_PASS:?Define SUPERSET_ADMIN_PASS antes de iniciar Superset}"
    superset fab create-admin \
        --username "${SUPERSET_ADMIN_USER:-admin}" \
        --firstname "${SUPERSET_ADMIN_FIRSTNAME:-Admin}" \
        --lastname "${SUPERSET_ADMIN_LASTNAME:-BI}" \
        --email "${SUPERSET_ADMIN_EMAIL:-admin@poc.com}" \
        --password "${SUPERSET_ADMIN_PASS}" || true
fi

superset init

if [[ "${SUPERSET_BOOTSTRAP_DASHBOARD:-1}" != "0" ]]; then
    echo "[superset] Creando/verificando el dashboard Sales Analytics..."
    python /app/bootstrap_dashboard.py || echo "[superset] Aviso: no se pudo preparar el dashboard."
fi

if [[ -x /usr/bin/run-server.sh ]]; then
    exec /usr/bin/run-server.sh
fi

exec superset run -h 0.0.0.0 -p 8088 --with-threads
