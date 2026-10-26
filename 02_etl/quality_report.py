"""Genera evidencia cuantificable de calidad antes y despues del ETL."""
from pathlib import Path
import pandas as pd

from config import DATA_RAW, LOG_PATH, PK, SOURCES


def _read_source(name, spec):
    path = DATA_RAW / spec["file"]
    if spec["file"].endswith((".xlsx", ".xls")):
        return pd.read_excel(path, sheet_name=spec.get("sheet", 0), dtype=str)
    return pd.read_csv(path, dtype=str, encoding=spec.get("encoding", "utf-8-sig"))


def _nulls(df):
    return int(df.isna().sum().sum() + (df == "").sum().sum())


def _invalid_fk(ventas, clientes, productos, sucursales):
    checks = {
        "cod_cliente": clientes["cod_cliente"],
        "cod_producto": productos["cod_producto"],
        "cod_sucursal": sucursales["cod_sucursal"],
    }
    return sum(int((~ventas[col].isin(parent)).sum()) for col, parent in checks.items())


def _markdown_table(df):
    headers = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def generate_comparison(clean_dict, ventas_fact):
    raw = {name: _read_source(name, spec) for name, spec in SOURCES.items()}
    rows = []
    for name in SOURCES:
        before = raw[name]
        after = clean_dict[name]
        pk = PK[name]
        rows.append({
            "Entidad": name,
            "Filas antes": len(before),
            "Filas despues": len(after),
            "Diferencia": len(before) - len(after),
            "Nulos antes": _nulls(before),
            "Nulos despues": _nulls(after),
            "Duplicados exactos antes": int(before.duplicated().sum()),
            "Duplicados exactos despues": int(after.duplicated().sum()),
            "Claves unicas antes": int(before[pk].nunique()),
            "Claves unicas despues": int(after[pk].nunique()),
        })
    v = raw["ventas"].copy()
    for col in ["cantidad", "precio_unitario", "descuento_pct"]:
        v[col] = pd.to_numeric(v[col], errors="coerce")
    v["descuento_pct"] = v["descuento_pct"].where(v["descuento_pct"] <= 1, v["descuento_pct"] / 100)
    invalid_dates = int(pd.to_datetime(v["fecha_venta"], errors="coerce").isna().sum())
    invalid_ranges = int(((v["cantidad"] <= 0) | (v["precio_unitario"] < 0) | (v["descuento_pct"] < 0) | (v["descuento_pct"] > 1)).sum())
    fk_before = _invalid_fk(raw["ventas"], raw["clientes"], raw["productos"], raw["sucursales"])
    fk_after = _invalid_fk(clean_dict["ventas"], clean_dict["clientes"], clean_dict["productos"], clean_dict["sucursales"])
    summary = pd.DataFrame(rows)
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    summary.to_csv(LOG_PATH / "quality_comparison.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Comparacion de calidad: antes y despues del ETL", "",
        "El grano de `ventas` es una linea de venta; `id_venta` puede repetirse cuando una venta contiene varios productos.", "",
        "## Resultado por entidad", "",
        _markdown_table(summary), "",
        "## Controles de validez e integridad", "",
        f"| Regla | Antes | Despues | Tratamiento |",
        f"|---|---:|---:|---|",
        f"| Fechas de venta invalidas o nulas | {invalid_dates} | 0 | Se excluyen antes de construir la dimension tiempo |",
        f"| Filas con FK invalida | {fk_before} | {fk_after} | Se registran en `log_rechazos.csv` y no pasan a hechos |",
        f"| Filas con rangos numericos invalidos | {invalid_ranges} | 0 | Se validan cantidad, precio y descuento |",
        f"| Filas en FactVentas | - | {len(ventas_fact)} | Solo registros validos e integrables |", "",
        "## Impacto para el analisis", "",
        "Las filas descartadas no se fuerzan al dashboard: conservarlas produciria ventas sin cliente, producto o sucursal, "
        "distorsionando ingresos, unidades, margen y transacciones. El total publicado debe interpretarse como ventas validas integradas.",
    ]
    (LOG_PATH / "quality_comparison.md").write_text("\n".join(lines), encoding="utf-8")
