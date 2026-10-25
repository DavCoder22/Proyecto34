"""Homologacion de catalogos: variantes -> nombre canonico."""
import pandas as pd
from config import HOMOLOGACION

def homologate_col(df, col, mapping):
    if col not in df.columns:
        return df
    # normalizar clave: strip + case-insensitive match
    def _map(v):
        if pd.isna(v):
            v = ""
        key = str(v).strip()
        # buscar coincidencia exacta o case-insensitive
        if key in mapping:
            return mapping[key]
        low = key.lower()
        for k, val in mapping.items():
            if str(k).lower() == low:
                return val
        return key if key != "" else mapping.get("", key)
    df[col] = df[col].apply(_map)
    return df

def run_all(df_dict):
    out = {}
    for name, df in df_dict.items():
        df = df.copy()
        for col, mapping in HOMOLOGACION.items():
            if col in df.columns:
                df = homologate_col(df, col, mapping)
        out[name] = df
    return out