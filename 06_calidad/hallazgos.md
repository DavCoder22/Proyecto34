# Hallazgos para la toma de decisiones

Los siguientes resultados se obtuvieron de `03_dw/dw.db` después de ejecutar el ETL.

1. **La calidad sí cambia el universo analítico.** La fuente contiene 6.870 líneas de venta y el hecho integrado 6.800. Se eliminaron 20 duplicados exactos, 30 líneas con claves foráneas inválidas y 20 líneas sin fecha válida. Esto evita que el dashboard publique ventas sin dimensión relacionada.

2. **Accesorios y Hogar concentran la mayor participación.** Accesorios aporta 20,80% de los ingresos y Hogar 19,59%. Estas categorías justifican revisar inventario y campañas antes de priorizar categorías con menor contribución.

3. **El segmento Masivo concentra el volumen comercial.** Representa 3.789.241,73 de venta neta y 1.846 transacciones. El segmento Frecuente aporta 2.120.524,67, por lo que puede ser objetivo de campañas de fidelización para aumentar recurrencia.

4. **El margen bruto integrado es 1.966.780,12.** Frente a 7.452.222,71 de ingresos netos, equivale aproximadamente a 26,39%. Este indicador debe analizarse junto con categoría y sucursal, no solamente con ventas.

## Advertencia para proyecciones

Las cifras representan el universo válido, no una estimación de ventas faltantes. Antes de proyectar, se debe controlar mensualmente la tasa de rechazo y la cobertura de fechas. Si los rechazos aumentan o se concentran en una sucursal/categoría, la tendencia observada puede quedar sesgada.
