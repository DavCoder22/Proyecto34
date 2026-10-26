"""Pipeline ETL completo: extract -> clean -> homologate -> validate -> transform -> load."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from extract import run as extract_run, extract_one
from clean import clean_entity
from homologate import run_all as homologate_all
from validate import validate_all, remove_rejected, append_rejections
from transform import add_business_rules
from load import load_all
from config import SOURCES, DATA_STAGING, DATA_RAW
from profile import main as profile_main
from quality_report import generate_comparison
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

    # 1. profile the untouched sources, then extract to staging
    profile_main()
    extract_run()

    # 2. read staging
    df_dict = {}
    for name, spec in SOURCES.items():
        p = DATA_STAGING / f"stg_{name}.csv"
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
    # Registrar y excluir filas que no pueden formar parte de un hecho analitico.
    if "ventas" in df_dict:
        v = df_dict["ventas"]
        invalid = v["fecha_venta"].isna()
        for col in ["cantidad", "precio_unitario", "descuento_pct"]:
            invalid |= v[col].isna()
        invalid |= (v["cantidad"] <= 0) | (v["precio_unitario"] < 0)
        invalid |= (v["descuento_pct"] < 0) | (v["descuento_pct"] > 1)
        rejected = v[invalid].copy()
        rejected["motivo"] = "Regla de validez: fecha o valor numerico invalido"
        append_rejections(rejected)
        df_dict["ventas"] = v[~invalid].reset_index(drop=True)

    # 6. transform (business rules)
    ventas_fact = add_business_rules(df_dict["ventas"], df_dict["productos"])

    # 7. load
    load_all(df_dict, ventas_fact)

    # 8. save cleaned staging
    for name, df in df_dict.items():
        df.to_csv(DATA_STAGING / f"clean_{name}.csv", index=False, encoding="utf-8-sig")
    ventas_fact.to_csv(DATA_STAGING / "fact_ventas.csv", index=False, encoding="utf-8-sig")
    generate_comparison(df_dict, ventas_fact)

    print("\n=== PIPELINE OK ===")
    print("Duplicados eliminados:", dup_report)
    print("FK rechazados:", fk_report)
    print("Ventas fact filas:", len(ventas_fact))

if __name__ == "__main__":
    main()
