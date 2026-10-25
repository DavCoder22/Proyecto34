# Dashboard en Apache Superset

## 1. Conectar a PostgreSQL

1. Abrir Apache Superset → `Data` → `Databases` → `+ Database`
2. Seleccionar `PostgreSQL`
3. Pegar la `Connection String` de Zeabur/Postgres:
   ```text
   postgresql://usuario:password@host:puerto/nombre_db
   ```
4. Probar conexión y guardar.

---

## 2. Crear Datasets

Ir a `Data` → `Datasets` → `+ Dataset` y crear para:

| Dataset | Origen | Uso |
|---|---|---|
| `fact_ventas` | `fact_ventas` | Medidas (venta_neta, margen, cantidad) |
| `dim_tiempo` | `dim_tiempo` | Filtros por fecha/año/mes/trimestre |
| `dim_cliente` | `dim_cliente` | Filtro por segmento/ciudad |
| `dim_producto` | `dim_producto` | Filtro por categoría/subcategoría |
| `dim_sucursal` | `dim_sucursal` | Filtro por sucursal/región |

---

## 3. Crear los 4 Gráficos (KPIs)

### KPI 1: Evolución de Ventas (Serie Temporal)
- **Tipo:** Line Chart / Time-series Line
- **Dataset:** `fact_ventas` + `dim_tiempo` (join)
- **Eje X:** `dim_tiempo.fecha`
- **Métrica:** `SUM(fact_ventas.venta_neta)`
- **Título:** `Evolución de Ventas por Fecha`

### KPI 2: Ventas por Categoría
- **Tipo:** Bar Chart
- **Dataset:** `fact_ventas` + `dim_producto`
- **Eje X:** `dim_producto.categoria`
- **Métrica:** `SUM(fact_ventas.venta_neta)`
- **Orden:** Descendente
- **Título:** `Ventas por Categoría`

### KPI 3: Desempeño por Sucursal
- **Tipo:** Bar Chart
- **Dataset:** `fact_ventas` + `dim_sucursal`
- **Eje X:** `dim_sucursal.nombre_sucursal`
- **Métricas:** `SUM(fact_ventas.venta_neta)`, `AVG(fact_ventas.venta_neta)` (ticket promedio)
- **Título:** `Desempeño por Sucursal`

### KPI 4: Ventas por Segmento de Cliente
- **Tipo:** Bar Chart o Pie Chart
- **Dataset:** `fact_ventas` + `dim_cliente`
- **Eje X/Categoría:** `dim_cliente.segmento`
- **Métrica:** `SUM(fact_ventas.venta_neta)`
- **Título:** `Ventas por Segmento de Cliente`

---

## 4. Crear Dashboard

1. Ir a `Dashboards` → `+ Dashboard`
2. Nombre: `Sales Analytics`
3. Arrastrar los 4 gráficos al lienzo
4. Agregar **Filtros nativos**:
   - Fecha: `dim_tiempo.fecha`
   - Sucursal: `dim_sucursal.nombre_sucursal`
   - Categoría: `dim_producto.categoria`
   - Segmento: `dim_cliente.segmento`
5. Guardar y publicar.

---

## Sugerencias para la demo

- Mostrar **evolución temporal** para explicar tendencias.
- Filtrar por sucursal para mostrar análisis comparativo.
- Usar filtros cruzados para demostrar interactividad.
- Explicar: *"Estos 4 indicadores responden a las preguntas clave para la toma de decisiones comerciales."*
