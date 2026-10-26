# Desplegar Apache Superset en otra dirección

> Para Northflank, sigue la guía paso a paso: [NORTHFLANK_SUPERSET.md](NORTHFLANK_SUPERSET.md).

Esta guía deja Superset funcionando con datos reales de la PoC. El ETL ahora carga el DW en SQLite y, si `DATABASE_URL` apunta a PostgreSQL, también en PostgreSQL. Superset se conecta a ese PostgreSQL y se publica en una URL/puerto distinto al de Jupyter.

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

## Opción 2 — Northflank como segundo servicio (URL distinta)

> Guía detallada con job ETL, health check, volumen persistente y solución de problemas: [NORTHFLANK_SUPERSET.md](NORTHFLANK_SUPERSET.md).

1. Crea o reutiliza un addon **PostgreSQL** en el mismo proyecto. Copia su connection string interna.
2. Crea un servicio **Superset**:
   - Repositorio: `DavCoder22/Proyecto34`
   - Build context: raíz del repositorio
   - Dockerfile: `docker/superset/Dockerfile`
   - Puerto: `8088` (HTTP, público)
   - Health check: ruta `/health`
3. Variables de entorno del servicio Superset:

```text
SUPERSET_SECRET_KEY=<clave-larga-y-aleatoria>
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASS=<password-fuerte>
SUPERSET_ADMIN_EMAIL=admin@poc.com
SUPERSET_METADATA_DATABASE_URL=sqlite:////app/superset_home/superset.db
SUPERSET_TALISMAN_ENABLED=false
DATABASE_URL=postgresql+psycopg2://usuario:password@host:5432/bi_dw
SUPERSET_DW_DATABASE_NAME=PoC DW
SUPERSET_BOOTSTRAP_DASHBOARD=1
```

`DATABASE_URL` permite que Superset cree automáticamente la conexión al DW y el dashboard `Sales Analytics`. Si no lo defines, Superset arranca vacío y tendrías que crear la conexión/datasets/gráficos a mano.

Opcional: agrega un volumen persistente en `/app/superset_home` para no perder dashboards al redeploy. Si prefieres PostgreSQL como metadatos, crea una base `superset` y usa:

```text
SUPERSET_METADATA_DATABASE_URL=postgresql+psycopg2://usuario:password@host:5432/superset
```

4. Despliega y copia la **URL pública de Superset**. Esa es la "otra dirección".
5. Carga el DW en PostgreSQL:
   - **Importante:** vuelve a desplegar Jupyter con el `docker/Dockerfile` actualizado. El entrypoint nuevo ejecuta el ETL al arrancar.
   - En el servicio Jupyter, define `DATABASE_URL` con la connection string del PostgreSQL y `RUN_ETL_ON_START=1`; reinicia el servicio. El entrypoint cargará PostgreSQL.
   - Alternativa: crea un **job** de Northflank usando `docker/Dockerfile.etl`, con `DATABASE_URL`, `LOAD_POSTGRES=1` y `REQUIRE_POSTGRES_LOAD=1`, y ejecútalo una vez.
6. Entra a Superset y crea la conexión al DW (ver abajo).

## Configurar el dashboard en Superset

El despliegue crea automáticamente la conexión, los datasets, los 4 gráficos y el dashboard `Sales Analytics`. Esta sección sirve para personalizarlo o recrearlo manualmente si desactivas `SUPERSET_BOOTSTRAP_DASHBOARD`.

### 1. Conexión a la base del DW

`Settings` → `Database Connections` → `+ Database` → `PostgreSQL`:

```text
postgresql://bi_user:bi_pass@postgres:5432/bi_dw
```

En Northflank usa el host/puerto/usuario que te dio el addon. Prueba la conexión y guarda.

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
| No abre el puerto 8088 | Expón el puerto en el servidor/Northflank o configura el proxy inverso. |
| Superset redirige a HTTPS y falla | Deja `SUPERSET_TALISMAN_ENABLED=false` detrás de HTTP; con HTTPS puedes activarlo. |
