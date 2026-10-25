"""Capa de limpieza generica: nulos, duplicados, tipos, encoding, fechas."""
import pandas as pd
import numpy as np
from config import DATE_COLS, DESCUENTO_COLS

def to_utf8_str(df):
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"nan": np.nan, "None": np.nan, "": np.nan})
    return df

def drop_dupes(df, pk=None, keep="first"):
    before = len(df)
    if pk and pk in df.columns:
        df = df.drop_duplicates(subset=[pk], keep=keep)
    else:
        df = df.drop_duplicates(keep=keep)
    return df, before - len(df)

def parse_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=False)
    return df

def normalize_discount(df):
    for c in DESCUENTO_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            # si valores >1 se asumen porcentaje (5.0 -> 0.05)
            mask = df[c] > 1
            df.loc[mask, c] = df.loc[mask, c] / 100.0
    return df

def coerce_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def fill_nulls(df, defaults):
    for c, v in defaults.items():
        if c in df.columns:
            df[c] = df[c].fillna(v)
    return df

def clean_entity(name, df):
    df = to_utf8_str(df)
    from config import PK
    if name == "ventas":
        # ventas tiene varias lineas por id_venta -> dedup por fila completa
        df, n_dup = drop_dupes(df, pk=None)
    else:
        pk = PK.get(name)
        df, n_dup = drop_dupes(df, pk=pk)
    if name in DATE_COLS:
        df = parse_dates(df, DATE_COLS[name])
    if name == "ventas":
        df = normalize_discount(df)
        df = coerce_numeric(df, ["cantidad", "precio_unitario", "descuento_pct"])
    if name == "productos":
        df = coerce_numeric(df, ["costo_unitario"])
    return df, n_dup