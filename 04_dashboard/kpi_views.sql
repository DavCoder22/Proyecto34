-- Vistas SQL para el dashboard (Metabase / SQLite / Power BI via ODBC)
-- KPI 1: Evolucion de ventas por mes
CREATE VIEW IF NOT EXISTS v_ventas_mes AS
SELECT t.anio, t.mes, t.mes_nombre, t.trimestre,
       date(t.anio || '-' || printf('%02d', t.mes) || '-01') AS fecha,
       SUM(f.venta_neta) AS venta_neta,
       SUM(f.cantidad) AS unidades,
       COUNT(DISTINCT f.id_venta) AS num_ventas
FROM FactVentas f JOIN DimTiempo t ON f.id_tiempo=t.id_tiempo
GROUP BY t.anio, t.mes, t.mes_nombre, t.trimestre;

-- KPI 2: Ventas por categoria
CREATE VIEW IF NOT EXISTS v_ventas_categoria AS
SELECT p.categoria, SUM(f.venta_neta) AS venta_neta,
       SUM(f.venta_neta)*100.0/(SELECT SUM(venta_neta) FROM FactVentas) AS pct_participacion
FROM FactVentas f JOIN DimProducto p ON f.id_producto=p.id_producto
GROUP BY p.categoria;

-- KPI 3: Desempeno por sucursal
CREATE VIEW IF NOT EXISTS v_ventas_sucursal AS
SELECT s.id_sucursal, s.nombre_sucursal, s.ciudad, s.provincia, s.region,
       SUM(x.venta_neta) AS venta_neta,
       COUNT(*) AS num_ventas,
       AVG(x.ticket) AS ticket_promedio
FROM (SELECT id_sucursal, id_venta, SUM(venta_neta) AS venta_neta,
             SUM(venta_neta) AS ticket
      FROM FactVentas GROUP BY id_sucursal, id_venta) x
JOIN DimSucursal s ON x.id_sucursal=s.id_sucursal
GROUP BY s.id_sucursal, s.nombre_sucursal, s.ciudad, s.provincia, s.region;

-- KPI 4: Ventas por segmento de cliente
CREATE VIEW IF NOT EXISTS v_ventas_segmento AS
SELECT c.segmento, SUM(x.venta_neta) AS venta_neta,
       COUNT(*) AS num_ventas,
       AVG(x.ticket) AS ticket_promedio
FROM (SELECT id_cliente, id_venta, SUM(venta_neta) AS venta_neta,
             SUM(venta_neta) AS ticket
      FROM FactVentas GROUP BY id_cliente, id_venta) x
JOIN DimCliente c ON x.id_cliente=c.id_cliente
GROUP BY c.segmento;

-- Filtro auxiliar: canales y metodos de pago
CREATE VIEW IF NOT EXISTS v_ventas_canal AS
SELECT f.canal_venta, SUM(f.venta_neta) AS venta_neta, COUNT(*) AS lineas
FROM FactVentas f GROUP BY f.canal_venta;

-- KPIs consolidados para tarjetas del dashboard
CREATE VIEW IF NOT EXISTS v_kpis_consolidados AS
SELECT SUM(venta_neta) AS ingresos,
       SUM(cantidad) AS unidades,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS transacciones,
       SUM(venta_neta) * 1.0 / NULLIF(COUNT(DISTINCT id_venta), 0) AS ticket_promedio,
       SUM(margen) * 1.0 / NULLIF(SUM(venta_neta), 0) AS margen_pct
FROM FactVentas;

-- KPI 5: Ranking de marcas por unidades vendidas y venta neta
CREATE VIEW IF NOT EXISTS v_ventas_marca AS
SELECT p.marca,
       SUM(f.cantidad) AS unidades,
       SUM(f.venta_neta) AS venta_neta,
       SUM(f.venta_bruta - f.venta_neta) AS descuento_usd,
       AVG(f.descuento_pct) AS descuento_promedio
FROM FactVentas f JOIN DimProducto p ON f.id_producto = p.id_producto
WHERE p.marca IS NOT NULL AND TRIM(p.marca) <> ''
GROUP BY p.marca;

-- KPI 6: Productos con mayor descuento promedio (minimo 5 unidades)
CREATE VIEW IF NOT EXISTS v_descuento_producto AS
SELECT p.nombre_producto, p.categoria, p.marca,
       SUM(f.cantidad) AS unidades,
       SUM(f.venta_neta) AS venta_neta,
       SUM(f.venta_bruta - f.venta_neta) AS descuento_usd,
       AVG(f.descuento_pct) AS descuento_promedio
