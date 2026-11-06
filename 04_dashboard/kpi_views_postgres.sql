-- Vistas KPI para PostgreSQL / Apache Superset
-- Se recrean en cada carga del ETL.
-- Modelo analitico: un hecho de ventas validas (fact_ventas) y un hecho de
-- rechazos (fact_rechazos) para medir perdidas por sucursal y fecha.

-- =====================================================================
-- VISTA UNIFICADA A NIVEL DE DETALLE (habilita cross-filtering completo)
-- =====================================================================
DROP VIEW IF EXISTS v_ventas_detalle CASCADE;
CREATE VIEW v_ventas_detalle AS
SELECT f.id_venta_pk,
       f.id_venta,
       t.fecha,
       t.anio,
       t.mes,
       t.mes_nombre,
       t.trimestre,
       t.semana,
       t.dia_semana,
       c.provincia,
       c.ciudad AS ciudad_cliente,
       c.segmento,
       p.cod_producto,
       p.nombre_producto,
       p.categoria,
       p.subcategoria,
       p.marca,
       s.id_sucursal,
       s.nombre_sucursal,
       s.ciudad AS ciudad_sucursal,
       s.provincia AS provincia_sucursal,
       s.region,
       f.canal_venta,
       f.metodo_pago,
       f.cantidad,
       f.precio_unitario,
       f.descuento_pct,
       f.venta_bruta,
       (f.venta_bruta - f.venta_neta) AS descuento_usd,
       f.venta_neta,
       f.costo_total,
       f.margen
FROM fact_ventas f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
JOIN dim_cliente c ON f.id_cliente = c.id_cliente
JOIN dim_producto p ON f.id_producto = p.id_producto
JOIN dim_sucursal s ON f.id_sucursal = s.id_sucursal;

-- =====================================================================
-- VISTAS DE VENTAS AGREGADAS
-- =====================================================================
DROP VIEW IF EXISTS v_ventas_mes CASCADE;
CREATE VIEW v_ventas_mes AS
SELECT anio, mes, mes_nombre, trimestre,
       make_date(anio, mes, 1) AS fecha,
       SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       COUNT(DISTINCT id_venta) AS num_ventas
FROM v_ventas_detalle
GROUP BY anio, mes, mes_nombre, trimestre;

DROP VIEW IF EXISTS v_ventas_categoria CASCADE;
CREATE VIEW v_ventas_categoria AS
SELECT categoria,
       SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       SUM(descuento_usd) AS descuento_usd,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS num_ventas,
       SUM(venta_neta) * 100.0 / NULLIF((SELECT SUM(venta_neta) FROM fact_ventas), 0) AS pct_participacion
FROM v_ventas_detalle
GROUP BY categoria;

DROP VIEW IF EXISTS v_ventas_marca CASCADE;
CREATE VIEW v_ventas_marca AS
SELECT marca,
       SUM(cantidad) AS unidades,
       SUM(venta_neta) AS venta_neta,
       SUM(descuento_usd) AS descuento_usd,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS num_ventas,
       AVG(descuento_pct) AS descuento_promedio
FROM v_ventas_detalle
WHERE marca IS NOT NULL AND TRIM(marca) <> ''
GROUP BY marca;

DROP VIEW IF EXISTS v_ventas_sucursal CASCADE;
CREATE VIEW v_ventas_sucursal AS
SELECT id_sucursal,
       nombre_sucursal,
       ciudad_sucursal,
       provincia_sucursal,
       region,
       SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       SUM(descuento_usd) AS descuento_usd,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS num_ventas,
       SUM(venta_neta) / NULLIF(COUNT(DISTINCT id_venta), 0) AS ticket_promedio
FROM v_ventas_detalle
GROUP BY id_sucursal, nombre_sucursal, ciudad_sucursal, provincia_sucursal, region;

DROP VIEW IF EXISTS v_ventas_segmento CASCADE;
CREATE VIEW v_ventas_segmento AS
SELECT segmento,
       SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       SUM(descuento_usd) AS descuento_usd,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS num_ventas,
       SUM(venta_neta) / NULLIF(COUNT(DISTINCT id_venta), 0) AS ticket_promedio
FROM v_ventas_detalle
GROUP BY segmento;

