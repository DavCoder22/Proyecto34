-- Vistas KPI para PostgreSQL / Apache Superset
-- Se recrean en cada carga del ETL.

CREATE OR REPLACE VIEW v_ventas_mes AS
SELECT t.anio, t.mes, t.mes_nombre, t.trimestre,
       make_date(t.anio, t.mes, 1) AS fecha,
       SUM(f.venta_neta) AS venta_neta,
       SUM(f.cantidad) AS unidades,
       COUNT(DISTINCT f.id_venta) AS num_ventas
FROM fact_ventas f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
GROUP BY t.anio, t.mes, t.mes_nombre, t.trimestre;

CREATE OR REPLACE VIEW v_ventas_categoria AS
SELECT p.categoria,
       SUM(f.venta_neta) AS venta_neta,
       SUM(f.venta_neta) * 100.0 / NULLIF((SELECT SUM(venta_neta) FROM fact_ventas), 0) AS pct_participacion
FROM fact_ventas f
JOIN dim_producto p ON f.id_producto = p.id_producto
GROUP BY p.categoria;

CREATE OR REPLACE VIEW v_ventas_sucursal AS
SELECT s.id_sucursal, s.nombre_sucursal, s.ciudad, s.provincia, s.region,
       SUM(x.venta_neta) AS venta_neta,
       COUNT(*) AS num_ventas,
       AVG(x.ticket) AS ticket_promedio
FROM (
    SELECT id_sucursal, id_venta, SUM(venta_neta) AS venta_neta, SUM(venta_neta) AS ticket
    FROM fact_ventas
    GROUP BY id_sucursal, id_venta
) x
JOIN dim_sucursal s ON x.id_sucursal = s.id_sucursal
GROUP BY s.id_sucursal, s.nombre_sucursal, s.ciudad, s.provincia, s.region;

CREATE OR REPLACE VIEW v_ventas_segmento AS
SELECT c.segmento,
       SUM(x.venta_neta) AS venta_neta,
       COUNT(*) AS num_ventas,
       AVG(x.ticket) AS ticket_promedio
FROM (
    SELECT id_cliente, id_venta, SUM(venta_neta) AS venta_neta, SUM(venta_neta) AS ticket
    FROM fact_ventas
    GROUP BY id_cliente, id_venta
) x
JOIN dim_cliente c ON x.id_cliente = c.id_cliente
GROUP BY c.segmento;

CREATE OR REPLACE VIEW v_ventas_canal AS
SELECT f.canal_venta,
       SUM(f.venta_neta) AS venta_neta,
       COUNT(*) AS lineas
FROM fact_ventas f
GROUP BY f.canal_venta;

CREATE OR REPLACE VIEW v_kpis_consolidados AS
SELECT SUM(venta_neta) AS ingresos,
       SUM(cantidad) AS unidades,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS transacciones,
       SUM(venta_neta) / NULLIF(COUNT(DISTINCT id_venta), 0) AS ticket_promedio,
       SUM(margen) / NULLIF(SUM(venta_neta), 0) AS margen_pct
FROM fact_ventas;
