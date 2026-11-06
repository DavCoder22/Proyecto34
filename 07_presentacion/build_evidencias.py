#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las evidencias gráficas de los cambios del dashboard y del modelo."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
EVID = ROOT / "evidencias"
EVID.mkdir(exist_ok=True)
DB = ROOT / "03_dw" / "dw.db"

NAVY = "#103F77"
RED = "#AB1926"
BLUE = "#2B6CB0"
GRAY = "#5A6472"


def _es(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def load():
    con = sqlite3.connect(DB)
    kpi = pd.read_sql_query(
        """
        SELECT SUM(venta_neta) ing, SUM(cantidad) uni, SUM(margen) mar,
               SUM(venta_bruta - venta_neta) desc, COUNT(DISTINCT id_venta) tx
        FROM FactVentas
        """,
        con,
    ).iloc[0].to_dict()
    cat = pd.read_sql_query(
        """
        SELECT p.categoria, SUM(f.venta_bruta - f.venta_neta) descuento
        FROM FactVentas f JOIN DimProducto p ON p.id_producto = f.id_producto
        GROUP BY p.categoria ORDER BY descuento DESC
        """,
        con,
    )
    con.close()
    rej_path = ROOT / "06_calidad" / "log_rechazos.csv"
    rej = pd.read_csv(rej_path, dtype=str, encoding="utf-8-sig")
    for col in ("cantidad", "precio_unitario", "descuento_pct"):
        rej[col] = pd.to_numeric(rej[col], errors="coerce").fillna(0)
    rej["descuento_pct"] = rej["descuento_pct"].where(
        rej["descuento_pct"] <= 1, rej["descuento_pct"] / 100
    )
    rej["venta_perdida"] = rej["cantidad"] * rej["precio_unitario"] * (1 - rej["descuento_pct"])
    return kpi, cat, rej


def modelo_actual():
    fig, ax = plt.subplots(figsize=(11.2, 5.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    def box(x, y, w, h, title, body, color, edge=NAVY):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.10",
            linewidth=1.2, edgecolor=edge, facecolor=color,
        ))
        ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
                fontsize=9, weight="bold", color=NAVY)
        ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center",
                fontsize=7.2, color=GRAY)

    def arrow(x1, y1, x2, y2, color=GRAY, dashed=False):
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12,
            linewidth=1.1, color=color, linestyle="--" if dashed else "-",
        ))

    box(0.2, 4.6, 2.3, 1.2, "DimTiempo", "fecha · año · mes", "#DCE6F1")
    box(0.2, 3.1, 2.3, 1.2, "DimCliente", "segmento · provincia", "#DCE6F1")
    box(0.2, 1.6, 2.3, 1.2, "DimProducto", "categoría · marca", "#DCE6F1")
    box(0.2, 0.1, 2.3, 1.2, "DimSucursal", "ciudad · región", "#DCE6F1")

    box(3.2, 3.0, 2.5, 1.8, "FactVentas", "línea de venta\nventa_neta · margen\nventa_bruta · descuento", "#FCE4D6")
    box(3.2, 0.3, 2.5, 1.5, "FactRechazos", "motivo · venta_perdida\nsucursal · fecha", "#F8CBAD")

    box(6.3, 3.6, 2.7, 1.7, "v_ventas_detalle", "hecho a nivel de línea\ncon todas las dimensiones", "#E2EFDA")
    box(6.3, 1.7, 2.7, 1.5, "v_mapa_consolidado", "provincias + sucursales\ngeo_key · categoría", "#E2EFDA")
    box(6.3, 0.1, 2.7, 1.3, "v_rechazos", "pérdidas por sucursal,\nfecha y motivo", "#E2EFDA")

    box(9.6, 2.3, 2.2, 2.2, "Apache Superset", "dashboard ejecutivo\nmapa-filtro · 8 KPIs\nfiltros cruzados", "#FFF2CC")

    for y in (5.2, 3.7, 2.2, 0.7):
        arrow(2.5, y, 3.2, 3.9)
    arrow(5.7, 3.9, 6.3, 4.45)
    arrow(5.7, 1.05, 6.3, 2.45, dashed=True)
    arrow(9.0, 4.45, 9.6, 3.9)
    arrow(9.0, 2.45, 9.6, 3.3)
    arrow(9.0, 0.75, 9.6, 2.7)

    ax.text(6, 6.6, "Modelo analítico actualizado: ventas válidas y rechazos valorizados",
            ha="center", fontsize=12.5, weight="bold", color=NAVY)
    ax.text(6, 6.25, "FactVentas alimenta las vistas analíticas; FactRechazos conserva la pérdida estimada.",
            ha="center", fontsize=8.5, style="italic", color=GRAY)
    fig.savefig(EVID / "modelo_actual.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def dashboard_actual(kpi, rej):
    perdida = float(rej["venta_perdida"].sum())
    tiles = [
        ("Ingresos", _es(kpi["ing"], 2)),
        ("Unidades", _es(kpi["uni"])),
        ("Margen", _es(kpi["mar"], 2)),
        ("Descuento", _es(kpi["desc"], 2)),
        ("Transacciones", _es(kpi["tx"])),
        ("Ticket prom.", _es(kpi["ing"] / kpi["tx"], 2)),
        ("Margen %", f"{kpi['mar']/kpi['ing']*100:.2f}%".replace(".", ",")),
        ("Pérdida rechazos", _es(perdida, 2)),
    ]
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.text(6, 8.6, "Evidencia del dashboard ejecutivo en Apache Superset",
            ha="center", fontsize=12.5, weight="bold", color=NAVY)
    for i, (label, value) in enumerate(tiles):
        row, col = divmod(i, 4)
        x = 0.25 + col * 2.92
        y = 7.45 - row * 0.95
        ax.add_patch(FancyBboxPatch(
            (x, y), 2.72, 0.82, boxstyle="round,pad=0.02,rounding_size=0.10",
            linewidth=1.0, edgecolor="#B8C4D6", facecolor="#EDF3FB",
        ))
        ax.text(x + 1.36, y + 0.54, value, ha="center", va="center",
                fontsize=9.2, weight="bold", color=NAVY)
        ax.text(x + 1.36, y + 0.20, label, ha="center", va="center",
                fontsize=6.8, color=GRAY)

    ax.add_patch(FancyBboxPatch((0.25, 3.55), 7.3, 3.25, boxstyle="round,pad=0.02,rounding_size=0.12",
                                linewidth=1.2, edgecolor=NAVY, facecolor="#EAF1FA"))
    ax.text(3.9, 6.5, "Mapa-filtro: provincias y sucursales", ha="center",
            fontsize=8.6, weight="bold", color=NAVY)
    ax.text(0.55, 5.35,
            "Relleno: azul claro → oscuro = intensidad de venta\n"
            "Borde: turquesa Costa · café Sierra · verde Amazonía\n"
            "Puntos rojos: sucursales seleccionables\n"
            "Clic en provincia/sucursal: filtra todo el dashboard\n"
            "Categoría: el mapa muestra dónde se vende",
            ha="left", va="center", fontsize=7.4, color=GRAY, linespacing=1.6)
    ax.add_patch(FancyBboxPatch((7.75, 3.55), 4.0, 3.25, boxstyle="round,pad=0.02,rounding_size=0.12",
                                linewidth=1.0, edgecolor="#B8C4D6", facecolor="#F4F7FB"))
    ax.text(9.75, 6.5, "Contenido del tablero", ha="center", fontsize=8.6, weight="bold", color=NAVY)
    ax.text(9.75, 5.1,
            "Participación por categoría\nEvolución de ventas\nCategoría · sucursal · segmento\nMarca · descuento · región · canal\nLíderes y pérdidas por sucursal/fecha",
            ha="center", va="center", fontsize=7.2, color=GRAY, linespacing=1.7)
    ax.text(6, 2.7, "8 KPIs · mapa-filtro · 5 filtros nativos · filtros cruzados · leyenda de color y región",
            ha="center", fontsize=9, weight="bold", color=RED)
    ax.text(6, 2.25, "Los rechazos se muestran como pérdida estimada, no como ventas válidas.",
            ha="center", fontsize=8, style="italic", color=GRAY)
    fig.savefig(EVID / "dashboard_actual.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def rechazos_descuento(cat, rej):
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))
    ax = axes[0]
    losses = rej.groupby("cod_sucursal", as_index=False).agg(
        n=("id_venta", "count"), perdida=("venta_perdida", "sum")
    ).sort_values("perdida", ascending=False).head(8)
    losses = losses.sort_values("perdida")
    bars = ax.barh(losses["cod_sucursal"], losses["perdida"], color="#9BBB59")
    ax.set_title("Pérdida estimada por rechazos según sucursal")
    ax.set_xlabel("USD")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: _es(x)))
    for bar, value, n in zip(bars, losses["perdida"], losses["n"]):
        ax.text(value + 120, bar.get_y() + bar.get_height() / 2,
                f"{_es(value, 2)} · {int(n)} reg.", va="center", fontsize=8)
    ax.set_xlim(0, losses["perdida"].max() * 1.35)
    ax.grid(axis="x", alpha=0.25)

    ax = axes[1]
    cat = cat.sort_values("descuento")
    bars = ax.barh(cat["categoria"], cat["descuento"], color="#C0504D")
    ax.set_title("Descuento otorgado por categoría")
    ax.set_xlabel("USD")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: _es(x)))
    for bar, value in zip(bars, cat["descuento"]):
        ax.text(value + 900, bar.get_y() + bar.get_height() / 2,
                _es(value, 2), va="center", fontsize=8)
    ax.set_xlim(0, cat["descuento"].max() * 1.28)
    ax.grid(axis="x", alpha=0.25)
    fig.suptitle("Los rechazos y los descuentos también son evidencia de gestión", fontsize=10, y=1.02)
    fig.tight_layout()
    fig.savefig(EVID / "rechazos_descuento.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    kpi, cat, rej = load()
    modelo_actual()
    dashboard_actual(kpi, rej)
    rechazos_descuento(cat, rej)
    print("Evidencias generadas en", EVID)


if __name__ == "__main__":
    main()
