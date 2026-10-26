# Desplegar Apache Superset en otra dirección

> Para Northflank, sigue la guía paso a paso: [NORTHFLANK_SUPERSET.md](NORTHFLANK_SUPERSET.md).

Esta guía deja Superset funcionando con datos reales de la PoC. El ETL usa `ETL_TARGET` para elegir el destino: `sqlite` en local o `postgres` para Neon/PostgreSQL. Superset se conecta a ese PostgreSQL y se publica en su propia URL.

## Opción 1 — Stack independiente con Docker (cualquier servidor o VPS)

Ideal si no quieres depender de Northflank. Levanta PostgreSQL + ETL + Superset en una sola dirección.

```bash
cp .env.example .env
# Edita .env: cambia contraseñas, SUPERSET_SECRET_KEY y, si quieres, SUPERSET_PORT
docker compose --env-file .env -f docker/docker-compose.superset.yml up -d --build
```

Verifica:

```bash
docker compose --env-file .env -f docker/docker-compose.superset.yml ps
docker compose --env-file .env -f docker/docker-compose.superset.yml logs -f etl
docker compose --env-file .env -f docker/docker-compose.superset.yml logs -f superset
```

Abre:

```text
http://IP_DEL_SERVIDOR:8088
```

Usuario y contraseña: los de `SUPERSET_ADMIN_USER` / `SUPERSET_ADMIN_PASS` (por defecto `admin` / `admin`).

Al entrar, el dashboard **Sales Analytics** ya debe aparecer en `Dashboards`, con la conexión `PoC DW`, los 4 datasets y los 4 gráficos creados automáticamente. Si defines `SUPERSET_BOOTSTRAP_FORCE=1` y reinicias Superset, el dashboard se elimina y se vuelve a crear.

Si ya tenías tablas creadas con un esquema anterior, bórralas una vez para aplicar la precisión monetaria actual:

```sql
DROP TABLE IF EXISTS fact_ventas, dim_tiempo, dim_cliente, dim_producto, dim_sucursal CASCADE;
```

El servicio `etl` corre una vez, carga las tablas en PostgreSQL y luego arranca Superset. Para recargar los datos después de cambiar los CSV:

```bash
docker compose --env-file .env -f docker/docker-compose.superset.yml run --rm etl
```

Si quieres un dominio (por ejemplo `https://bi.tudominio.com`), apunta un proxy inverso (Nginx, Caddy o Traefik) al puerto `8088` del servidor. Superset ya tiene `ENABLE_PROXY_FIX=True`.

## Opción 2 — Northflank con Neon (job ETL + un servicio Superset)

> Guía detallada con secret group, job ETL, health check, volumen persistente y solución de problemas: [NORTHFLANK_SUPERSET.md](NORTHFLANK_SUPERSET.md).

En este escenario Neon es la única base de datos y solo se crea un servicio adicional: **Superset en el puerto 8008**. No se necesita addon PostgreSQL en Northflank ni servicio Jupyter para el dashboard.

1. Crea el secret group `proyecto34-secrets` con:

```text
DATABASE_URL=postgresql+psycopg2://usuario:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
ETL_TARGET=postgres
LOAD_POSTGRES=1
REQUIRE_POSTGRES_LOAD=1
SUPERSET_SECRET_KEY=<clave-larga-y-aleatoria>
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASS=<password-fuerte>
SUPERSET_ADMIN_EMAIL=admin@poc.com
SUPERSET_PORT=8008
SUPERSET_METADATA_DATABASE_URL=sqlite:////app/superset_home/superset.db
SUPERSET_TALISMAN_ENABLED=false
SUPERSET_COOKIE_SECURE=false
SUPERSET_BOOTSTRAP_DASHBOARD=1
SUPERSET_DW_DATABASE_NAME=PoC DW
```