DROP VIEW IF EXISTS v_ventas_canal CASCADE;
CREATE VIEW v_ventas_canal AS
SELECT canal_venta,
       SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       COUNT(*) AS lineas
FROM v_ventas_detalle
GROUP BY canal_venta;

-- =====================================================================
-- MATRICES DE DECISION: categoria y sucursal dentro de cada provincia
-- =====================================================================
DROP VIEW IF EXISTS v_categoria_provincia CASCADE;
CREATE VIEW v_categoria_provincia AS
SELECT provincia,
       categoria,
       SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       SUM(descuento_usd) AS descuento_usd,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS num_ventas
FROM v_ventas_detalle
GROUP BY provincia, categoria;

DROP VIEW IF EXISTS v_sucursal_provincia CASCADE;
CREATE VIEW v_sucursal_provincia AS
SELECT provincia_sucursal AS provincia,
       nombre_sucursal,
       SUM(venta_neta) AS venta_neta,
       SUM(cantidad) AS unidades,
       SUM(descuento_usd) AS descuento_usd,
       SUM(margen) AS margen,
       COUNT(DISTINCT id_venta) AS num_ventas,
       SUM(venta_neta) / NULLIF(COUNT(DISTINCT id_venta), 0) AS ticket_promedio
FROM v_ventas_detalle
GROUP BY provincia_sucursal, nombre_sucursal;

DROP VIEW IF EXISTS v_descuento_categoria_provincia CASCADE;
CREATE VIEW v_descuento_categoria_provincia AS
SELECT provincia,
       categoria,
       SUM(venta_bruta) AS venta_bruta,
       SUM(venta_neta) AS venta_neta,
       SUM(descuento_usd) AS descuento_usd,
       AVG(descuento_pct) AS descuento_promedio,
       COUNT(DISTINCT id_venta) AS num_ventas
FROM v_ventas_detalle
GROUP BY provincia, categoria;

DROP VIEW IF EXISTS v_descuento_sucursal CASCADE;
CREATE VIEW v_descuento_sucursal AS
SELECT provincia_sucursal AS provincia,
       nombre_sucursal,
       SUM(venta_bruta) AS venta_bruta,
       SUM(venta_neta) AS venta_neta,
       SUM(descuento_usd) AS descuento_usd,
       AVG(descuento_pct) AS descuento_promedio,
       COUNT(DISTINCT id_venta) AS num_ventas
FROM v_ventas_detalle
GROUP BY provincia_sucursal, nombre_sucursal;

-- =====================================================================
-- RANKINGS PARA DECISION
-- =====================================================================
DROP VIEW IF EXISTS v_top_marca_provincia CASCADE;
CREATE VIEW v_top_marca_provincia AS
WITH ranking AS (
    SELECT provincia, marca,
           SUM(cantidad) AS unidades,
           SUM(venta_neta) AS venta_neta,
           SUM(descuento_usd) AS descuento_usd,
           ROW_NUMBER() OVER (
               PARTITION BY provincia
               ORDER BY SUM(cantidad) DESC, SUM(venta_neta) DESC
           ) AS rn
    FROM v_ventas_detalle
    WHERE marca IS NOT NULL AND TRIM(marca) <> ''
    GROUP BY provincia, marca
)
SELECT provincia, marca, unidades, venta_neta, descuento_usd
FROM ranking WHERE rn = 1;

DROP VIEW IF EXISTS v_top_categoria_sucursal CASCADE;
CREATE VIEW v_top_categoria_sucursal AS
WITH ranking AS (
    SELECT nombre_sucursal, provincia_sucursal AS provincia, categoria,
           SUM(cantidad) AS unidades,
           SUM(venta_neta) AS venta_neta,
           ROW_NUMBER() OVER (
               PARTITION BY nombre_sucursal
               ORDER BY SUM(cantidad) DESC, SUM(venta_neta) DESC
           ) AS rn
    FROM v_ventas_detalle
    GROUP BY nombre_sucursal, provincia_sucursal, categoria
)
SELECT nombre_sucursal, provincia, categoria, unidades, venta_neta
FROM ranking WHERE rn = 1;

