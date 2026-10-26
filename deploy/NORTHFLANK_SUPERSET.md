# Desplegar Apache Superset en Northflank (proyecto34)

Guía para el escenario real de la PoC:

- **Neon** como base de datos.
- **Un job ETL** que carga los datos en Neon.
- **Un único servicio Superset** que publica el dashboard en el puerto **8008**.

No se necesita un addon PostgreSQL en Northflank ni un servicio Jupyter para que el dashboard funcione.

## Arquitectura

```text
                         Neon (PostgreSQL)
                        /                 \
                       /                   \
          Job ETL (Dockerfile.etl)     Servicio Superset
          carga originales + DW        (docker/superset/Dockerfile)
                                         puerto 8008
```

El job ETL crea en Neon:

- Datos originales: `stg_clientes`, `stg_sucursales`, `stg_productos`, `stg_ventas`.
- Datos transformados: `clean_clientes`, `clean_sucursales`, `clean_productos`, `clean_ventas`.
- Data warehouse: `dim_tiempo`, `dim_cliente`, `dim_producto`, `dim_sucursal`, `fact_ventas`.
- Vistas del dashboard: `v_ventas_mes`, `v_ventas_categoria`, `v_ventas_sucursal`, `v_ventas_segmento`.

El servicio Superset se conecta a Neon, crea el dashboard `Sales Analytics` y publica la URL de acceso.

## Datos del proyecto

| Dato | Valor |
|---|---|
| Proyecto Northflank | `proyecto34` |
| Repositorio | `DavCoder22/Proyecto34` |
| Rama | `main` |
| Puerto público de Superset | `8008` |
| Base de datos | Neon (conexión directa) |

## Paso 0. Subir los cambios a GitHub

Northflank construye desde GitHub. Antes de crear o actualizar los recursos, verifica que estén en `main`:

```bash
git add docker/Dockerfile.etl docker/superset/superset_config.py docker/superset/entrypoint.sh deploy/
git commit -m "fix: configurar Superset en 8008 para Northflank"
git push origin main
```

Archivos mínimos que deben existir en `main`:

- `docker/Dockerfile.etl`
- `docker/superset/Dockerfile`
- `docker/superset/entrypoint.sh`
- `docker/superset/superset_config.py`
- `docker/superset/bootstrap_dashboard.py`
- `04_dashboard/kpi_views_postgres.sql`
- `03_dw/schema.sql`
- `02_etl/load.py`
- `requirements.txt`

## Paso 1. Preparar Neon

