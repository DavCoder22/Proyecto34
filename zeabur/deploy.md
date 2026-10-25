# Despliegue en Zeabur (Nube)

Este proyecto está listo para ser desplegado en [zeabur.com](https://zeabur.com) para que terceros puedan probarlo mediante URLs públicas.

## Arquitectura

```text
Zeabur
├── PostgreSQL (Marketplace)  -> Data Warehouse (Star Schema)
├── Jupyter Notebook (Git/Docker) -> Evidencia del ETL
└── Apache Superset (Marketplace) -> Dashboard interactivo
```

---

## Paso 1: Subir repositorio a GitHub

1. Crear un repositorio en GitHub (privado o público).
2. Subir todo el proyecto `PoC_Analisis_Comercial/` al repositorio.
3. Verificar que existan: `docker/Dockerfile`, `03_dw/schema.sql`, `02_etl/01_etl_pipeline.ipynb`, `01_datos/`.

---

## Paso 2: Desplegar PostgreSQL

1. Ir a [zeabur.com](https://zeabur.com) → Crear proyecto → `Add Service` → `Marketplace` → `PostgreSQL`.
2. Esperar a que se despliegue.
3. Ir a `Variables` o `Connection` y copiar la **Connection String** (formato `postgresql://...`).

> El esquema `03_dw/schema.sql` se creará al cargarlo manualmente o puede ejecutarse desde Jupyter después del despliegue.

---

## Paso 3: Desplegar Jupyter Notebook (ETL)

1. En el mismo proyecto → `Add Service` → `Git` → Seleccionar tu repositorio.
2. Zeabur detectará automáticamente `docker/Dockerfile`.
3. Ir a `Variables` y agregar:
   | Variable | Valor |
   |---|---|
   | `JUPYTER_TOKEN` | `bi_poc` (o el que desees) |
   | `DATABASE_URL` | `postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB_NAME` (usar la connection string de Postgres) |
4. Desplegar y esperar (2-4 minutos).
5. Abrir la URL pública generada por Zeabur (ej: `https://xxx.zeabur.app` puerto 8888).

---

## Paso 4: Desplegar Apache Superset (Dashboard)

1. `Add Service` → `Marketplace` → `Apache Superset`.
2. Esperar inicialización (3-5 minutos).
3. Abrir la URL pública de Superset.
4. Iniciar sesión con las credenciales por defecto o las que configure Zeabur.
5. Ir a `Settings` → `Database Connections` → `+ Database` → `PostgreSQL`.
6. Pegar la misma `Connection String` y probar conexión.
7. Crear datasets desde `fact_ventas`, `dim_tiempo`, `dim_cliente`, `dim_producto`, `dim_sucursal`.
8. Crear dashboard `Sales Analytics` con los 4 KPIs.

Ver guía detallada en [`04_dashboard/README_SUPERSET.md`](../04_dashboard/README_SUPERSET.md)

---

## Orden de demostración para la defensa

1. **Abrir Jupyter** → Ejecutar `02_etl/01_etl_pipeline.ipynb` mostrando antes/después, limpieza, homologación y carga a PostgreSQL.
2. **Abrir Superset** → Mostrar dashboard `Sales Analytics` con los 4 gráficos interactivos y filtros.
3. **Mostrar Zeabur** → Evidenciar los 3 servicios en funcionamiento.

---

## Recomendaciones

- **Plan B:** Si hay latencia en nube, usar `run_local.bat` con Docker local.
- **Seguridad:** Cambiar `JUPYTER_TOKEN` y credenciales por valores distintos antes de entregar.
- **Datos:** Los archivos en `01_datos/` deben estar en el repo para que el notebook funcione.
- **RAM:** Usar Pandas (ya implementado), no PySpark.
