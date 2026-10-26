"""Carga al Data Warehouse (SQLite) con modelo estrella."""
import sqlite3
import pandas as pd
from pathlib import Path
from config import DW_PATH, ROOT

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
    return d[["id_tiempo","fecha","anio","mes","mes_nombre","trimestre","semana","dia_semana"]]

def load_all(df_dict, ventas_fact):
    DW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DW_PATH.exists():
        DW_PATH.unlink()
    conn = sqlite3.connect(DW_PATH)
    # Dims
    clientes = df_dict["clientes"].copy()
    clientes["id_cliente"] = range(1, len(clientes)+1)
    clientes.to_sql("DimCliente", conn, index=False, if_exists="replace")

    suc = df_dict["sucursales"].copy()
    suc["id_sucursal"] = range(1, len(suc)+1)
    suc.to_sql("DimSucursal", conn, index=False, if_exists="replace")

    prod = df_dict["productos"].copy()
    prod["id_producto"] = range(1, len(prod)+1)
    prod.to_sql("DimProducto", conn, index=False, if_exists="replace")

    dimt = build_dim_tiempo(ventas_fact)
    dimt.to_sql("DimTiempo", conn, index=False, if_exists="replace")

    # Map FKs to surrogate ids
    f = ventas_fact.copy()
    f["id_tiempo"] = pd.to_datetime(f["fecha_venta"]).dt.strftime("%Y%m%d").astype(int)
    cli_map = dict(zip(df_dict["clientes"]["cod_cliente"], clientes["id_cliente"]))
    suc_map = dict(zip(df_dict["sucursales"]["cod_sucursal"], suc["id_sucursal"]))
    prod_map = dict(zip(df_dict["productos"]["cod_producto"], prod["id_producto"]))
    f["id_cliente"] = f["cod_cliente"].map(cli_map)
    f["id_sucursal"] = f["cod_sucursal"].map(suc_map)
    f["id_producto"] = f["cod_producto"].map(prod_map)
    f["id_venta_pk"] = range(1, len(f)+1)
    fact_cols = ["id_venta_pk","id_venta","id_tiempo","id_cliente","id_producto","id_sucursal",
                 "cantidad","precio_unitario","descuento_pct","venta_bruta","venta_neta","costo_total","margen",
                 "canal_venta","metodo_pago"]
    f[fact_cols].to_sql("FactVentas", conn, index=False, if_exists="replace")

    # Agregados
    agg_mes = f.merge(dimt[["id_tiempo", "anio", "mes", "mes_nombre", "trimestre"]], on="id_tiempo") \
               .groupby(["anio", "mes", "mes_nombre", "trimestre"], as_index=False) \
               .agg(venta_neta=("venta_neta", "sum"), cantidad=("cantidad", "sum"), num_ventas=("id_venta", "nunique"))
    agg_mes.to_sql("Agg_VentasMes", conn, index=False, if_exists="replace")
    agg_cat = f.merge(prod[["cod_producto","categoria"]], left_on="cod_producto", right_on="cod_producto", how="left") \
               .groupby("categoria", as_index=False).agg(venta_neta=("venta_neta","sum"))
    agg_cat.to_sql("Agg_VentasCategoria", conn, index=False, if_exists="replace")
    agg_suc = f.groupby("id_sucursal", as_index=False).agg(venta_neta=("venta_neta","sum"))
    agg_suc.to_sql("Agg_VentasSucursal", conn, index=False, if_exists="replace")

    # Las vistas son parte del producto analitico y se recrean en cada carga.
    views_sql = (ROOT / "04_dashboard" / "kpi_views.sql").read_text(encoding="utf-8")
    conn.executescript(views_sql)
    conn.commit()
    conn.close()
    print(f"[LOAD] DW creado en {DW_PATH}")