DROP VIEW IF EXISTS v_top_producto_sucursal CASCADE;
CREATE VIEW v_top_producto_sucursal AS
WITH ranking AS (
    SELECT nombre_sucursal, provincia_sucursal AS provincia,
           cod_producto, nombre_producto, categoria, marca,
           SUM(cantidad) AS unidades,
           SUM(venta_neta) AS venta_neta,
           ROW_NUMBER() OVER (
               PARTITION BY nombre_sucursal
               ORDER BY SUM(cantidad) DESC, SUM(venta_neta) DESC
           ) AS rn
    FROM v_ventas_detalle
    GROUP BY nombre_sucursal, provincia_sucursal, cod_producto,
             nombre_producto, categoria, marca
)
SELECT nombre_sucursal, provincia, cod_producto, nombre_producto,
       categoria, marca, unidades, venta_neta
FROM ranking WHERE rn = 1;

-- =====================================================================
-- MAPA COROPLETICO PROVINCIAL (poligono en JSON para deck.gl)
-- =====================================================================
DROP VIEW IF EXISTS v_ventas_provincia CASCADE;
CREATE VIEW v_ventas_provincia AS
SELECT m.provincia,
       m.polygon AS geom,
       m.lat,
       m.lon,
       COALESCE(SUM(f.venta_neta), 0) AS venta_neta,
       COALESCE(SUM(f.cantidad), 0) AS unidades,
       COALESCE(SUM(f.margen), 0) AS margen,
       COALESCE(SUM(f.venta_bruta - f.venta_neta), 0) AS descuento_usd,
       COUNT(DISTINCT f.id_venta) AS num_ventas
FROM dim_provincia_mapa m
LEFT JOIN dim_cliente c ON c.provincia = m.provincia
LEFT JOIN fact_ventas f ON f.id_cliente = c.id_cliente
GROUP BY m.provincia, m.polygon, m.lat, m.lon;

DROP VIEW IF EXISTS v_sucursales_mapa CASCADE;
CREATE VIEW v_sucursales_mapa AS
SELECT s.id_sucursal,
       s.nombre_sucursal,
       s.ciudad,
       s.provincia,
       s.region,
       m.lat,
       m.lon,
       m.polygon AS geom,
       COALESCE(SUM(f.venta_neta), 0) AS venta_neta,
       COALESCE(SUM(f.venta_bruta - f.venta_neta), 0) AS descuento_usd,
       COUNT(DISTINCT f.id_venta) AS num_ventas
FROM dim_sucursal s
LEFT JOIN dim_provincia_mapa m ON m.provincia = s.provincia
LEFT JOIN fact_ventas f ON f.id_sucursal = s.id_sucursal
GROUP BY s.id_sucursal, s.nombre_sucursal, s.ciudad, s.provincia, s.region,
         m.lat, m.lon, m.polygon;

