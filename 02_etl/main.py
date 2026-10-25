"""Pipeline ETL completo: extract -> clean -> homologate -> validate -> transform -> load."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from extract import run as extract_run, extract_one
from clean import clean_entity
from homologate import run_all as homologate_all
from validate import validate_all, remove_rejected
from transform import add_business_rules
from load import load_all
from config import SOURCES, DATA_STAGING, DATA_RAW
import pandas as pd
import shutil

def main():
    # 0. asegurar raw copiado
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    for spec in SOURCES.values():
        src = Path(__file__).resolve().parents[2] / "datos" / spec["file"]
        dst = DATA_RAW / spec["file"]
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    # 1. extract
    extract_run()

    # 2. read staging
    df_dict = {}
    for name, spec in SOURCES.items():
        p = DATA_STAGING / f"stg_{name}.csv"
        if spec["file"].endswith((".xlsx",".xls")):
            df_dict[name] = pd.read_excel(DATA_RAW / spec["file"], sheet_name=spec.get("sheet",0))
        else:
            df_dict[name] = pd.read_csv(p, dtype=str, encoding="utf-8-sig")

    # 3. clean
    dup_report = {}
    for name in list(df_dict.keys()):
        df, n = clean_entity(name, df_dict[name])
        df_dict[name] = df
        dup_report[name] = n
        print(f"[CLEAN] {name}: {n} duplicados eliminados")

    # 4. homologate
    df_dict = homologate_all(df_dict)

    # 5. validate + remove rejected
    fk_report = validate_all(df_dict)
    df_dict = remove_rejected(df_dict)
    # eliminar filas con fecha nula (invalidas para analisis temporal)
    if "ventas" in df_dict:
        df_dict["ventas"] = df_dict["ventas"].dropna(subset=["fecha_venta"]).reset_index(drop=True)

    # 6. transform (business rules)
    ventas_fact = add_business_rules(df_dict["ventas"], df_dict["productos"])

    # 7. load
    load_all(df_dict, ventas_fact)

    # 8. save cleaned staging
    for name, df in df_dict.items():
        df.to_csv(DATA_STAGING / f"clean_{name}.csv", index=False, encoding="utf-8-sig")
    ventas_fact.to_csv(DATA_STAGING / "fact_ventas.csv", index=False, encoding="utf-8-sig")

    print("\n=== PIPELINE OK ===")
    print("Duplicados eliminados:", dup_report)
    print("FK rechazados:", fk_report)
    print("Ventas fact filas:", len(ventas_fact))

if __name__ == "__main__":
    main()