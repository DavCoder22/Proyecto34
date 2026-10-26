"""Carga al Data Warehouse: SQLite siempre y PostgreSQL si DATABASE_URL está definida."""
import os
import sqlite3

import pandas as pd

from config import DW_PATH, ROOT

POSTGRES_TABLES = {
    "DimTiempo": "dim_tiempo",
    "DimCliente": "dim_cliente",
    "DimProducto": "dim_producto",
    "DimSucursal": "dim_sucursal",
    "FactVentas": "fact_ventas",
}

FACT_COLS = [
    "id_venta_pk", "id_venta", "id_tiempo", "id_cliente", "id_producto", "id_sucursal",
    "cantidad", "precio_unitario", "descuento_pct", "venta_bruta", "venta_neta",
    "costo_total", "margen", "canal_venta", "metodo_pago",
]


def build_dim_tiempo(ventas):
    fechas = pd.to_datetime(ventas["fecha_venta"], errors="coerce").dropna().dt.date.unique()
    d = pd.DataFrame({"fecha": pd.to_datetime(fechas)})
    d["id_tiempo"] = d["fecha"].dt.strftime("%Y%m%d").astype(int)
    d["anio"] = d["fecha"].dt.year
    d["mes"] = d["fecha"].dt.month
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    d["mes_nombre"] = d["fecha"].dt.month.map(lambda m: meses[m - 1])
    d["trimestre"] = d["fecha"].dt.quarter.map(lambda q: f"Q{q}")
    d["semana"] = d["fecha"].dt.isocalendar().week.astype(int)
    d["dia_semana"] = d["fecha"].dt.day_name()
    return d[["id_tiempo", "fecha", "anio", "mes", "mes_nombre", "trimestre", "semana", "dia_semana"]]


def _split_sql(sql):
    return [stmt.strip() for stmt in sql.split(";") if stmt.strip()]


def _build_frames(df_dict, ventas_fact):
    clientes = df_dict["clientes"].copy()
    clientes["id_cliente"] = range(1, len(clientes) + 1)

    suc = df_dict["sucursales"].copy()
    suc["id_sucursal"] = range(1, len(suc) + 1)

    prod = df_dict["productos"].copy()
    prod["id_producto"] = range(1, len(prod) + 1)

    dimt = build_dim_tiempo(ventas_fact)

    f = ventas_fact.copy()
    f["id_tiempo"] = pd.to_datetime(f["fecha_venta"]).dt.strftime("%Y%m%d").astype(int)
    cli_map = dict(zip(df_dict["clientes"]["cod_cliente"], clientes["id_cliente"]))
    suc_map = dict(zip(df_dict["sucursales"]["cod_sucursal"], suc["id_sucursal"]))
    prod_map = dict(zip(df_dict["productos"]["cod_producto"], prod["id_producto"]))
    for column, source, mapping in (
        ("id_cliente", "cod_cliente", cli_map),
        ("id_sucursal", "cod_sucursal", suc_map),
        ("id_producto", "cod_producto", prod_map),
    ):
        f[column] = f[source].map(mapping)
        if f[column].isna().any():
            raise ValueError(f"Hay {source} sin correspondencia en la dimensión")
        f[column] = f[column].astype(int)
    f["id_venta_pk"] = range(1, len(f) + 1)

    frames = {
        "DimTiempo": dimt,
        "DimCliente": clientes,
        "DimProducto": prod,
        "DimSucursal": suc,
        "FactVentas": f[FACT_COLS].copy(),
    }
    return frames, f, dimt, prod