-- Mapa unico: provincias (poligonos) y sucursales (puntos).
-- Se replica una fila por categoria para que el mapa reaccione al filtro de
-- categoria; el color se calcula sobre el total provincial.
DROP VIEW IF EXISTS v_mapa_consolidado CASCADE;
CREATE VIEW v_mapa_consolidado AS
WITH prov AS (
    SELECT m.provincia,
           m.polygon AS geom,
           COALESCE(SUM(f.venta_neta), 0) AS venta_neta,
           COUNT(DISTINCT f.id_venta) AS num_ventas
    FROM dim_provincia_mapa m
    LEFT JOIN dim_cliente c ON c.provincia = m.provincia
    LEFT JOIN fact_ventas f ON f.id_cliente = c.id_cliente
    GROUP BY m.provincia, m.polygon
    HAVING COALESCE(SUM(f.venta_neta), 0) > 0
),
prov_color AS (
    SELECT *, NTILE(5) OVER (ORDER BY venta_neta) AS bucket FROM prov
),
prov_region AS (
    SELECT * FROM (VALUES
        ('Esmeraldas', 'Costa'),
        ('Manabí', 'Costa'),
        ('Santo Domingo de los Tsáchilas', 'Costa'),
        ('Los Ríos', 'Costa'),
        ('Guayas', 'Costa'),
        ('Santa Elena', 'Costa'),
        ('El Oro', 'Costa'),
        ('Carchi', 'Sierra'),
        ('Imbabura', 'Sierra'),
        ('Pichincha', 'Sierra'),
        ('Cotopaxi', 'Sierra'),
        ('Tungurahua', 'Sierra'),
        ('Bolívar', 'Sierra'),
        ('Chimborazo', 'Sierra'),
        ('Cañar', 'Sierra'),
        ('Azuay', 'Sierra'),
        ('Loja', 'Sierra'),
        ('Sucumbíos', 'Amazonía'),
        ('Napo', 'Amazonía'),
        ('Orellana', 'Amazonía'),
        ('Pastaza', 'Amazonía'),
        ('Morona Santiago', 'Amazonía'),
        ('Zamora Chinchipe', 'Amazonía')
    ) AS t(provincia, region)
),
prov_cat_sales AS (
    SELECT c.provincia,
           p.categoria,
           SUM(f.venta_neta) AS venta_cat,
           COUNT(DISTINCT f.id_venta) AS num_ventas_cat
    FROM fact_ventas f
    JOIN dim_cliente c ON f.id_cliente = c.id_cliente
    JOIN dim_producto p ON f.id_producto = p.id_producto
    GROUP BY c.provincia, p.categoria
),
prov_features AS (
    SELECT pcs.provincia,
           pcs.categoria,
           NULL::text AS nombre_sucursal,
           COALESCE(pr.region, 'Sin región') AS region,
           ('provincia:' || pcs.provincia) AS geo_key,
           jsonb_build_object(
               'type', 'Feature',
               'provincia', pcs.provincia,
               'geo_key', 'provincia:' || pcs.provincia,
               'geometry', jsonb_build_object(
                   'type', 'Polygon',
                   'coordinates', jsonb_build_array(pv.geom::jsonb)
               ),
               'properties', jsonb_build_object(
                   'tipo', 'provincia',
                   'provincia', pcs.provincia,
                   'categoria', pcs.categoria,
                   'region', COALESCE(pr.region, 'Sin región'),
                   'ventaNeta', round(pcs.venta_cat, 2),
                   'ventaTotal', round(pv.venta_neta, 2),
                   'fillColor',
                   (ARRAY['#c9dcff', '#9bbcf7', '#5f8fe8', '#2a5fc4', '#0033A0'])[pv.bucket],
                   'strokeColor', '#ffffff',
                   'stroke-width', 1.5
               ),
               'extraProps', jsonb_build_object(
                   'Provincia', pcs.provincia,
                   'Categoría', pcs.categoria,
                   'Venta neta', round(pcs.venta_cat, 2),
                   'Venta total', round(pv.venta_neta, 2),
                   'Transacciones', pcs.num_ventas_cat
               )
           )::text AS geojson
    FROM prov_color pv
    JOIN prov_cat_sales pcs ON pcs.provincia = pv.provincia
    LEFT JOIN prov_region pr ON pr.provincia = pcs.provincia
),
suc AS (
    SELECT s.nombre_sucursal,
           s.ciudad,
           s.provincia,
           s.region,
           m.lat,
           m.lon,
           COALESCE(SUM(f.venta_neta), 0) AS venta_neta,
           COUNT(DISTINCT f.id_venta) AS num_ventas
    FROM dim_sucursal s
    JOIN dim_provincia_mapa m ON m.provincia = s.provincia
    LEFT JOIN fact_ventas f ON f.id_sucursal = s.id_sucursal
    GROUP BY s.nombre_sucursal, s.ciudad, s.provincia, s.region, m.lat, m.lon
),
suc_pos AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY provincia ORDER BY nombre_sucursal
           ) AS rn_prov,
           COUNT(*) OVER (PARTITION BY provincia) AS cnt_prov
    FROM suc
),
suc_cat_sales AS (
    SELECT s.nombre_sucursal,
           p.categoria,
           SUM(f.venta_neta) AS venta_cat,
           COUNT(DISTINCT f.id_venta) AS num_ventas_cat
    FROM fact_ventas f
    JOIN dim_sucursal s ON f.id_sucursal = s.id_sucursal
    JOIN dim_producto p ON f.id_producto = p.id_producto
    GROUP BY s.nombre_sucursal, p.categoria
),
suc_features AS (
    SELECT sp.provincia,
           scs.categoria,
           sp.nombre_sucursal,
           COALESCE(sp.region, 'Sin región') AS region,
           ('sucursal:' || sp.nombre_sucursal) AS geo_key,
           jsonb_build_object(
               'type', 'Feature',
               'provincia', sp.provincia,
               'geo_key', 'sucursal:' || sp.nombre_sucursal,
               'geometry', jsonb_build_object(
                   'type', 'Point',
                   'coordinates', jsonb_build_array(
                       sp.lon + CASE
                           WHEN sp.cnt_prov = 1 THEN 0
                           ELSE (sp.rn_prov - (sp.cnt_prov + 1) / 2.0) * 0.10
                       END,
                       sp.lat + CASE
                           WHEN sp.cnt_prov = 1 THEN 0
                           WHEN MOD(sp.rn_prov, 2) = 0 THEN 0.06
                           ELSE -0.06
                       END
                   )
               ),
               'properties', jsonb_build_object(
                   'tipo', 'sucursal',
                   'sucursal', sp.nombre_sucursal,
                   'ciudad', sp.ciudad,
                   'provincia', sp.provincia,
                   'region', COALESCE(sp.region, 'Sin región'),
                   'categoria', scs.categoria,
                   'ventaNeta', round(scs.venta_cat, 2),
                   'ventaTotal', round(sp.venta_neta, 2),
                   'fillColor', '#CE1126',
                   'strokeColor', '#ffffff',
                   'stroke-width', 2
               ),
               'extraProps', jsonb_build_object(
                   'Sucursal', sp.nombre_sucursal,
                   'Ciudad', sp.ciudad,
                   'Provincia', sp.provincia,
                   'Categoría', scs.categoria,
                   'Venta neta', round(scs.venta_cat, 2),
                   'Venta total', round(sp.venta_neta, 2),
                   'Transacciones', scs.num_ventas_cat
               )
           )::text AS geojson
    FROM suc_pos sp
    JOIN suc_cat_sales scs ON scs.nombre_sucursal = sp.nombre_sucursal
)
SELECT geojson, provincia, categoria, nombre_sucursal, region, geo_key FROM prov_features
UNION ALL
SELECT geojson, provincia, categoria, nombre_sucursal, region, geo_key FROM suc_features;