2. Crea el job **`proyecto34-etl`** con Dockerfile `docker/Dockerfile.etl`, contexto `.` y enlaza el secret group. Ejecútalo una vez.
3. Crea el servicio **`proyecto34-superset`** con Dockerfile `docker/superset/Dockerfile`, contexto `.`, puerto `8008` HTTP público, health check `/health`, volumen `/app/superset_home` y enlaza el secret group.
4. Copia la **URL pública de Superset** y abre el dashboard `Sales Analytics`.

## Configurar el dashboard en Superset

El despliegue crea automáticamente la conexión, los datasets, los 4 gráficos y el dashboard `Sales Analytics`. Esta sección sirve para personalizarlo o recrearlo manualmente si desactivas `SUPERSET_BOOTSTRAP_DASHBOARD`.

### 1. Conexión a la base del DW

`Settings` → `Database Connections` → `+ Database` → `PostgreSQL`:

```text
postgresql+psycopg2://usuario:password@postgres:5432/bi_dw
```

En Northflank usa la conexión directa de Neon (sin `-pooler` y con `?sslmode=require`). Prueba la conexión y guarda.

### 2. Datasets

Crea un dataset por cada vista KPI (recomendado porque ya traen agregados y porcentajes):

| Dataset | Para qué |
|---|---|
| `v_ventas_mes` | Evolución mensual |
| `v_ventas_categoria` | Ventas por categoría + participación |
| `v_ventas_sucursal` | Ranking por sucursal + ticket promedio |
| `v_ventas_segmento` | Ventas por segmento + ticket promedio |

También puedes usar las tablas base `fact_ventas`, `dim_tiempo`, `dim_cliente`, `dim_producto` y `dim_sucursal` para filtros y gráficos personalizados.

### 3. Los 4 gráficos

| KPI | Tipo | Eje / Dimensión | Métrica |
|---|---|---|---|
| Evolución de ventas | Line | `v_ventas_mes`: `anio`, `mes` | `SUM(venta_neta)` |
| Ventas por categoría | Bar | `v_ventas_categoria`: `categoria` | `SUM(venta_neta)` |
| Desempeño por sucursal | Bar | `v_ventas_sucursal`: `nombre_sucursal` | `SUM(venta_neta)` y `AVG(ticket_promedio)` |
| Ventas por segmento | Bar o Pie | `v_ventas_segmento`: `segmento` | `SUM(venta_neta)` |

### 4. Dashboard y filtros

1. `Dashboards` → `+ Dashboard` → nombre `Sales Analytics`.
2. Arrastra los 4 gráficos.
3. Agrega filtros nativos sobre `dim_sucursal.nombre_sucursal`, `dim_producto.categoria`, `dim_cliente.segmento` y `dim_tiempo.fecha`.
4. Guarda y publica.

## Verificación de datos

En Jupyter o en `psql`:

```sql
SELECT SUM(venta_neta) AS ingresos,
       SUM(cantidad) AS unidades,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS transacciones
FROM fact_ventas;
```

Resultado esperado: `7452222.71`, `13817`, `1966780.12`, `3587`.

## Problemas frecuentes

| Síntoma | Causa / solución |
|---|---|
| Superset muestra tablas vacías | El ETL no cargó PostgreSQL. Revisa `docker compose logs etl` o el job de Northflank. |
| `could not connect to server` | `DATABASE_URL` debe usar el host interno del PostgreSQL (`postgres` en Docker, host del addon en Northflank). |
| Los dashboards desaparecen al redeploy | La metadata está en SQLite sin volumen. Agrega el volumen `/app/superset_home` o usa PostgreSQL como metadata. |
| `No module named psycopg2` | Estás usando la imagen oficial sin el driver. Reconstruye con `docker/superset/Dockerfile`. |
| No abre el puerto configurado | En local usa 8088; en Northflank usa 8008 y expón ese puerto o configura el proxy inverso. |
| Superset redirige a HTTPS y falla | Deja `SUPERSET_TALISMAN_ENABLED=false` detrás de HTTP; con HTTPS puedes activarlo. |
