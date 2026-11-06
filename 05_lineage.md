# Data Lineage por KPI

## KPI 1: Evolucion de ventas (serie temporal)
ventas_sucursales.csv -> stg_ventas -> clean_ventas (dedup, fechas, descuento) -> FactVentas (venta_neta) -> DimTiempo (mes/trimestre) -> v_ventas_mes -> grafico lineas

## KPI 2: Ventas por categoria
productos.xlsx -> stg_productos -> clean_productos (homologa categoria) -> DimProducto -> FactVentas -> v_ventas_categoria -> barras + % participacion

## KPI 3: Desempeno por sucursal
sucursales.csv -> stg_sucursales -> DimSucursal -> FactVentas -> v_ventas_sucursal -> ranking + ticket promedio

## KPI 4: Ventas por segmento
clientes.csv -> stg_clientes -> clean (segmento homologado) -> DimCliente -> FactVentas -> v_ventas_segmento -> dona + ticket promedio

## KPI 5: Marca mas vendida
productos.xlsx -> stg_productos -> clean_productos (marca homologada) -> DimProducto -> FactVentas (cantidad, venta_neta) -> v_ventas_marca / v_top_marca_provincia / v_top_marca_sucursal -> ranking de marcas y tarjeta "Marca mas vendida"

## KPI 6: Productos con mayor descuento
ventas_sucursales.csv -> stg_ventas -> clean_ventas (descuento validado) -> FactVentas (descuento_pct, venta_bruta, venta_neta) -> v_descuento_producto / v_top_descuento_provincia / v_top_descuento_sucursal -> barras de descuento promedio y monto descontado

## KPI 7: Lideres por provincia y sucursal
DimCliente (provincia) / DimSucursal -> FactVentas -> DimProducto (categoria, producto, marca) -> v_top_categoria_* / v_top_producto_* / v_top_marca_* / v_top_descuento_* -> tabla territorial del dashboard

Los rankings de "mas vendido" usan `SUM(cantidad)` como metrica principal y `SUM(venta_neta)` como criterio de desempate. El mayor descuento usa `AVG(descuento_pct)` con un minimo de 5 unidades para evitar conclusiones sobre productos con una sola venta.

## Cuadre de exactitud
Total venta_neta dashboard = SUM(FactVentas.venta_neta) = 7,452,222.71
Control vs fuente: aplicar las mismas reglas (venta_neta = cantidad*precio*(1-descuento)) sobre stg_ventas y comparar totales.

## Indicadores consolidados

| Indicador | Expresión sobre `FactVentas` | Resultado ejecutado |
|---|---|---:|
| Ingresos por ventas | `SUM(venta_neta)` | 7,452,222.71 |
| Unidades vendidas | `SUM(cantidad)` | 13,817 |
| Margen bruto | `SUM(margen)` | 1,966,780.12 |
| Número de transacciones | `COUNT(DISTINCT id_venta)` | 3,587 |
| Ticket promedio | `SUM(venta_neta) / COUNT(DISTINCT id_venta)` | 2,077.56 |
| Margen % | `SUM(margen) / SUM(venta_neta)` | 26.39 % |

El ticket promedio se calcula por transacción: primero se suman las líneas de cada `id_venta` y después se obtiene el promedio. Así no se sesga el resultado por ventas con más productos.

Las mismas vistas existen en PostgreSQL (`04_dashboard/kpi_views_postgres.sql`) para que Apache Superset consuma el DW sin recalcular las reglas de negocio.
