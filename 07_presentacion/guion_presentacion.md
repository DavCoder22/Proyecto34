# Guion de Presentación — Mesa de Juntas

**Proyecto:** Integración y Calidad de Datos para Análisis Comercial
**Audiencia:** Directores / Gerencia (toma de decisiones)
**Duración sugerida:** 20 min + 10-15 min Q&A
**Formato:** Presentación ejecutiva + demo en vivo del dashboard

---

## 🎯 Objetivo de la reunión

Mostrar cómo la integración y calidad de los datos permite **decisiones comerciales basadas en evidencia**, con un dashboard interactivo y trazabilidad completa.

---

## 🛠️ Tecnologías que se presentan

| Capa | Tecnología | Por qué se eligió |
|---|---|---|
| Extracción | Python (pandas) | Lectura de múltiples formatos (CSV, Excel) |
| Transformación | Python (pandas) | Reglas de negocio auditables y reproducibles |
| Almacenamiento | SQLite (PoC) / PostgreSQL-Snowflake (prod) | Portable hoy, escalable mañana |
| Calidad | Scripts propios + Great Expectations (prod) | Métricas medibles y log de rechazos |
| Visualización | **Power BI Desktop** | Conecta directo al DW, DAX para KPIs, filtros interactivos |
| Orquestación | `.bat` / Airflow (prod) | Ejecución reproducible |

> **Mensaje clave para la mesa:** "La herramienta de BI (Power BI) es la cara visible; por detrás hay un proceso de calidad que garantiza que los números sean confiables."

---

## 📋 Agenda y guion palabra por palabra

### 1. Contexto y objetivo (2 min)
> "Hoy tomamos decisiones comerciales con datos dispersos en 4 sistemas. Esta PoC integra esas fuentes, las limpia y las pone en un dashboard único para que podamos decidir con datos confiables."

### 2. Fuentes y arquitectura (3 min)
> "Tenemos 4 orígenes: clientes (CRM), sucursales (SQL), productos (Excel) y ventas (CSV). Pasan por staging, ETL con calidad, un modelo estrella y finalmente el dashboard."

Mostrar diagrama de arquitectura (5 capas).

### 3. Proceso ETL y calidad de datos (5 min)
> "No solo movimos datos: los limpiamos. Eliminamos 29 duplicados, homologamos 6 variantes de categoría, rechazamos 30 registros con claves inválidas y documentamos todo en un log de rechazos."

Mostrar `profile_report.md` y `log_rechazos.csv`.

### 4. Modelo dimensional (3 min)
> "El DW está en esquema estrella: una tabla de hechos (ventas) y 4 dimensiones (tiempo, cliente, producto, sucursal). Esto permite filtrar por fecha, sucursal, categoría y segmento en segundos."

### 5. Demo del dashboard — 4 KPIs (4 min)

**KPI 1 — Evolución de ventas**
> "¿Cómo van las ventas mes a mes? Serie temporal para detectar estacionalidad."

**KPI 2 — Ventas por categoría**
> "¿Qué categorías aportan más? Barras + % de participación para priorizar inventario."

**KPI 3 — Desempeño por sucursal**
> "¿Qué sucursales cumplen meta? Ranking + ticket promedio para coaching comercial."

**KPI 4 — Ventas por segmento**
> "¿Qué segmento de cliente es más rentable? Contribución + ticket promedio para campañas."

Demostrar filtros: Fecha · Sucursal · Categoría · Segmento.

### 6. Validación y limitaciones (2 min)
> "Validamos cuadre: el total del dashboard coincide con la fuente. Limitaciones: PoC con datos de 6 meses, sin carga incremental ni gobierno de datos aún."

### 7. Conclusiones (1 min)
> "Tenemos una base confiable para decidir. Próximo paso: automatizar la carga y escalar a producción."

---

## ❓ Preguntas modelo del jurado / directivos

1. **¿Por qué Python y no una herramienta ETL empresarial?**
   > "Para la PoC priorizamos reproducibilidad y costo cero. En producción se migraría a Airbyte + dbt + Airflow, manteniendo las mismas reglas."

2. **¿Cómo garantizan que los datos son correctos?**
   > "Log de rechazos, métricas de calidad antes/después y cuadre de totales dashboard vs fuente."

3. **¿Se puede actualizar automáticamente?**
   > "Hoy es carga full manual. Trabajo futuro: carga incremental y orquestación con Airflow."

4. **¿Qué pasa si entra un dato nuevo con error?**
   > "El validador lo rechaza y lo registra en `log_rechazos.csv` con el motivo."

5. **¿Cuánto cuesta escalar?**
   > "La PoC es gratuita (Python + SQLite + Power BI Desktop). Producción: Snowflake + Power BI Service (licencias)."

6. **¿Qué decisiones se pueden tomar hoy?**
   > "Priorizar categorías, asignar presupuesto a sucursales top, campañas por segmento, detectar estacionalidad."

---

## 📎 Material de respaldo

- Diagrama de arquitectura (slide)
- `profile_report.md` (calidad antes)
- `log_rechazos.csv` (casos rechazados)
- Capturas del dashboard + video demo (plan B)
- `05_lineage.md` (trazabilidad por KPI)