# PoC — Integración y Calidad de Datos para Análisis Comercial

> Prueba de Concepto lista para **despliegue en la nube (Northflank)** o **ejecución local con Docker**. Integra 4 fuentes heterogéneas, aplica calidad de datos medible y presenta resultados en **Jupyter Notebook** (evidencia ETL) + **Apache Superset** (dashboard).

---

## Objetivo

Demostrar la integración, limpieza, validación y visualización de datos comerciales para apoyar la toma de decisiones, con trazabilidad completa por KPI.

---

## Arquitectura (Cloud / Local)

```text
Jupyter Notebook (ETL) --> PostgreSQL (Data Warehouse - Star Schema) --> Apache Superset (Dashboard)
```

Todo desplegable con **Docker** o directamente en **Northflank**.

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
| Nube | Northflank | Despliegue accesible por URL |
| Respaldos Locales | Python + SQLite + Power BI | Opción A funcional sin nube |

---

## Configuración del Entorno

### Requisitos previos

- Python 3.10 o superior.
- Git para descargar o actualizar el repositorio.
- Navegador web para visualizar el dashboard HTML.
- Docker Desktop únicamente si se desea ejecutar PostgreSQL, Jupyter y Superset.

### Instalación en Windows PowerShell

Desde la carpeta raíz del proyecto:

```powershell
git clone https://github.com/DavCoder22/Proyecto34.git
cd PoC_Analisis_Comercial
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno, ejecutar una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

En Windows también se puede utilizar el intérprete del entorno directamente:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Instalación en Linux o macOS

```bash
git clone https://github.com/DavCoder22/Proyecto34.git
cd PoC_Analisis_Comercial
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

El entorno virtual `.venv` es local y no debe subirse al repositorio. Si se utiliza otro entorno virtual, ejecutar los comandos con su intérprete activo.

### Variables de entorno

La ejecución local del ETL no requiere credenciales: utiliza los archivos de `01_datos/raw` y genera `03_dw/dw.db`. Para Docker o PostgreSQL, copiar `.env.example` como `.env` y reemplazar las contraseñas de ejemplo:

```bash
cp .env.example .env
```

En Windows:

```bat
copy .env.example .env
```

No publicar `.env` ni credenciales reales.

---

## Opciones de Ejecución

### Opción A: Local con Docker (Recomendado para pruebas)

1. Copiar variables: `copy .env.example .env`
2. Ejecutar: `run_local.bat` o `docker compose -f docker/docker-compose.yml up --build`
3. Acceder:
   - Jupyter: `http://localhost:8888` (token: `bi_poc`)
   - Superset: `http://localhost:8088` (admin / admin)
   - PostgreSQL: `localhost:5432`

### Opción B: Desplegar en Northflank (Para entregar y que lo prueben)

1. Ir a [northflank.com](https://northflank.com) → Crear proyecto
2. Conectar repositorio GitHub `https://github.com/DavCoder22/Proyecto34.git`
3. Desplegar `PostgreSQL` (Addon/Service)
4. Desplegar `Jupyter` usando `docker/Dockerfile` con variables `JUPYTER_TOKEN` y `DATABASE_URL`
5. Desplegar `Apache Superset` conectado al mismo PostgreSQL
6. Acceder por las URLs públicas generadas

#### Archivos dentro de Jupyter en la nube

El `docker/Dockerfile` copia el repositorio completo dentro de `/home/jovyan/work` y ejecuta el ETL durante la construcción de la imagen. Por eso, después de cada redeploy deben estar disponibles en Jupyter `01_datos`, `02_etl`, `03_dw`, `04_dashboard` y `06_calidad`.

En Northflank configurar el contexto de construcción como la raíz del repositorio, seleccionar `docker/Dockerfile` y definir:

```text
JUPYTER_TOKEN=<token-seguro>
```

Después de reconstruir la imagen, abrir `02_etl/01_etl_pipeline.ipynb`. El ETL ya habrá sido ejecutado durante el build y sus resultados estarán en `03_dw/dw.db` y `06_calidad/`. Para volver a ejecutarlo manualmente desde una terminal Jupyter:

```bash
python 02_etl/main.py
python 04_dashboard/build_dashboard.py
```

El dashboard se puede abrir desde `04_dashboard/dashboard.html`. Si el servicio permite terminal, también se puede publicar temporalmente con:

```bash
python -m http.server 8000 --directory 04_dashboard
```

El puerto `8000` debe estar expuesto en Northflank para acceder a ese servidor. Jupyter continuará disponible en el puerto `8888`.

### Opción C: Local con SQLite + Power BI (Respaldo)

```bash
run_etl.bat
```
Usar `03_dw/dw.db` con Power BI Desktop.

### Evidencia académica del ETL

Desde la raíz del proyecto, ejecutar `python 02_etl/main.py` (o `run_etl.bat` en Windows). El proceso genera:

- `06_calidad/profile_report.md`: perfil de las fuentes antes de limpiar.
- `06_calidad/quality_comparison.md`: comparación cuantificable antes/después.
- `06_calidad/reglas_transformacion.md`: problema, regla, criterio y efecto esperado.
- `06_calidad/log_rechazos.csv`: filas rechazadas por integridad referencial.
- `03_dw/dw.db`: modelo estrella y vistas para el dashboard.

El notebook `02_etl/01_etl_pipeline.ipynb` ejecuta el mismo pipeline y muestra los cuatro indicadores: ingresos, unidades, margen bruto y transacciones.

Para generar una visualización local sin configurar un servidor, ejecutar `python 04_dashboard/build_dashboard.py` y abrir `04_dashboard/dashboard.html`. El HTML contiene tarjetas de los cuatro indicadores y gráficos de evolución, categoría, sucursal y segmento. Para una demo con filtros, usar la misma base `03_dw/dw.db` en Superset o Power BI.

---

## Flujo de Demostración

1. **Jupyter Notebook** — Evidencia del ETL: lectura, nulos, duplicados, homologación, validación FK, reglas de negocio y carga a PostgreSQL.
2. **Apache Superset** — Conclusión: Dashboard `Sales Analytics` con 4 KPIs y filtros interactivos.
3. **Northflank** — Evidenciar los 3 servicios funcionando.

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
- [`06_calidad/quality_comparison.md`](06_calidad/quality_comparison.md) — Evidencia antes/después
- [`06_calidad/reglas_transformacion.md`](06_calidad/reglas_transformacion.md) — Justificación de reglas
- [`06_calidad/hallazgos.md`](06_calidad/hallazgos.md) — Hallazgos y efecto en proyecciones

---

## Notas para Entrega

- El repositorio debe subirse completo a GitHub para desplegar en Zeabur.
- Usar siempre `.env.example` como referencia, nunca subir `.env` real.
- El notebook `02_etl/01_etl_pipeline.ipynb` contiene la evidencia obligatoria para la defensa.
- Apache Superset es la herramienta de BI para la presentación en mesa de juntas.
