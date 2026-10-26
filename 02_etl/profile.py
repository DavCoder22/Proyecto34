"""Reconocimiento/profiling de datos: genera log de calidad inicial (antes de limpiar)."""
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import SOURCES, DATA_RAW, LOG_PATH, PK

def profile_df(name, df):
    lines = [
        f"## {name} — {len(df)} filas x {len(df.columns)} cols",
        f"- PK: {PK.get(name)} (unicos: {df[PK[name]].nunique() if PK.get(name) in df.columns else 'n/a'})",
        "- Nulos por columna:",
    ]
    for c in df.columns:
        n = df[c].isna().sum() if df[c].dtype != object else df[c].replace({"": pd.NA, "nan": pd.NA}).isna().sum()
        lines.append(f"  - {c}: {int(n)} ({round(n/len(df)*100,2)}%)")
    lines.append(f"- Filas duplicadas (exactas): {int(df.duplicated().sum())}")
    # valores unicos para categoricas pequeñas
    for c in df.columns:
        if df[c].nunique() <= 15 and df[c].dtype == object:
            vals = df[c].value_counts(dropna=False).to_dict()
            lines.append(f"- {c} valores: {vals}")
    lines.append("")
    return "\n".join(lines)

def main():
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    # asegurar raw
    from pathlib import Path as P
    for spec in SOURCES.values():
        src = P(__file__).resolve().parents[2] / "datos" / spec["file"]
        dst = DATA_RAW / spec["file"]
        if src.exists() and not dst.exists():
            import shutil; shutil.copy2(src, dst)

    report = ["# Reporte de Reconocimiento de Datos (Profiling inicial)\n"]
    for name, spec in SOURCES.items():
        if spec["file"].endswith((".xlsx",".xls")):
            df = pd.read_excel(DATA_RAW / spec["file"], sheet_name=spec.get("sheet",0), dtype=str)
        else:
            df = pd.read_csv(DATA_RAW / spec["file"], sep=spec.get("sep",","), encoding=spec.get("encoding","utf-8"), dtype=str)
        report.append(profile_df(name, df))

    out = LOG_PATH / "profile_report.md"
    out.write_text("\n".join(report), encoding="utf-8")
    print(f"Reporte generado: {out}")

if __name__ == "__main__":
    main()