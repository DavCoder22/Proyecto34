# Dashboard en Apache Superset

## 0. Datos disponibles

El ETL carga el DW en SQLite (`03_dw/dw.db`) y, si `DATABASE_URL` está definida, también en PostgreSQL (`dim_*` y `fact_ventas`). Para Superset usa PostgreSQL.

Despliegue rápido del stack independiente:

```bash
cp .env.example .env
docker compose --env-file .env -f docker/docker-compose.superset.yml up -d --build
```

Guía completa (Docker/VPS y Northflank): [`deploy/SUPERSET_DEPLOY.md`](../deploy/SUPERSET_DEPLOY.md).

Al iniciar, el contenedor de Superset crea automáticamente la conexión al DW, los datasets, las 6 tarjetas KPI, los 4 gráficos y el dashboard `Sales Analytics`, con el tema institucional UCE. Los pasos de las secciones siguientes quedan como referencia para personalizar o recrear el dashboard manualmente.

Verifica que las tablas tengan datos:

```sql
SELECT COUNT(*) FROM fact_ventas;
SELECT SUM(venta_neta) FROM fact_ventas;
```

Resultado esperado: `6800` filas y `7452222.71` de ingresos.

---

## 1. Conectar al DW

1. Abrir Apache Superset → `Settings` → `Database Connections` → `+ Database`
2. Seleccionar `PostgreSQL`
3. Pegar la connection string:

En Docker Compose:

```text
postgresql://usuario:password@postgres:5432/bi_dw
```

En Northflank u otro servidor, usar el host, puerto, usuario y base que correspondan.

4. Probar la conexión y guardar.

---

## 2. Crear Datasets

Ir a `Data` → `Datasets` → `+ Dataset`. Se recomiendan las vistas KPI porque ya traen los agregados:

| Dataset | Origen | Uso |
|---|---|---|
| `v_ventas_mes` | Vista PostgreSQL | Evolución mensual |
| `v_ventas_categoria` | Vista PostgreSQL | Categoría + % de participación |
| `v_ventas_sucursal` | Vista PostgreSQL | Ranking + ticket promedio |
| `v_ventas_segmento` | Vista PostgreSQL | Segmento + ticket promedio |
| `v_kpis_consolidados` | Vista PostgreSQL | Tarjetas de indicadores consolidados |
| `fact_ventas` | Tabla | Medidas base y filtros |
| `dim_tiempo` | Tabla | Filtros por fecha/año/mes/trimestre |
| `dim_cliente` | Tabla | Filtro por segmento/ciudad |
| `dim_producto` | Tabla | Filtro por categoría/subcategoría |
| `dim_sucursal` | Tabla | Filtro por sucursal/región |

---

## 3. Crear las tarjetas KPI consolidadas

Usar el dataset `v_kpis_consolidados` y el gráfico `Big Number`:

| Tarjeta | Métrica | Formato |
|---|---|---|
| Ingresos Netos | `kpi_ingresos` | `$,.2f` |
| Unidades Vendidas | `kpi_unidades` | `,.0f` |
| Margen Bruto | `kpi_margen` | `$,.2f` |
| Transacciones | `kpi_transacciones` | `,.0f` |
| Ticket Promedio | `kpi_ticket_promedio` | `$,.2f` |
| Margen % | `kpi_margen_pct` | `.2%` |

Las cuatro primeras comprueban la utilidad analítica del universo integrado; ticket promedio y margen % añaden lectura comparativa de valor y rentabilidad.

## 4. Crear los 4 Gráficos

### KPI 1: Evolución de Ventas
- **Tipo:** Line Chart
- **Dataset:** `v_ventas_mes`
- **Eje X:** `anio`, `mes`
- **Métrica:** `SUM(venta_neta)`
- **Título:** `Evolución de Ventas por Mes`

### KPI 2: Ventas por Categoría
- **Tipo:** Bar Chart
- **Dataset:** `v_ventas_categoria`
- **Eje X:** `categoria`
- **Métrica:** `SUM(venta_neta)`
- **Orden:** Descendente
- **Título:** `Ventas por Categoría`

### KPI 3: Desempeño por Sucursal
- **Tipo:** Bar Chart
- **Dataset:** `v_ventas_sucursal`
- **Eje X:** `nombre_sucursal`
- **Métricas:** `SUM(venta_neta)` y `AVG(ticket_promedio)`
- **Título:** `Desempeño por Sucursal`

### KPI 4: Ventas por Segmento de Cliente
- **Tipo:** Bar Chart o Pie Chart
- **Dataset:** `v_ventas_segmento`
- **Eje X/Categoría:** `segmento`
- **Métrica:** `SUM(venta_neta)`
- **Título:** `Ventas por Segmento de Cliente`

---

## 5. Crear Dashboard

1. Ir a `Dashboards` → `+ Dashboard`
2. Nombre: `Sales Analytics`
3. Arrastrar las 6 tarjetas KPI y los 4 gráficos al lienzo
4. Agregar **filtros nativos**:
   - Fecha: `dim_tiempo.fecha`
   - Sucursal: `dim_sucursal.nombre_sucursal`
   - Categoría: `dim_producto.categoria`
   - Segmento: `dim_cliente.segmento`
5. Guardar y publicar.

---

## 6. Recargar datos

Si cambian los CSV, vuelve a ejecutar el ETL en Jupyter (`python 02_etl/main.py`) o el servicio de carga:

```bash
docker compose --env-file .env -f docker/docker-compose.superset.yml run --rm etl
```

Las vistas KPI se recrean automáticamente en cada carga.

---

## Sugerencias para la demo

- Mostrar **evolución temporal** para explicar tendencias.
- Filtrar por sucursal para mostrar análisis comparativo.
- Usar filtros cruzados para demostrar interactividad.
- Explicar: *"Estos 4 indicadores responden a las preguntas clave para la toma de decisiones comerciales."*
