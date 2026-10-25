# PoC — Integración y Calidad de Datos para Análisis Comercial

> Prueba de Concepto lista para **despliegue en la nube (Zeabur)** o **ejecución local con Docker**. Integra 4 fuentes heterogéneas, aplica calidad de datos medible y presenta resultados en **Jupyter Notebook** (evidencia ETL) + **Apache Superset** (dashboard).

---

## Objetivo

Demostrar la integración, limpieza, validación y visualización de datos comerciales para apoyar la toma de decisiones, con trazabilidad completa por KPI.

---

## Arquitectura (Cloud / Local)

```text
Jupyter Notebook (ETL) --> PostgreSQL (Data Warehouse - Star Schema) --> Apache Superset (Dashboard)
```

Todo desplegable con **Docker** o directamente en **Zeabur**.

---

## Estructura del Proyecto

```text
PoC_Analisis_Comercial/
├── 01_datos/                # CSV/Excel originales
├── 02_etl/
│   ├── *.py                 # Scripts ETL locales (SQLite + Power BI)
│   └── 01_etl_pipeline.ipynb # Notebook para PostgreSQL + Jupyter
├── 03_dw/
│   ├── schema.sql           # DDL PostgreSQL (Star Schema)
│   └── schema_sqlite.sql    # Respaldo esquema SQLite
├── 04_dashboard/
│   ├── kpi_views.sql        # Vistas SQLite
│   ├── dax_measures.txt     # Medidas DAX (Power BI)
│   └── README_SUPERSET.md   # Guía Apache Superset
├── 06_calidad/              # profile_report.md, log_rechazos.csv
├── 07_presentacion/         # Guion de presentación
├── docker/                  # Dockerfile + docker-compose.yml
├── zeabur/                  # Guía de despliegue en Zeabur
├── .env.example             # Variables de entorno
├── run_local.bat            # Levantar stack local
├── run_etl.bat              # ETL local SQLite
└── README.md
```

---

## Tecnologías

| Capa | Tecnología | Uso |
|---|---|---|
| ETL (Evidencia) | Jupyter Notebook + Pandas | Limpieza, homologación, validación y carga a PostgreSQL |
| Data Warehouse | PostgreSQL | Almacenamiento del modelo estrella |
| Dashboard | Apache Superset | Gráficos interactivos para toma de decisiones |
| Contenedores | Docker / Docker Compose | Ejecución portable en local/nube |
| Nube | Zeabur | Despliegue accesible por URL |
| Respaldos Locales | Python + SQLite + Power BI | Opción A funcional sin nube |

---

## Opciones de Ejecución

### Opción A: Local con Docker (Recomendado para pruebas)

1. Copiar variables: `copy .env.example .env`
2. Ejecutar: `run_local.bat` o `docker compose -f docker/docker-compose.yml up --build`
3. Acceder:
   - Jupyter: `http://localhost:8888` (token: `bi_poc`)
   - Superset: `http://localhost:8088` (admin / admin)
   - PostgreSQL: `localhost:5432`

### Opción B: Desplegar en Zeabur (Para entregar y que lo prueben)

Seguir paso a paso: [`zeabur/deploy.md`](zeabur/deploy.md)

### Opción C: Local con SQLite + Power BI (Respaldo)

```bash
run_etl.bat
```
Usar `03_dw/dw.db` con Power BI Desktop.

---

## Flujo de Demostración

1. **Jupyter Notebook** — Evidencia del ETL: lectura, nulos, duplicados, homologación, validación FK, reglas de negocio y carga a PostgreSQL.
2. **Apache Superset** — Conclusión: Dashboard `Sales Analytics` con 4 KPIs y filtros interactivos.
3. **Zeabur** — Evidenciar los 3 servicios funcionando.

---

## KPIs del Dashboard

| KPI | Descripción | Uso Gerencial |
|---|---|---|
| Evolución de Ventas | Serie temporal por fecha | Detectar tendencias y estacionalidad |
| Ventas por Categoría | Participación por categoría | Priorizar inventario/productos |
| Desempeño por Sucursal | Ranking + ticket promedio | Evaluar gestión comercial |
| Ventas por Segmento | Contribución por segmento | Dirigir campañas y fidelización |

**Filtros:** Fecha · Sucursal · Categoría · Segmento

---

## Calidad de Datos

Ver documentación completa:
- [`README.md` Técnico](#) — Técnicas aplicadas (nulos, duplicados, outliers, integridad, trazabilidad)
- [`05_lineage.md`](05_lineage.md) — Data Lineage por KPI
- [`06_calidad/profile_report.md`](06_calidad/profile_report.md) — Perfilado antes de limpiar
- [`06_calidad/log_rechazos.csv`](06_calidad/log_rechazos.csv) — Registros rechazados con motivo

---

## Notas para Entrega

- El repositorio debe subirse completo a GitHub para desplegar en Zeabur.
- Usar siempre `.env.example` como referencia, nunca subir `.env` real.
- El notebook `02_etl/01_etl_pipeline.ipynb` contiene la evidencia obligatoria para la defensa.
- Apache Superset es la herramienta de BI para la presentación en mesa de juntas.