-- =====================================================================
-- RECHAZOS: perdidas estimadas por sucursal, fecha y motivo
-- =====================================================================
DROP VIEW IF EXISTS v_rechazos CASCADE;
CREATE VIEW v_rechazos AS
SELECT r.id_rechazo,
       r.id_venta,
       r.fecha_venta,
       r.cod_cliente,
       r.cod_producto,
       r.cod_sucursal,
       COALESCE(s.nombre_sucursal, r.cod_sucursal, 'Sucursal desconocida') AS nombre_sucursal,
       COALESCE(s.provincia, 'Provincia desconocida') AS provincia,
       COALESCE(s.region, 'Sin región') AS region,
       COALESCE(p.categoria, 'Sin categoría') AS categoria,
       COALESCE(p.marca, 'Sin marca') AS marca,
       r.cantidad,
       r.precio_unitario,
       r.descuento_pct,
       r.canal_venta,
       r.metodo_pago,
       COALESCE(r.motivo, 'Sin motivo') AS motivo,
       r.venta_perdida
FROM fact_rechazos r
LEFT JOIN dim_sucursal s ON s.cod_sucursal = r.cod_sucursal
LEFT JOIN dim_producto p ON p.cod_producto = r.cod_producto;

DROP VIEW IF EXISTS v_rechazos_sucursal CASCADE;
CREATE VIEW v_rechazos_sucursal AS
SELECT nombre_sucursal,
       provincia,
       COUNT(*) AS num_rechazos,
       SUM(venta_perdida) AS venta_perdida
FROM v_rechazos
GROUP BY nombre_sucursal, provincia;

DROP VIEW IF EXISTS v_rechazos_fecha CASCADE;
CREATE VIEW v_rechazos_fecha AS
SELECT fecha_venta,
       date_trunc('month', fecha_venta)::date AS mes,
       COUNT(*) AS num_rechazos,
       SUM(venta_perdida) AS venta_perdida
FROM v_rechazos
WHERE fecha_venta IS NOT NULL
GROUP BY fecha_venta, date_trunc('month', fecha_venta)::date;

DROP VIEW IF EXISTS v_rechazos_motivo CASCADE;
CREATE VIEW v_rechazos_motivo AS
SELECT motivo,
       COUNT(*) AS num_rechazos,
       SUM(venta_perdida) AS venta_perdida
FROM v_rechazos
GROUP BY motivo;
