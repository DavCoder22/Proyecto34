"""Validacion: completitud, unicidad, integridad (FK). Genera log de rechazos."""
import pandas as pd
from pathlib import Path
from config import FK_CHECKS, DATA_STAGING, LOG_PATH

def check_completeness(df, required_cols):
    issues = []
    for c in required_cols:
        if c in df.columns:
            n = df[c].isna().sum()
            if n > 0:
                issues.append({"columna": c, "nulos": int(n), "pct": round(n/len(df)*100,2)})
    return issues

def check_fk(child_df, fk_col, parent_df, parent_pk):
    mask = ~child_df[fk_col].isin(parent_df[parent_pk])
    rejected = child_df[mask].copy()
    rejected["motivo"] = f"FK invalida: {fk_col} no existe en {parent_pk}"
    return rejected, int(mask.sum())

def validate_all(df_dict):
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    rechazos = []
    fk_report = []
    for (child, fk_col, parent) in FK_CHECKS:
        if child in df_dict and parent in df_dict:
            pk = fk_col
            rej, n = check_fk(df_dict[child], fk_col, df_dict[parent], pk)
            if n > 0:
                rechazos.append(rej)
                fk_report.append({"hija": child, "fk": fk_col, "padre": parent, "rechazados": n})
                print(f"[VALIDATE] {child}.{fk_col} -> {parent}: {n} rechazados")
    if rechazos:
        rej_df = pd.concat(rechazos, ignore_index=True)
        rej_df.to_csv(LOG_PATH / "log_rechazos.csv", index=False, encoding="utf-8-sig")
    # completitud
    for name, df in df_dict.items():
        issues = check_completeness(df, list(df.columns))
        if issues:
            print(f"[VALIDATE] {name} nulos: {issues}")
    return fk_report

def remove_rejected(df_dict):
    """Elimina de ventas las filas con FK invalida."""
    if "ventas" not in df_dict:
        return df_dict
    v = df_dict["ventas"].copy()
    for (child, fk_col, parent) in FK_CHECKS:
        if child == "ventas" and parent in df_dict:
            v = v[v[fk_col].isin(df_dict[parent][fk_col])]
    df_dict["ventas"] = v.reset_index(drop=True)
    return df_dict