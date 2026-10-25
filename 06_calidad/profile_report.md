# Reporte de Reconocimiento de Datos (Profiling inicial)

## clientes — 1006 filas x 7 cols
- PK: cod_cliente (unicos: 1000)
- Nulos por columna:
  - cod_cliente: 0 (0.0%)
  - nombre_cliente: 0 (0.0%)
  - segmento: 10 (0.99%)
  - ciudad: 0 (0.0%)
  - provincia: 0 (0.0%)
  - fecha_registro: 0 (0.0%)
  - estado_cliente: 0 (0.0%)
- Filas duplicadas (exactas): 6

## sucursales — 12 filas x 7 cols
- PK: cod_sucursal (unicos: 12)
- Nulos por columna:
  - cod_sucursal: 0 (0.0%)
  - nombre_sucursal: 0 (0.0%)
  - ciudad: 0 (0.0%)
  - provincia: 0 (0.0%)
  - region: 0 (0.0%)
  - fecha_apertura: 0 (0.0%)
  - estado_sucursal: 0 (0.0%)
- Filas duplicadas (exactas): 0

## productos — 123 filas x 7 cols
- PK: cod_producto (unicos: 120)
- Nulos por columna:
  - cod_producto: 0 (0.0%)
  - nombre_producto: 0 (0.0%)
  - categoria: 0 (0.0%)
  - subcategoria: 0 (0.0%)
  - marca: 5 (4.07%)
  - costo_unitario: 0 (0.0%)
  - estado_producto: 0 (0.0%)
- Filas duplicadas (exactas): 3

## ventas — 6870 filas x 10 cols
- PK: id_venta (unicos: 3600)
- Nulos por columna:
  - id_venta: 0 (0.0%)
  - fecha_venta: 0 (0.0%)
  - cod_cliente: 0 (0.0%)
  - cod_producto: 0 (0.0%)
  - cod_sucursal: 0 (0.0%)
  - cantidad: 0 (0.0%)
  - precio_unitario: 0 (0.0%)
  - descuento_pct: 0 (0.0%)
  - canal_venta: 15 (0.22%)
  - metodo_pago: 12 (0.17%)
- Filas duplicadas (exactas): 20
