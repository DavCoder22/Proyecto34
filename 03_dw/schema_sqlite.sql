-- Star Schema adaptado a PostgreSQL
-- Data Warehouse para PoC Integración y Calidad de Datos

-- DIMENSIONES
CREATE TABLE IF NOT EXISTS dim_tiempo (
    id_tiempo INTEGER PRIMARY KEY,
    fecha DATE NOT NULL,
    anio INTEGER,
    mes INTEGER,
    mes_nombre VARCHAR(20),
    trimestre VARCHAR(2),
    semana INTEGER,
    dia_semana VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS dim_cliente (
    id_cliente SERIAL PRIMARY KEY,
    cod_cliente VARCHAR(10) UNIQUE NOT NULL,
    nombre_cliente VARCHAR(150),
    segmento VARCHAR(30),
    ciudad VARCHAR(80),
    provincia VARCHAR(80),
    fecha_registro DATE,
    estado_cliente VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS dim_producto (
    id_producto SERIAL PRIMARY KEY,
    cod_producto VARCHAR(10) UNIQUE NOT NULL,
    nombre_producto VARCHAR(150),
    categoria VARCHAR(60),
    subcategoria VARCHAR(60),
    marca VARCHAR(60),
    costo_unitario NUMERIC(12,2),
    estado_producto VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS dim_sucursal (
    id_sucursal SERIAL PRIMARY KEY,
    cod_sucursal VARCHAR(10) UNIQUE NOT NULL,
    nombre_sucursal VARCHAR(80),
    ciudad VARCHAR(80),
    provincia VARCHAR(80),
    region VARCHAR(20),
    fecha_apertura DATE,
    estado_sucursal VARCHAR(15)
);

-- HECHO
CREATE TABLE IF NOT EXISTS fact_ventas (
    id_venta_pk SERIAL PRIMARY KEY,
    id_venta VARCHAR(15) NOT NULL,
    id_tiempo INTEGER REFERENCES dim_tiempo(id_tiempo),
    id_cliente INTEGER REFERENCES dim_cliente(id_cliente),
    id_producto INTEGER REFERENCES dim_producto(id_producto),
    id_sucursal INTEGER REFERENCES dim_sucursal(id_sucursal),
    cantidad INTEGER,
    precio_unitario NUMERIC(12,2),
    descuento_pct NUMERIC(5,2),
    venta_bruta NUMERIC(14,2),
    venta_neta NUMERIC(14,2),
    costo_total NUMERIC(14,2),
    margen NUMERIC(14,2),
    canal_venta VARCHAR(30),
    metodo_pago VARCHAR(30)
);

-- ÍNDICES PARA RENDIMIENTO
CREATE INDEX IF NOT EXISTS idx_fact_ventas_tiempo ON fact_ventas(id_tiempo);
CREATE INDEX IF NOT EXISTS idx_fact_ventas_cliente ON fact_ventas(id_cliente);
CREATE INDEX IF NOT EXISTS idx_fact_ventas_producto ON fact_ventas(id_producto);
CREATE INDEX IF NOT EXISTS idx_fact_ventas_sucursal ON fact_ventas(id_sucursal);
CREATE INDEX IF NOT EXISTS idx_fact_ventas_idventa ON fact_ventas(id_venta);