FROM FactVentas f JOIN DimProducto p ON f.id_producto = p.id_producto
GROUP BY p.id_producto, p.nombre_producto, p.categoria, p.marca
HAVING SUM(f.cantidad) >= 5;

-- Lider de marca por provincia
CREATE VIEW IF NOT EXISTS v_top_marca_provincia AS
WITH ranking AS (
    SELECT c.provincia, p.marca,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_neta) AS venta_neta,
           SUM(f.venta_bruta - f.venta_neta) AS descuento_usd,
           AVG(f.descuento_pct) AS descuento_promedio,
           ROW_NUMBER() OVER (
               PARTITION BY c.provincia
               ORDER BY SUM(f.cantidad) DESC, SUM(f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimCliente c ON f.id_cliente = c.id_cliente
    WHERE p.marca IS NOT NULL AND TRIM(p.marca) <> ''
    GROUP BY c.provincia, p.marca
)
SELECT provincia, marca, unidades, venta_neta, descuento_usd, descuento_promedio
FROM ranking WHERE rn = 1;

-- Lider de marca por sucursal
CREATE VIEW IF NOT EXISTS v_top_marca_sucursal AS
WITH ranking AS (
    SELECT s.nombre_sucursal, s.provincia,
           p.marca,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_neta) AS venta_neta,
           SUM(f.venta_bruta - f.venta_neta) AS descuento_usd,
           AVG(f.descuento_pct) AS descuento_promedio,
           ROW_NUMBER() OVER (
               PARTITION BY s.id_sucursal
               ORDER BY SUM(f.cantidad) DESC, SUM(f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimSucursal s ON f.id_sucursal = s.id_sucursal
    WHERE p.marca IS NOT NULL AND TRIM(p.marca) <> ''
    GROUP BY s.id_sucursal, s.nombre_sucursal, s.provincia, p.marca
)
SELECT nombre_sucursal, provincia, marca, unidades, venta_neta, descuento_usd, descuento_promedio
FROM ranking WHERE rn = 1;

-- Lider de producto por provincia
CREATE VIEW IF NOT EXISTS v_top_producto_provincia AS
WITH ranking AS (
    SELECT c.provincia, p.cod_producto, p.nombre_producto, p.categoria, p.marca,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_neta) AS venta_neta,
           ROW_NUMBER() OVER (
               PARTITION BY c.provincia
               ORDER BY SUM(f.cantidad) DESC, SUM(f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimCliente c ON f.id_cliente = c.id_cliente
    GROUP BY c.provincia, p.id_producto, p.cod_producto, p.nombre_producto, p.categoria, p.marca
)
SELECT provincia, cod_producto, nombre_producto, categoria, marca, unidades, venta_neta
FROM ranking WHERE rn = 1;

-- Lider de producto por sucursal
CREATE VIEW IF NOT EXISTS v_top_producto_sucursal AS
WITH ranking AS (
    SELECT s.nombre_sucursal, s.provincia,
           p.cod_producto, p.nombre_producto, p.categoria, p.marca,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_neta) AS venta_neta,
           ROW_NUMBER() OVER (
               PARTITION BY s.id_sucursal
               ORDER BY SUM(f.cantidad) DESC, SUM(f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimSucursal s ON f.id_sucursal = s.id_sucursal
    GROUP BY s.id_sucursal, s.nombre_sucursal, s.provincia,
             p.id_producto, p.cod_producto, p.nombre_producto, p.categoria, p.marca
)
SELECT nombre_sucursal, provincia, cod_producto, nombre_producto, categoria, marca, unidades, venta_neta
FROM ranking WHERE rn = 1;

-- Lider de categoria por provincia
CREATE VIEW IF NOT EXISTS v_top_categoria_provincia AS
WITH ranking AS (
    SELECT c.provincia, p.categoria,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_neta) AS venta_neta,
           ROW_NUMBER() OVER (
               PARTITION BY c.provincia
               ORDER BY SUM(f.cantidad) DESC, SUM(f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimCliente c ON f.id_cliente = c.id_cliente
    GROUP BY c.provincia, p.categoria
)
SELECT provincia, categoria, unidades, venta_neta
FROM ranking WHERE rn = 1;

-- Lider de categoria por sucursal
CREATE VIEW IF NOT EXISTS v_top_categoria_sucursal AS
WITH ranking AS (
    SELECT s.nombre_sucursal, s.provincia,
           p.categoria,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_neta) AS venta_neta,
           ROW_NUMBER() OVER (
               PARTITION BY s.id_sucursal
               ORDER BY SUM(f.cantidad) DESC, SUM(f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimSucursal s ON f.id_sucursal = s.id_sucursal
    GROUP BY s.id_sucursal, s.nombre_sucursal, s.provincia, p.categoria
)
SELECT nombre_sucursal, provincia, categoria, unidades, venta_neta
FROM ranking WHERE rn = 1;

-- Producto con mayor descuento promedio por provincia (minimo 5 unidades)
CREATE VIEW IF NOT EXISTS v_top_descuento_provincia AS
WITH ranking AS (
    SELECT c.provincia, p.nombre_producto, p.categoria, p.marca,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_bruta - f.venta_neta) AS descuento_usd,
           AVG(f.descuento_pct) AS descuento_promedio,
           ROW_NUMBER() OVER (
               PARTITION BY c.provincia
               ORDER BY AVG(f.descuento_pct) DESC, SUM(f.venta_bruta - f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimCliente c ON f.id_cliente = c.id_cliente
    GROUP BY c.provincia, p.id_producto, p.nombre_producto, p.categoria, p.marca
    HAVING SUM(f.cantidad) >= 5
)
SELECT provincia, nombre_producto, categoria, marca, unidades, descuento_usd, descuento_promedio
FROM ranking WHERE rn = 1;

-- Producto con mayor descuento promedio por sucursal (minimo 5 unidades)
CREATE VIEW IF NOT EXISTS v_top_descuento_sucursal AS
WITH ranking AS (
    SELECT s.nombre_sucursal, s.provincia,
           p.nombre_producto, p.categoria, p.marca,
           SUM(f.cantidad) AS unidades,
           SUM(f.venta_bruta - f.venta_neta) AS descuento_usd,
           AVG(f.descuento_pct) AS descuento_promedio,
           ROW_NUMBER() OVER (
               PARTITION BY s.id_sucursal
               ORDER BY AVG(f.descuento_pct) DESC, SUM(f.venta_bruta - f.venta_neta) DESC
           ) AS rn
    FROM FactVentas f
    JOIN DimProducto p ON f.id_producto = p.id_producto
    JOIN DimSucursal s ON f.id_sucursal = s.id_sucursal
    GROUP BY s.id_sucursal, s.nombre_sucursal, s.provincia,
             p.id_producto, p.nombre_producto, p.categoria, p.marca
    HAVING SUM(f.cantidad) >= 5
)
SELECT nombre_sucursal, provincia, nombre_producto, categoria, marca, unidades, descuento_usd, descuento_promedio
FROM ranking WHERE rn = 1;

-- =====================================================================
-- Vistas del modelo analitico ampliado (SQLite)
-- =====================================================================
CREATE VIEW IF NOT EXISTS v_ventas_detalle AS
SELECT f.id_venta_pk, f.id_venta, t.fecha, t.anio, t.mes, t.mes_nombre,
       t.trimestre, t.semana, t.dia_semana,
       c.provincia, c.ciudad AS ciudad_cliente, c.segmento,
       p.cod_producto, p.nombre_producto, p.categoria, p.subcategoria, p.marca,
       s.id_sucursal, s.nombre_sucursal, s.ciudad AS ciudad_sucursal,
       s.provincia AS provincia_sucursal, s.region,
       f.canal_venta, f.metodo_pago,
       f.cantidad, f.precio_unitario, f.descuento_pct,
       f.venta_bruta, (f.venta_bruta - f.venta_neta) AS descuento_usd,
       f.venta_neta, f.costo_total, f.margen
FROM FactVentas f
JOIN DimTiempo t ON f.id_tiempo = t.id_tiempo
JOIN DimCliente c ON f.id_cliente = c.id_cliente
JOIN DimProducto p ON f.id_producto = p.id_producto
JOIN DimSucursal s ON f.id_sucursal = s.id_sucursal;

CREATE VIEW IF NOT EXISTS v_ventas_marca AS
SELECT marca, SUM(cantidad) AS unidades, SUM(venta_neta) AS venta_neta,
       SUM(venta_bruta - venta_neta) AS descuento_usd,
       SUM(margen) AS margen, COUNT(DISTINCT id_venta) AS num_ventas,
       AVG(descuento_pct) AS descuento_promedio
FROM v_ventas_detalle
WHERE marca IS NOT NULL AND TRIM(marca) <> ''
GROUP BY marca;

CREATE VIEW IF NOT EXISTS v_categoria_provincia AS
SELECT provincia, categoria, SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       SUM(venta_bruta - venta_neta) AS descuento_usd,
       SUM(margen) AS margen, COUNT(DISTINCT id_venta) AS num_ventas
FROM v_ventas_detalle GROUP BY provincia, categoria;

CREATE VIEW IF NOT EXISTS v_sucursal_provincia AS
SELECT provincia_sucursal AS provincia, nombre_sucursal,
       SUM(venta_neta) AS venta_neta, SUM(cantidad) AS unidades,
       SUM(venta_bruta - venta_neta) AS descuento_usd,
       SUM(margen) AS margen, COUNT(DISTINCT id_venta) AS num_ventas,
       SUM(venta_neta) / NULLIF(COUNT(DISTINCT id_venta), 0) AS ticket_promedio
FROM v_ventas_detalle GROUP BY provincia_sucursal, nombre_sucursal;

CREATE VIEW IF NOT EXISTS v_descuento_categoria_provincia AS
SELECT provincia, categoria, SUM(venta_bruta) AS venta_bruta,
       SUM(venta_neta) AS venta_neta,
       SUM(venta_bruta - venta_neta) AS descuento_usd,
       AVG(descuento_pct) AS descuento_promedio,
       COUNT(DISTINCT id_venta) AS num_ventas
FROM v_ventas_detalle GROUP BY provincia, categoria;

CREATE VIEW IF NOT EXISTS v_descuento_sucursal AS
SELECT provincia_sucursal AS provincia, nombre_sucursal,
       SUM(venta_bruta) AS venta_bruta, SUM(venta_neta) AS venta_neta,
       SUM(venta_bruta - venta_neta) AS descuento_usd,
       AVG(descuento_pct) AS descuento_promedio,
       COUNT(DISTINCT id_venta) AS num_ventas
FROM v_ventas_detalle GROUP BY provincia_sucursal, nombre_sucursal;

DROP VIEW IF EXISTS v_rechazos_sucursal;
DROP VIEW IF EXISTS v_rechazos_motivo;
DROP VIEW IF EXISTS v_rechazos_fecha;
DROP VIEW IF EXISTS v_rechazos;
CREATE VIEW v_rechazos AS
SELECT r.id_venta, r.fecha_venta, r.cod_cliente, r.cod_producto,
       r.cod_sucursal,
       COALESCE(s.nombre_sucursal, r.cod_sucursal, 'Sucursal desconocida') AS nombre_sucursal,
       COALESCE(s.provincia, 'Provincia desconocida') AS provincia,
       COALESCE(s.region, 'Sin region') AS region,
       COALESCE(p.categoria, 'Sin categoria') AS categoria,
       COALESCE(p.marca, 'Sin marca') AS marca,
       r.cantidad, r.precio_unitario, r.descuento_pct,
       r.canal_venta, r.metodo_pago,
       COALESCE(r.motivo, 'Sin motivo') AS motivo, r.venta_perdida
FROM fact_rechazos r
LEFT JOIN DimSucursal s ON s.cod_sucursal = r.cod_sucursal
LEFT JOIN DimProducto p ON p.cod_producto = r.cod_producto;

CREATE VIEW IF NOT EXISTS v_rechazos_sucursal AS
SELECT nombre_sucursal, provincia, COUNT(*) AS num_rechazos,
       SUM(venta_perdida) AS venta_perdida
FROM v_rechazos GROUP BY nombre_sucursal, provincia;

CREATE VIEW IF NOT EXISTS v_rechazos_motivo AS
SELECT motivo, COUNT(*) AS num_rechazos, SUM(venta_perdida) AS venta_perdida
FROM v_rechazos GROUP BY motivo;

CREATE VIEW IF NOT EXISTS v_rechazos_fecha AS
SELECT strftime('%Y-%m', fecha_venta) AS mes, COUNT(*) AS num_rechazos,
       SUM(venta_perdida) AS venta_perdida
FROM v_rechazos WHERE fecha_venta IS NOT NULL GROUP BY mes;
