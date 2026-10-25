"""Reglas de negocio: venta neta, ticket promedio, margen."""
import pandas as pd

def add_business_rules(ventas, productos):
    v = ventas.copy()
    v["venta_bruta"] = v["cantidad"] * v["precio_unitario"]
    v["venta_neta"] = v["venta_bruta"] * (1 - v["descuento_pct"].fillna(0))
    # costo unitario desde productos
    costos = productos[["cod_producto", "costo_unitario"]].drop_duplicates("cod_producto")
    v = v.merge(costos, on="cod_producto", how="left")
    v["costo_total"] = v["cantidad"] * v["costo_unitario"].fillna(0)
    v["margen"] = v["venta_neta"] - v["costo_total"]
    return v