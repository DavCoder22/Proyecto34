# Comparacion de calidad: antes y despues del ETL

El grano de `ventas` es una linea de venta; `id_venta` puede repetirse cuando una venta contiene varios productos.

## Resultado por entidad

| Entidad | Filas antes | Filas despues | Diferencia | Nulos antes | Nulos despues | Duplicados exactos antes | Duplicados exactos despues | Claves unicas antes | Claves unicas despues |
|---|---|---|---|---|---|---|---|---|---|
| clientes | 1006 | 1000 | 6 | 10 | 8 | 6 | 0 | 1000 | 1000 |
| sucursales | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 12 | 12 |
| productos | 123 | 120 | 3 | 5 | 5 | 3 | 0 | 120 | 120 |
| ventas | 6870 | 6800 | 70 | 27 | 0 | 20 | 0 | 3600 | 3587 |

## Controles de validez e integridad

| Regla | Antes | Despues | Tratamiento |
|---|---:|---:|---|
| Fechas de venta invalidas o nulas | 21 | 0 | Se excluyen antes de construir la dimension tiempo |
| Filas con FK invalida | 30 | 0 | Se registran en `log_rechazos.csv` y no pasan a hechos |
| Filas con rangos numericos invalidos | 0 | 0 | Se validan cantidad, precio y descuento |
| Filas en FactVentas | - | 6800 | Solo registros validos e integrables |

## Impacto para el analisis

Las filas descartadas no se fuerzan al dashboard: conservarlas produciria ventas sin cliente, producto o sucursal, distorsionando ingresos, unidades, margen y transacciones. El total publicado debe interpretarse como ventas validas integradas.