def _load_sqlite(frames, fact_full, dimt, prod):
    DW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DW_PATH.exists():
        DW_PATH.unlink()
    conn = sqlite3.connect(DW_PATH)

    for name in ("DimTiempo", "DimCliente", "DimProducto", "DimSucursal", "FactVentas"):
        frames[name].to_sql(name, conn, index=False, if_exists="replace")

    agg_mes = fact_full.merge(dimt[["id_tiempo", "anio", "mes", "mes_nombre", "trimestre"]], on="id_tiempo") \
        .groupby(["anio", "mes", "mes_nombre", "trimestre"], as_index=False) \
        .agg(venta_neta=("venta_neta", "sum"), cantidad=("cantidad", "sum"), num_ventas=("id_venta", "nunique"))
    agg_mes.to_sql("Agg_VentasMes", conn, index=False, if_exists="replace")

    agg_cat = fact_full.merge(prod[["cod_producto", "categoria"]], on="cod_producto", how="left") \
        .groupby("categoria", as_index=False).agg(venta_neta=("venta_neta", "sum"))
    agg_cat.to_sql("Agg_VentasCategoria", conn, index=False, if_exists="replace")

    agg_suc = fact_full.groupby("id_sucursal", as_index=False).agg(venta_neta=("venta_neta", "sum"))
    agg_suc.to_sql("Agg_VentasSucursal", conn, index=False, if_exists="replace")

    views_sql = (ROOT / "04_dashboard" / "kpi_views.sql").read_text(encoding="utf-8")
    conn.executescript(views_sql)
    conn.commit()
    conn.close()
    print(f"[LOAD] DW SQLite creado en {DW_PATH}")


def _postgres_required():
    return os.environ.get("REQUIRE_POSTGRES_LOAD", "").strip().lower() in {"1", "true", "yes", "on"}


def _load_postgres(frames):
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        if _postgres_required():
            raise RuntimeError("REQUIRE_POSTGRES_LOAD=1 pero DATABASE_URL no está definida")
        return
    if os.environ.get("LOAD_POSTGRES", "1").strip().lower() in {"0", "false", "no", "off"}:
        print("[LOAD] Carga a PostgreSQL omitida por LOAD_POSTGRES")
        return
    if not database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        message = "DATABASE_URL no es PostgreSQL; se omite la carga a PostgreSQL"
        if _postgres_required():
            raise RuntimeError(message)
        print(f"[LOAD][WARN] {message}")
        return

    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        if _postgres_required():
            raise
        print(f"[LOAD][WARN] SQLAlchemy no disponible: {exc}")
        return

    engine = None
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        schema_sql = (ROOT / "03_dw" / "schema.sql").read_text(encoding="utf-8")

        with engine.begin() as conn:
            for statement in _split_sql(schema_sql):
                conn.execute(text(statement))
            conn.execute(text(
                "TRUNCATE TABLE fact_ventas, dim_tiempo, dim_cliente, dim_producto, dim_sucursal "
                "RESTART IDENTITY CASCADE"
            ))

        for name in ("DimTiempo", "DimCliente", "DimProducto", "DimSucursal", "FactVentas"):
            frames[name].to_sql(
                POSTGRES_TABLES[name],
                engine,
                index=False,
                if_exists="append",
                method="multi",
                chunksize=500,
            )

        views_path = ROOT / "04_dashboard" / "kpi_views_postgres.sql"
        if views_path.exists():
            with engine.begin() as conn:
                for statement in _split_sql(views_path.read_text(encoding="utf-8")):
                    conn.execute(text(statement))

        with engine.begin() as conn:
            for table, column in (
                ("dim_cliente", "id_cliente"),
                ("dim_producto", "id_producto"),
                ("dim_sucursal", "id_sucursal"),
                ("fact_ventas", "id_venta_pk"),
            ):
                conn.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
                    f"COALESCE((SELECT MAX({column}) FROM {table}), 1))"
                ))

        safe_url = database_url.split("@")[-1]
        print(f"[LOAD] DW PostgreSQL actualizado en {safe_url}")
    except Exception as exc:
        if _postgres_required():
            raise
        print(f"[LOAD][WARN] No se pudo cargar a PostgreSQL: {exc}")
    finally:
        if engine is not None:
            engine.dispose()


def load_all(df_dict, ventas_fact):
    frames, fact_full, dimt, prod = _build_frames(df_dict, ventas_fact)
    _load_sqlite(frames, fact_full, dimt, prod)
    _load_postgres(frames)
