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
