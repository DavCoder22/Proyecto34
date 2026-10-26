# Reglas de transformación y justificación

| Problema observado | Fuente | Regla aplicada | Criterio y resultado esperado |
|---|---|---|---|
| Duplicados exactos | Las cuatro fuentes | Eliminar duplicados exactos; en catálogos conservar una fila por clave natural | Evitar doble conteo. En ventas se conserva el grano línea y solo se elimina una fila idéntica |
| Fechas heterogéneas, vacías o inválidas | Clientes, sucursales y ventas | Parsear con `pandas.to_datetime`; excluir ventas sin fecha | La dimensión tiempo solo contiene fechas válidas y el dashboard puede agrupar por año/mes |
| Descuentos en decimal o porcentaje | Ventas | Valores mayores que 1 se dividen para 100 | Todos los descuentos quedan entre 0 y 1 para calcular venta neta |
| Categorías con distinta escritura | Productos | Homologar mayúsculas, minúsculas y acentos a un catálogo canónico | Evitar que una misma categoría aparezca como varias series |
| Segmento, canal o método vacío | Clientes y ventas | Sustituir vacío por una categoría explícita de no especificado | No perder filas y hacer visible la incertidumbre en el dashboard |
| Claves foráneas inexistentes | Ventas | Registrar el rechazo y excluir la línea del hecho integrado | Impedir ventas huérfanas que distorsionen filtros y agregados |
| Costo de producto desconocido | Productos | No imputar cero; conservar costo y margen como desconocidos | No sobreestimar artificialmente el margen bruto |
| Tipos numéricos almacenados como texto | Ventas y productos | Convertir cantidad, precio, descuento y costo a numérico | Permitir cálculos reproducibles de ingresos y margen |

## Efecto en la proyección

El dashboard usa únicamente registros integrables. Por tanto, la proyección comercial no debe sumar las filas rechazadas como si fueran ventas válidas. La exclusión reduce el universo analítico, pero evita proyectar sobre clientes, productos o sucursales inexistentes. Las filas excluidas deben monitorearse como una tasa de rechazo; si aumenta, la proyección pierde cobertura y la gerencia debe corregir el origen.
