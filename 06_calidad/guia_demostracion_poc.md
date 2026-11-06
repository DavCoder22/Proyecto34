# Guía de demostración de la PoC — Perfilado y corrección de datos

## Objetivo
Demostrar en vivo qué está mal en los datos de origen y cómo el ETL los corrige, mostrando evidencias antes/después.

## Paso 1 — Abrir el entorno
```bat
cd "PoC_Analisis_Comercial"
run_local.bat
```
Abrir Jupyter y el archivo `02_etl/01_etl_pipeline.ipynb`.

## Lógica de detección (antes de compilar en Jupyter)

### Nulos
- `profile.py:15` → `df[c].isna().sum()` (y reemplazo de `""`/`"nan"` por `pd.NA` en columnas de texto).
- `quality_report.py:16` → `_nulls(df)` = `df.isna().sum().sum() + (df == "").sum().sum()`.

### Duplicados
- `profile.py:17` → `df.duplicated().sum()` (filas exactas).
- `quality_report.py:50-51` → `before.duplicated().sum()` vs `after.duplicated().sum()`.

### Errores / invalidez
- Fechas: `pd.to_datetime(..., errors="coerce").isna()` (ventas sin fecha válida se excluyen).
- FK inválidas: `quality_report.py:19-25` → `_invalid_fk` verifica `ventas[col].isin(parent)`.
- Rangos: `quality_report.py:60` → cantidad ≤ 0, precio < 0, descuento fuera de [0,1].
- Columnas basura: `clean.py:12` → columnas `Unnamed:` o con ≥99% nulos.

## Paso 2 — Mostrar el problema (perfilado inicial)
1. Ejecutar la celda de profiling (reconocimiento) sobre `01_datos/staging/`.
2. Mostrar `06_calidad/profile_report.md`:
   - `clientes`: 1006 filas, 6 duplicados exactos, columnas basura `Unnamed`, PK con 1000 únicos.
   - `productos`: 3 duplicados, `marca` con 5 nulos (4,07%).
   - `ventas`: 6870 filas pero solo 3600 `id_venta` únicos (duplicados), nulos en `canal_venta` y `metodo_pago`.
3. Mostrar `06_calidad/hallazgos.md` para cuantificar el impacto en el universo analítico.

## Paso 3 — Ejecutar el ETL
```bat
run_etl.bat
```
Revisar `06_calidad/log_rechazos.csv` y `run_etl_log.txt` para ver filas rechazadas y motivos.

## Paso 4 — Mostrar la corrección (datos limpios)
1. Abrir `01_datos/staging/clean_*.csv` y comparar con `stg_*.csv`.
2. Verificar en `03_dw/dw.db` las tablas dimensionales y de hechos.
3. Comparar `06_calidad/quality_comparison.csv` para métricas antes/después.

## Paso 5 — Mostrar el dashboard
1. Levantar Superset con `docker/docker-compose.superset.yml`.
2. Mostrar KPIs (ingresos, margen, transacciones) y filtros por categoría/sucursal/segmento.
3. Validar que no aparecen ventas huérfanas ni categorías duplicadas.

## Paso 6 — Cierre
- Resumir reglas aplicadas (`06_calidad/reglas_transformacion.md`).
- Advertir sobre tasa de rechazo y cobertura de fechas antes de proyectar.
- Mostrar evidencias en `evidencias/` (comparacion.png, datosProcesados.png, calidad).