1. Entra a [neon.com](https://neon.com) y abre tu proyecto.
2. En **Connect**, copia la **conexión directa**, sin `-pooler`.
3. La URL debe quedar así:

```text
postgresql+psycopg2://usuario:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
```

4. Conserva `?sslmode=require`.
5. Usa el prefijo `postgresql+psycopg2://`. Si Neon entrega `postgresql://`, el código lo normaliza, pero el prefijo explícito evita errores de driver.

## Paso 2. Crear el secret group

1. En Northflank, abre el proyecto `proyecto34`.
2. **Create new → Secret group**.
3. Nombre: `proyecto34-secrets`.
4. Agrega estas variables:

```text
DATABASE_URL=postgresql+psycopg2://usuario:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
ETL_TARGET=postgres
LOAD_POSTGRES=1
REQUIRE_POSTGRES_LOAD=1

SUPERSET_SECRET_KEY=<clave-larga-y-aleatoria>
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASS=<password-fuerte>
SUPERSET_ADMIN_EMAIL=admin@poc.com
SUPERSET_CREATE_ADMIN=1

SUPERSET_PORT=8008
SUPERSET_METADATA_DATABASE_URL=sqlite:////app/superset_home/superset.db
SUPERSET_TALISMAN_ENABLED=false
SUPERSET_COOKIE_SECURE=false
SUPERSET_BOOTSTRAP_DASHBOARD=1
SUPERSET_DW_DATABASE_NAME=PoC DW
```

Genera la clave con:

```bash
openssl rand -hex 32
```

Notas:

- `ETL_TARGET=postgres` es obligatorio para que el job escriba en Neon y no en SQLite.
- `SUPERSET_PORT=8008` debe coincidir con el puerto del servicio Superset en Northflank.
- La plantilla completa está en [`northflank.env.example`](northflank.env.example). No subas credenciales reales.
- Para la metadata de Superset se usa SQLite dentro de `/app/superset_home`; por eso el servicio necesita un volumen persistente.
- Si prefieres metadata en PostgreSQL, crea una base separada llamada `superset` en Neon y usa:
  `SUPERSET_METADATA_DATABASE_URL=postgresql+psycopg2://.../superset?sslmode=require`.

## Paso 3. Crear el job ETL

Este job carga Neon. Debe ejecutarse **antes** de abrir el dashboard.

1. En el proyecto: **Create new → Job**.
2. Nombre: `proyecto34-etl`.
3. Fuente: **Git repository**.
4. Repositorio: `DavCoder22/Proyecto34`.
5. Rama: `main`.
6. Build type: **Dockerfile**.
7. Dockerfile path: `docker/Dockerfile.etl`.
8. Build context: `.` (raíz del repositorio).
9. Runtime environment: enlaza el secret group `proyecto34-secrets`.
10. Crea el job y ejecútalo con **Run job**. Si el job ya existe, solo actualiza el repositorio y vuelve a ejecutarlo.

El Dockerfile ya define por defecto:

```text
ETL_TARGET=postgres
LOAD_POSTGRES=1
REQUIRE_POSTGRES_LOAD=1
```

En los logs debes ver:

```text
[LOAD] DW PostgreSQL actualizado en ...
=== PIPELINE OK ===
Ventas fact filas: 6800
```

Para comprobar en Neon:

```sql
SELECT 'stg_ventas' AS tabla, COUNT(*) FROM stg_ventas
UNION ALL
SELECT 'clean_ventas', COUNT(*) FROM clean_ventas
UNION ALL
SELECT 'fact_ventas', COUNT(*) FROM fact_ventas;
```

Resultado esperado: `6870`, `6800` y `6800`.

Si el job falla:

- Revisa que `DATABASE_URL` sea la conexión directa de Neon.
- Confirma `?sslmode=require`.
- Confirma `ETL_TARGET=postgres`.
- Revisa el mensaje `No se pudo cargar a PostgreSQL` en los logs.

## Paso 4. Crear el único servicio Superset

1. En el proyecto: **Create new → Service → Combined service**.
2. Nombre: `proyecto34-superset`.
3. Fuente: **Git repository**.
4. Repositorio: `DavCoder22/Proyecto34`.
5. Rama: `main`.
6. Build type: **Dockerfile**.
7. Dockerfile path: `docker/superset/Dockerfile`.
8. Build context: `.` (raíz del repositorio).
9. Networking:
   - Puerto: `8008`.
   - Protocolo: `HTTP`.
   - Accesibilidad: `Public`.
   - No uses `8088` en la nube: el puerto del servicio y `SUPERSET_PORT` deben ser `8008`.
10. Health check:
    - Protocolo: `HTTP`.
    - Path: `/health`.
    - Puerto: `8008`.
    - Initial delay: `120` segundos.
    - Interval: `10` segundos.
    - Timeout: `5` segundos.
    - Failure threshold: `5`.
11. Recursos recomendados para Sandbox:
    - `0.5 vCPU`.
    - `1 GB` de RAM.
12. Volumen persistente:
    - Mount path: `/app/superset_home`.
    - Tamaño: `1 GB`.
13. Environment:
    - Enlaza el secret group `proyecto34-secrets`.
    - Verifica que incluya `SUPERSET_PORT=8008` y `DATABASE_URL` de Neon.
14. Crea el servicio y espera el build. Si el servicio ya existe, cambia su puerto a `8008`, confirma `SUPERSET_PORT=8008` en el secret group y redespliega.

> `EXPOSE 8088` en el Dockerfile es solo el valor por defecto local. En Northflank el puerto real se define con `SUPERSET_PORT=8008` y el puerto del servicio. Si prefieres `8088`, cambia ambos a `8088`.

## Paso 5. Verificar los logs

En **Observe → Logs** del servicio Superset busca:

```text
[superset] Inicializando base de metadatos...
[superset] Creando/verificando el dashboard Sales Analytics...
[bootstrap] Dashboard Sales Analytics creado correctamente.
Listening at: http://0.0.0.0:8008
```

Si aparece:

```text
[bootstrap] Esperando vistas KPI en PostgreSQL...
```

el job ETL todavía no cargó las vistas o `DATABASE_URL` no apunta a Neon. Ejecuta de nuevo el job y reinicia Superset.

## Paso 6. Abrir el dashboard

1. Abre la URL pública del servicio Superset (**Overview → Domains**).
2. Inicia sesión con `SUPERSET_ADMIN_USER` y `SUPERSET_ADMIN_PASS`.
3. Ve a **Dashboards → Sales Analytics**.
4. URL directa:

```text
https://<url-publica-de-northflank>/superset/dashboard/sales-analytics/
```

## Paso 7. Verificar los datos del dashboard

En SQL Lab o en Neon:

```sql
SELECT SUM(venta_neta) AS ingresos,
       SUM(cantidad) AS unidades,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS transacciones
FROM fact_ventas;
```

Resultado esperado:

```text
ingresos      | unidades | margen        | transacciones
7452222.71    | 13817    | 1966780.12    | 3587
```

## Opcional: Jupyter en la nube

Para el dashboard no necesitas Jupyter. Si además quieres el notebook en la nube:

1. Crea un servicio con `docker/Dockerfile`.
2. Puerto `8888` HTTP público.
3. Variables:

```text
JUPYTER_TOKEN=<token-seguro>
DATABASE_URL=postgresql+psycopg2://usuario:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
ETL_TARGET=postgres
RUN_ETL_ON_START=1
```

4. En local, en cambio, usa `ETL_TARGET=sqlite` para que el notebook trabaje con `03_dw/dw.db` y no con Neon.

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| El build no encuentra el Dockerfile | Path o contexto incorrecto | Dockerfile `docker/superset/Dockerfile`, contexto `.` |
| `No module named psycopg2` | Se usó la imagen oficial de Superset | Usa `docker/superset/Dockerfile` del repositorio |
| El servicio falla el health check | Puerto o tiempo de arranque incorrecto | Puerto `8008`, `/health`, initial delay `120` s y 1 GB RAM |
| El dashboard no aparece | El job ETL no cargó las vistas en Neon | Ejecuta el job y reinicia Superset |
| El dashboard desaparece tras redeploy | Metadata SQLite sin volumen | Monta `/app/superset_home` o usa una base `superset` en Neon |
| Neon rechaza la conexión | Falta `sslmode=require` o se usó `-pooler` | Usa la conexión directa de Neon |
| `could not connect to server` | `DATABASE_URL` incorrecta | Copia de nuevo la URL directa de Neon |
| El ETL no escribe en Neon | `ETL_TARGET` no es `postgres` | Define `ETL_TARGET=postgres` en el secret group |
| No puedo entrar con la contraseña nueva | El usuario admin ya existía | Ejecuta `superset fab reset-password` o recrea el volumen |
| El servicio responde en 8088 y no en 8008 | `SUPERSET_PORT` y puerto del servicio no coinciden | Usa `8008` en ambos |

## Checklist

- [ ] Repositorio `DavCoder22/Proyecto34` actualizado en `main`.
- [ ] Neon tiene la conexión directa con `sslmode=require`.
- [ ] Secret group `proyecto34-secrets` creado y enlazado.
- [ ] Job ETL ejecutado con `Ventas fact filas: 6800`.
- [ ] Servicio `proyecto34-superset` en puerto `8008` y público.
- [ ] Volumen `/app/superset_home` montado.
- [ ] Log con `[bootstrap] Dashboard Sales Analytics creado correctamente.`
- [ ] URL pública abre el login de Superset.
- [ ] Dashboard `Sales Analytics` muestra los cuatro gráficos.
- [ ] Credenciales de administrador disponibles para la demo.
