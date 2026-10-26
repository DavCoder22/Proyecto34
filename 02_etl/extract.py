"""Capa de extraccion: lee fuentes heterogeneas y las deja en staging/raw."""
import pandas as pd
from pathlib import Path
from config import SOURCES, DATA_RAW, DATA_STAGING

def detect_encoding(path):
    try:
        import chardet
        with open(path, "rb") as f:
            raw = f.read(10000)
        return chardet.detect(raw).get("encoding") or "utf-8"
    except ImportError:
        return "utf-8"

def extract_one(spec):
    path = DATA_RAW / spec["file"]
    if not path.exists():
        # fallback: buscar en carpeta datos original
        alt = Path(__file__).resolve().parents[2] / "datos" / spec["file"]
        if alt.exists():
            path = alt
        else:
            raise FileNotFoundError(f"No se encontro {spec['file']}")
    if spec["file"].endswith((".xlsx", ".xls")):
        df = pd.read_excel(path, sheet_name=spec.get("sheet", 0))
    else:
        enc = spec.get("encoding", detect_encoding(path))
        df = pd.read_csv(path, sep=spec.get("sep", ","), encoding=enc, dtype=str)
    return df

def run():
    DATA_STAGING.mkdir(parents=True, exist_ok=True)
    report = []
    for name, spec in SOURCES.items():
        df = extract_one(spec)
        out = DATA_STAGING / f"stg_{name}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        report.append({"fuente": name, "filas": len(df), "cols": list(df.columns)})
        print(f"[EXTRACT] {name}: {len(df)} filas -> {out}")
    return report

if __name__ == "__main__":
    run()