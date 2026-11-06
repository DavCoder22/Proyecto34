# Esquema estrella — Data Warehouse

```mermaid
erDiagram
    DIM_TIEMPO ||--o{ FACT_VENTAS : id_tiempo
    DIM_CLIENTE ||--o{ FACT_VENTAS : id_cliente
    DIM_PRODUCTO ||--o{ FACT_VENTAS : id_producto
    DIM_SUCURSAL ||--o{ FACT_VENTAS : id_sucursal

    DIM_TIEMPO {
        int id_tiempo PK
        date fecha
        int anio
        int mes
        string mes_nombre
        string trimestre
        int semana
        string dia_semana
    }
    DIM_CLIENTE {
        int id_cliente PK
        string cod_cliente UK
        string nombre_cliente
        string segmento
        string ciudad
        string provincia
        date fecha_registro
        string estado_cliente
    }
    DIM_PRODUCTO {
        int id_producto PK
        string cod_producto UK
        string nombre_producto
        string categoria
        string subcategoria
        string marca
        numeric costo_unitario
        string estado_producto
    }
    DIM_SUCURSAL {
        int id_sucursal PK
        string cod_sucursal UK
        string nombre_sucursal
        string ciudad
        string provincia
        string region
        date fecha_apertura
        string estado_sucursal
    }
    FACT_VENTAS {
        int id_venta_pk PK
        string id_venta
        int id_tiempo FK
        int id_cliente FK
        int id_producto FK
        int id_sucursal FK
        int cantidad
        numeric precio_unitario
        numeric descuento_pct
        numeric venta_bruta
        numeric venta_neta
        numeric costo_total
        numeric margen
        string canal_venta
        string metodo_pago
    }
```

Relaciones: `fact_ventas` se une a cada dimensión por su surrogate key (`id_tiempo`, `id_cliente`, `id_producto`, `id_sucursal`). `dim_provincia_mapa` es auxiliar para el dashboard.