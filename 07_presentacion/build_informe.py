#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageDraw, ImageFont

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ASSETS = OUT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
DOCX_PATH = OUT / "Informe_Practico_APA.docx"
PDF_PATH = OUT / "Informe_Practico_APA.pdf"

TITLE = (
    "Integración y calidad de datos para el análisis comercial: prueba de concepto "
    "con ETL, data warehouse y dashboard en Apache Superset"
)
REPO_URL = "https://github.com/DavCoder22/Proyecto34"

HEADINGS = [
    (1, "Introducción"),
    (2, "Planteamiento del problema"),
    (2, "Objetivos"),
    (3, "Objetivo general"),
    (3, "Objetivos específicos"),
    (2, "Justificación"),
    (2, "Alcance y estructura del documento"),
    (1, "Teoría"),
    (2, "Inteligencia de negocios y analítica"),
    (2, "ETL y data warehouse"),
    (2, "Calidad de datos"),
    (2, "Modelo dimensional"),
    (2, "KPIs y dashboards"),
    (2, "Apache Superset y tecnologías del stack"),
    (2, "Marco metodológico"),
    (1, "Metodología experimental"),
    (2, "Enfoque y diseño"),
    (2, "Fuentes de datos"),
    (2, "Fases del pipeline ETL"),
    (3, "Extracción"),
    (3, "Perfilado"),
    (3, "Limpieza"),
    (3, "Homologación"),
    (3, "Validación y rechazo"),
    (3, "Transformación"),
    (3, "Carga"),
    (2, "Reglas de calidad"),
    (2, "Modelo dimensional del data warehouse"),
    (2, "Definición de KPIs"),
    (2, "Construcción del dashboard"),
    (2, "Despliegue y reproducibilidad"),
    (2, "Consideraciones éticas"),
    (1, "Análisis y resultados"),
    (2, "Perfilado inicial"),
    (2, "Comparación de calidad antes y después"),
    (2, "Registros rechazados"),
    (2, "Modelo dimensional resultante"),
    (2, "Indicadores consolidados"),
    (2, "Evolución mensual de ventas"),
    (2, "Ventas por categoría"),
    (2, "Desempeño por sucursal"),
    (2, "Ventas por segmento"),
    (2, "Canales y métodos de pago"),
    (2, "Evidencia del dashboard"),
    (2, "Cumplimiento de objetivos"),
    (2, "Auditoría de consistencia de cifras"),
    (1, "Discusión de resultados"),
    (2, "Interpretación comercial"),
    (2, "Contraste con la teoría"),
    (2, "Limitaciones"),
    (2, "Validez y amenazas"),
    (1, "Conclusiones"),
    (1, "Recomendaciones"),
    (1, "Referencias"),
    (1, "Anexos"),
    (2, "Anexo A. Esquema del modelo estrella"),
    (2, "Anexo B. Vistas KPI"),
    (2, "Anexo C. Evidencia de rechazos"),
    (2, "Anexo D. Reproducibilidad"),
    (2, "Anexo E. Evidencias del proceso ETL y del dashboard en la nube"),
]

TABLES = [
    (1, "Fuentes de datos del caso de estudio"),
    (2, "Problemas observados y reglas de transformación"),
    (3, "Estructura del modelo estrella"),
    (4, "Definición de los indicadores del dashboard"),
    (5, "Tecnologías utilizadas y función en la solución"),
    (6, "Comparación de calidad antes y después del ETL"),
    (7, "Registros rechazados por motivo"),
    (8, "Indicadores consolidados del universo válido"),
    (9, "Ventas por categoría y margen bruto"),
    (10, "Desempeño por sucursal"),
    (11, "Ventas por segmento de cliente"),
    (12, "Canales de venta y métodos de pago"),
    (13, "Cumplimiento de los objetivos específicos"),
]

FIGURES = [
    (1, "Arquitectura de la solución"),
    (2, "Flujo del pipeline ETL"),
    (3, "Efecto del proceso de calidad sobre el universo de datos"),
    (4, "Evolución mensual de las ventas netas"),
    (5, "Participación de las categorías en las ventas netas"),
    (6, "Desempeño de las sucursales por región"),
    (7, "Participación de los segmentos de cliente"),
    (8, "Dashboard Sales Analytics generado desde el data warehouse"),
    (9, "Marcas líderes por venta neta"),
    (10, "Descuento otorgado por categoría"),
    (11, "Pérdida estimada por rechazos según sucursal"),
    (12, "Notebook de Jupyter con la ejecución del pipeline ETL"),
    (13, "Datos procesados en la etapa de staging"),
    (14, "Tablas originales y transformadas cargadas en Neon"),
    (15, "Comparación de calidad antes y después del ETL"),
    (16, "Reglas de transformación y justificación"),
    (17, "Dashboard Sales Analytics en Apache Superset"),
    (18, "Modelo analítico actualizado con FactRechazos y vistas nuevas"),
    (19, "Dashboard ejecutivo actualizado: KPIs, mapa-filtro y leyenda"),
    (20, "Pérdidas por rechazos y descuentos por categoría"),
]

ANNEXES = [
    ("A", "Esquema del modelo estrella"),
    ("B", "Vistas KPI"),
    ("C", "Evidencia de rechazos"),
    ("D", "Reproducibilidad"),
    ("E", "Evidencias del proceso ETL y del dashboard en la nube"),
]

PRELIM_TOC = [
    ("Datos del componente", "prelim:Datos del componente"),
    ("Derechos de autor", "prelim:Derechos de autor"),
    ("Aprobación del tutor", "prelim:Aprobación del tutor"),
    ("Tabla de contenidos", "prelim:Tabla de contenidos"),
    ("Lista de tablas", "prelim:Lista de tablas"),
    ("Lista de figuras", "prelim:Lista de figuras"),
    ("Lista de anexos", "prelim:Lista de anexos"),
    ("Resumen", "prelim:Resumen"),
    ("Abstract", "prelim:Abstract"),
]


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def money(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def integer(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def pct(value: float) -> str:
    return f"{value:.2f}%".replace(".", ",")


def load_data() -> dict:
    con = sqlite3.connect(BASE / "03_dw" / "dw.db")
    kpi = pd.read_sql_query(
        """
        SELECT SUM(venta_neta) AS ingresos, SUM(cantidad) AS unidades,
               SUM(margen) AS margen, SUM(venta_bruta - venta_neta) AS descuento,
               COUNT(DISTINCT id_venta) AS transacciones, COUNT(*) AS lineas
        FROM FactVentas
        """,
        con,
    ).iloc[0].to_dict()
    kpi["ticket_promedio"] = kpi["ingresos"] / kpi["transacciones"]
    kpi["margen_pct"] = kpi["margen"] / kpi["ingresos"] * 100

    category = pd.read_sql_query(
        "SELECT * FROM v_ventas_categoria ORDER BY venta_neta DESC", con
    )
    category_margin = pd.read_sql_query(
        """
        SELECT p.categoria, SUM(f.margen) AS margen
        FROM FactVentas f JOIN DimProducto p ON f.id_producto = p.id_producto
        GROUP BY p.categoria
        """,
        con,
    )
    category = category.merge(category_margin, on="categoria", how="left")
    branch = pd.read_sql_query(
        "SELECT * FROM v_ventas_sucursal ORDER BY venta_neta DESC", con
    )
    segment = pd.read_sql_query(
        "SELECT * FROM v_ventas_segmento ORDER BY venta_neta DESC", con
    )
    channel = pd.read_sql_query(
        "SELECT * FROM v_ventas_canal ORDER BY venta_neta DESC", con
    )
    payment = pd.read_sql_query(
        """
        SELECT metodo_pago, SUM(venta_neta) AS venta_neta, COUNT(*) AS lineas
        FROM FactVentas GROUP BY metodo_pago ORDER BY venta_neta DESC
        """,
        con,
    )
    months = pd.read_sql_query(
        "SELECT * FROM v_ventas_mes ORDER BY anio, mes", con
    )
    region = pd.read_sql_query(
        """
        SELECT s.region, SUM(f.venta_neta) AS venta_neta
        FROM FactVentas f JOIN DimSucursal s ON f.id_sucursal = s.id_sucursal
        GROUP BY s.region ORDER BY venta_neta DESC
        """,
        con,
    )
    brand = pd.read_sql_query(
        """
        SELECT p.marca, SUM(f.venta_neta) AS venta_neta, SUM(f.cantidad) AS unidades,
               SUM(f.venta_bruta - f.venta_neta) AS descuento_usd
        FROM FactVentas f JOIN DimProducto p ON f.id_producto = p.id_producto
        WHERE p.marca IS NOT NULL AND TRIM(p.marca) <> ''
        GROUP BY p.marca ORDER BY venta_neta DESC
        """,
        con,
    )
    discount_category = pd.read_sql_query(
        """
        SELECT p.categoria, SUM(f.venta_bruta - f.venta_neta) AS descuento_usd,
               AVG(f.descuento_pct) AS descuento_promedio
        FROM FactVentas f JOIN DimProducto p ON f.id_producto = p.id_producto
        GROUP BY p.categoria ORDER BY descuento_usd DESC
        """,
        con,
    )
    top_products = pd.read_sql_query(
        """
        SELECT p.nombre_producto, p.categoria, SUM(f.venta_neta) AS venta_neta
        FROM FactVentas f JOIN DimProducto p ON f.id_producto = p.id_producto
        GROUP BY p.id_producto ORDER BY venta_neta DESC LIMIT 5
        """,
        con,
    )
    dim_queries = {
        "DimCliente": "SELECT COUNT(*) FROM DimCliente",
        "DimProducto": "SELECT COUNT(*) FROM DimProducto",
        "DimSucursal": "SELECT COUNT(*) FROM DimSucursal",
        "DimTiempo": "SELECT COUNT(*) FROM DimTiempo",
        "FactVentas": "SELECT COUNT(*) FROM FactVentas",
    }
    dim_counts = {
        table: con.execute(query).fetchone()[0]
        for table, query in dim_queries.items()
    }
    period = con.execute("SELECT MIN(fecha), MAX(fecha) FROM DimTiempo").fetchone()
    con.close()

    quality = pd.read_csv(BASE / "06_calidad" / "quality_comparison.csv", encoding="utf-8-sig")
    quality.columns = [c.strip() for c in quality.columns]
    rejects = pd.read_csv(BASE / "06_calidad" / "log_rechazos.csv", encoding="utf-8-sig")
    rejects_by_motive = (
        rejects["motivo"].value_counts().rename_axis("motivo").reset_index(name="total")
    )

    clients = pd.read_csv(
        BASE / "01_datos" / "raw" / "clientes.csv", dtype=str, encoding="utf-8-sig"
    )
    branches = pd.read_csv(
        BASE / "01_datos" / "raw" / "sucursales.csv", dtype=str, encoding="utf-8-sig"
    )
    products = pd.read_excel(BASE / "01_datos" / "raw" / "productos.xlsx", dtype=str)
    sales = pd.read_csv(
        BASE / "01_datos" / "raw" / "ventas_sucursales.csv",
        dtype=str,
        encoding="utf-8-sig",
    )

    rejects_calc = rejects.copy()
    for column in ("cantidad", "precio_unitario", "descuento_pct"):
        rejects_calc[column] = pd.to_numeric(
            rejects_calc[column], errors="coerce"
        ).fillna(0)
    rejects_calc["descuento_pct"] = rejects_calc["descuento_pct"].where(
        rejects_calc["descuento_pct"] <= 1, rejects_calc["descuento_pct"] / 100
    )
    rejects_calc["venta_perdida"] = (
        rejects_calc["cantidad"] * rejects_calc["precio_unitario"]
        * (1 - rejects_calc["descuento_pct"])
    )
    branch_lookup = branches[["cod_sucursal", "nombre_sucursal", "region"]]
    rejects_loss = rejects_calc.merge(branch_lookup, on="cod_sucursal", how="left")
    rejects_loss["nombre_sucursal"] = rejects_loss["nombre_sucursal"].fillna(
        rejects_loss["cod_sucursal"]
    )
    rejects_total_loss = float(rejects_calc["venta_perdida"].sum())
    rejects_by_branch = (
        rejects_loss.groupby(["nombre_sucursal", "region"], as_index=False)
        .agg(num_rechazos=("id_venta", "count"), venta_perdida=("venta_perdida", "sum"))
        .sort_values("venta_perdida", ascending=False)
    )

    sources = {
        "clientes": {
            "archivo": "clientes.csv",
            "tipo": "CSV",
            "filas": len(clients),
            "columnas": clients.shape[1],
            "clave": "cod_cliente",
            "uso": "Dimensión cliente y segmentación",
        },
        "sucursales": {
            "archivo": "sucursales.csv",
            "tipo": "CSV",
            "filas": len(branches),
            "columnas": branches.shape[1],
            "clave": "cod_sucursal",
            "uso": "Dimensión sucursal y región",
        },
        "productos": {
            "archivo": "productos.xlsx",
            "tipo": "Excel",
            "filas": len(products),
            "columnas": products.shape[1],
            "clave": "cod_producto",
            "uso": "Dimensión producto, categoría y costo",
        },
        "ventas": {
            "archivo": "ventas_sucursales.csv",
            "tipo": "CSV",
            "filas": len(sales),
            "columnas": sales.shape[1],
            "clave": "id_venta",
            "uso": "Tabla de hechos a nivel de línea de venta",
        },
    }

    return {
        "kpi": kpi,
        "category": category,
        "branch": branch,
        "segment": segment,
        "channel": channel,
        "payment": payment,
        "months": months,
        "region": region,
        "brand": brand,
        "discount_category": discount_category,
        "top_products": top_products,
        "dim_counts": dim_counts,
        "period": period,
        "quality": quality,
        "rejects": rejects,
        "rejects_by_motive": rejects_by_motive,
        "rejects_total_loss": rejects_total_loss,
        "rejects_by_branch": rejects_by_branch,
        "sources": sources,
        "raw": {
            "clients": clients,
            "branches": branches,
            "products": products,
            "sales": sales,
        },
    }


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(ASSETS / name, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_assets(data: dict) -> None:
    plt.rcParams.update(
        {
            "font.family": "Liberation Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.unicode_minus": False,
        }
    )

    fig, ax = plt.subplots(figsize=(11.2, 4.4))
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    def box(x, y, w, h, title, subtitle, color, dashed=False):
        rect = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.03,rounding_size=0.12",
            linewidth=1.2,
            edgecolor="#444444",
            facecolor=color,
            linestyle="--" if dashed else "-",
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", weight="bold", fontsize=9)
        ax.text(x + w / 2, y + h * 0.28, subtitle, ha="center", va="center", fontsize=8)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.2,
                color="#555555",
            )
        )

    box(0.2, 2.35, 2.1, 1.25, "Fuentes de datos", "Clientes, sucursales,\nproductos y ventas", "#DCE6F1")
    box(2.8, 2.35, 2.3, 1.25, "ETL con Python", "Extracción, limpieza,\nhomologación y validación", "#E2EFDA")
    box(5.6, 2.35, 2.4, 1.25, "Data warehouse", "Modelo estrella en\nSQLite y PostgreSQL", "#FCE4D6")
    box(8.5, 2.35, 2.45, 1.25, "Visualización", "Apache Superset y\ndashboard HTML", "#FFF2CC")
    box(2.8, 0.45, 2.3, 1.0, "Calidad y trazabilidad", "profile_report, quality_comparison\ny log_rechazos", "#EDEDED", dashed=True)
    box(5.6, 0.45, 2.4, 1.0, "Vistas KPI", "Agregados por fecha,\ncategoría, sucursal y segmento", "#EDEDED", dashed=True)

    arrow(2.3, 2.98, 2.8, 2.98)
    arrow(5.1, 2.98, 5.6, 2.98)
    arrow(8.0, 2.98, 8.5, 2.98)
    arrow(3.95, 1.45, 3.95, 2.35)
    arrow(6.8, 1.45, 6.8, 2.35)
    arrow(5.1, 1.05, 5.6, 1.05)
    ax.text(5.6, 0.12, "El mismo universo validado alimenta la evidencia, el dashboard y los controles de calidad.", ha="center", fontsize=8, style="italic")
    save_figure(fig, "fig_arquitectura.png")

    fig, ax = plt.subplots(figsize=(11.2, 3.3))
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 3.3)
    ax.axis("off")
    labels = [
        ("Extracción", "CSV y Excel"),
        ("Perfilado", "nulos, duplicados\ny claves"),
        ("Limpieza y\nhomologación", "tipos, fechas,\ncategorías"),
        ("Validación", "FK, rangos y\nreglas de negocio"),
        ("Transformación", "venta neta,\ncosto y margen"),
        ("Carga", "SQLite y\nPostgreSQL"),
    ]
    x_positions = [0.2, 2.05, 3.9, 5.75, 7.6, 9.45]
    for i, (title, sub) in enumerate(labels):
        x = x_positions[i]
        rect = FancyBboxPatch(
            (x, 1.25),
            1.55,
            1.05,
            boxstyle="round,pad=0.03,rounding_size=0.10",
            linewidth=1.1,
            edgecolor="#444444",
            facecolor="#E2EFDA" if i < 3 else "#DCE6F1",
        )
        ax.add_patch(rect)
        ax.text(x + 0.775, 1.92, title, ha="center", va="center", weight="bold", fontsize=8)
        ax.text(x + 0.775, 1.53, sub, ha="center", va="center", fontsize=7.5)
        if i < len(labels) - 1:
            ax.add_patch(
                FancyArrowPatch(
                    (x + 1.57, 1.78),
                    (x_positions[i + 1] - 0.02, 1.78),
                    arrowstyle="-|>",
                    mutation_scale=10,
                    linewidth=1.1,
                    color="#555555",
                )
            )
    ax.add_patch(
        FancyBboxPatch(
            (5.6, 0.25),
            2.05,
            0.62,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            linewidth=1.0,
            edgecolor="#777777",
            facecolor="#EDEDED",
            linestyle="--",
        )
    )
    ax.text(6.625, 0.56, "log_rechazos.csv", ha="center", va="center", fontsize=8)
    ax.add_patch(
        FancyArrowPatch(
            (6.625, 0.87),
            (6.625, 1.25),
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.1,
            color="#777777",
            linestyle="--",
        )
    )
    ax.text(5.6, 2.85, "Cada fase deja evidencia reproducible y auditable.", ha="center", fontsize=8, style="italic")
    save_figure(fig, "fig_flujo_etl.png")

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.0))
    ax = axes[0]
    entities = ["Ventas", "Productos", "Clientes", "Sucursales"]
    removed = [70, 3, 6, 0]
    colors = ["#C0504D", "#4F81BD", "#9BBB59", "#8064A2"]
    bars = ax.barh(entities, removed, color=colors)
    ax.set_title("Registros eliminados por entidad")
    ax.set_xlabel("Cantidad de registros")
    ax.invert_yaxis()
    for bar, value in zip(bars, removed):
        ax.text(value + 1.2, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=8)
    ax.set_xlim(0, 80)
    ax.grid(axis="x", alpha=0.25)

    ax = axes[1]
    motives = ["Duplicados\nexactos", "Claves foráneas\ninválidas", "Fecha o valor\ninválido"]
    values = [20, 30, 20]
    bars = ax.bar(motives, values, color=["#4F81BD", "#C0504D", "#9BBB59"])
    ax.set_title("Causas de exclusión en ventas")
    ax.set_ylabel("Cantidad de registros")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.8, str(value), ha="center", fontsize=8)
    ax.set_ylim(0, 35)
    ax.grid(axis="y", alpha=0.25)
    fig.suptitle("El universo final conserva 6.800 de 6.870 líneas de venta (98,98 %)", fontsize=9, y=1.02)
    save_figure(fig, "fig_calidad.png")

    months = data["months"].copy()
    months["fecha"] = pd.to_datetime(
        months["anio"].astype(str) + "-" + months["mes"].astype(str).str.zfill(2) + "-01"
    )
    fig, ax = plt.subplots(figsize=(11.2, 4.2))
    ax.plot(months["fecha"], months["venta_neta"], color="#1F4E79", linewidth=1.8, marker="o", markersize=3)
    mean = months["venta_neta"].mean()
    ax.axhline(mean, color="#C0504D", linestyle="--", linewidth=1.0, label=f"Promedio mensual: ${money(mean)}")
    ax.fill_between(months["fecha"], months["venta_neta"], mean, color="#1F4E79", alpha=0.10)
    ax.set_title("Evolución mensual de ventas netas (enero 2024 - agosto 2026)")
    ax.set_ylabel("Venta neta (USD)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}".replace(",", ".")))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    max_row = months.loc[months["venta_neta"].idxmax()]
    ax.annotate(
        f"Máximo: ${money(max_row['venta_neta'])}",
        xy=(max_row["fecha"], max_row["venta_neta"]),
        xytext=(12, 12),
        textcoords="offset points",
        fontsize=8,
        arrowprops=dict(arrowstyle="-", color="#777777", lw=0.8),
    )
    save_figure(fig, "fig_evolucion.png")

    category = data["category"].sort_values("venta_neta")
    fig, ax = plt.subplots(figsize=(10.6, 4.2))
    bars = ax.barh(category["categoria"], category["venta_neta"], color="#4F81BD")
    ax.set_title("Participación de las categorías en las ventas netas")
    ax.set_xlabel("Venta neta (USD)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}".replace(",", ".")))
    for bar, value, share in zip(bars, category["venta_neta"], category["pct_participacion"]):
        ax.text(value + 18000, bar.get_y() + bar.get_height() / 2, f"{share:.2f}%".replace(".", ","), va="center", fontsize=8)
    ax.set_xlim(0, category["venta_neta"].max() * 1.16)
    ax.grid(axis="x", alpha=0.25)
    save_figure(fig, "fig_categoria.png")

    branch = data["branch"].sort_values("venta_neta")
    colors = ["#C0504D" if r == "Costa" else "#4F81BD" for r in branch["region"]]
    fig, ax = plt.subplots(figsize=(10.6, 4.8))
    bars = ax.barh(branch["nombre_sucursal"], branch["venta_neta"], color=colors)
    ax.set_title("Desempeño de las sucursales por región")
    ax.set_xlabel("Venta neta (USD)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}".replace(",", ".")))
    for bar, value in zip(bars, branch["venta_neta"]):
        ax.text(value + 9000, bar.get_y() + bar.get_height() / 2, f"${value/1_000_000:.2f}M".replace(".", ","), va="center", fontsize=7.5)
    ax.set_xlim(0, branch["venta_neta"].max() * 1.14)
    ax.grid(axis="x", alpha=0.25)
    ax.legend(
        handles=[Patch(facecolor="#4F81BD", label="Sierra"), Patch(facecolor="#C0504D", label="Costa")],
        frameon=False,
        fontsize=8,
        loc="lower right",
    )
    save_figure(fig, "fig_sucursal.png")

    segment = data["segment"]
    fig, ax = plt.subplots(figsize=(10.6, 4.0))
    bars = ax.bar(segment["segmento"], segment["venta_neta"], color=["#1F4E79", "#4F81BD", "#9BBB59", "#F2A900", "#A6A6A6"])
    ax.set_title("Participación de los segmentos de cliente")
    ax.set_ylabel("Venta neta (USD)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}".replace(",", ".")))
    total = data["kpi"]["ingresos"]
    for bar, value in zip(bars, segment["venta_neta"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 55000,
            f"{value/total*100:.2f}%".replace(".", ","),
            ha="center",
            fontsize=8,
        )
    ax.set_ylim(0, segment["venta_neta"].max() * 1.16)
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, "fig_segmento.png")

    brand = data["brand"].head(8).sort_values("venta_neta")
    fig, ax = plt.subplots(figsize=(10.6, 4.2))
    bars = ax.barh(brand["marca"], brand["venta_neta"], color="#1F4E79")
    ax.set_title("Marcas líderes por venta neta")
    ax.set_xlabel("Venta neta (USD)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}".replace(",", ".")))
    for bar, value, units in zip(bars, brand["venta_neta"], brand["unidades"]):
        ax.text(
            value + 6000, bar.get_y() + bar.get_height() / 2,
            f"${value/1_000_000:.2f}M · {int(units)} u.".replace(".", ","),
            va="center", fontsize=8,
        )
    ax.set_xlim(0, brand["venta_neta"].max() * 1.22)
    ax.grid(axis="x", alpha=0.25)
    save_figure(fig, "fig_marca.png")

    discount = data["discount_category"].sort_values("descuento_usd")
    fig, ax = plt.subplots(figsize=(10.6, 4.2))
    bars = ax.barh(discount["categoria"], discount["descuento_usd"], color="#C0504D")
    ax.set_title("Descuento otorgado por categoría")
    ax.set_xlabel("Descuento (USD)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}".replace(",", ".")))
    for bar, value, prom in zip(
        bars, discount["descuento_usd"], discount["descuento_promedio"]
    ):
        ax.text(
            value + 1200, bar.get_y() + bar.get_height() / 2,
            f"{money(value)} · {pct(prom*100)}",
            va="center", fontsize=8,
        )
    ax.set_xlim(0, discount["descuento_usd"].max() * 1.24)
    ax.grid(axis="x", alpha=0.25)
    save_figure(fig, "fig_descuento_categoria.png")

    losses = data["rejects_by_branch"].head(8).sort_values("venta_perdida")
    fig, ax = plt.subplots(figsize=(10.6, 4.6))
    bars = ax.barh(losses["nombre_sucursal"], losses["venta_perdida"], color="#9BBB59")
    ax.set_title("Pérdida estimada por rechazos, según sucursal")
    ax.set_xlabel("Venta perdida estimada (USD)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:,.0f}".replace(",", ".")))
    for bar, value, count in zip(
        bars, losses["venta_perdida"], losses["num_rechazos"]
    ):
        ax.text(
            value + 240, bar.get_y() + bar.get_height() / 2,
            f"${value:,.0f} · {int(count)} reg.".replace(",", "."),
            va="center", fontsize=8,
        )
    ax.set_xlim(0, losses["venta_perdida"].max() * 1.28)
    ax.grid(axis="x", alpha=0.25)
    save_figure(fig, "fig_rechazos_sucursal.png")

    kpi = data["kpi"]
    fig, ax = plt.subplots(figsize=(11.2, 6.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")

    def tile(x, y, w, h, title, value, color):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.10",
            linewidth=1.0, edgecolor="#B8C4D6", facecolor=color,
        ))
        ax.text(x + w / 2, y + h * 0.64, value, ha="center", va="center",
                fontsize=9.5, weight="bold", color="#103F77")
        ax.text(x + w / 2, y + h * 0.24, title, ha="center", va="center",
                fontsize=6.8, color="#44546A")

    kpis = [
        ("Ingresos", money(kpi["ingresos"])),
        ("Unidades", integer(kpi["unidades"])),
        ("Margen bruto", money(kpi["margen"])),
        ("Descuento", money(kpi["descuento"])),
        ("Transacciones", integer(kpi["transacciones"])),
        ("Ticket prom.", money(kpi["ticket_promedio"])),
        ("Margen %", pct(kpi["margen_pct"])),
        ("Pérdida rechazos", money(data["rejects_total_loss"])),
    ]
    for i, (label, value) in enumerate(kpis):
        row, col = divmod(i, 4)
        tile(0.25 + col * 2.95, 7.55 - row * 0.95, 2.75, 0.82, label, value, "#EDF3FB")

    ax.add_patch(FancyBboxPatch((0.25, 3.55), 7.4, 3.35, boxstyle="round,pad=0.02,rounding_size=0.12",
                                linewidth=1.2, edgecolor="#103F77", facecolor="#EAF1FA"))
    ax.text(3.95, 6.62, "Mapa interactivo de provincias y sucursales", ha="center",
            fontsize=8.5, weight="bold", color="#103F77")
    ax.text(
        0.55, 5.55,
        "Relleno: azul claro → azul oscuro = intensidad de venta.\n"
        "Borde: turquesa Costa · café Sierra · verde Amazonía.\n"
        "Puntos rojos: sucursales seleccionables.\n"
        "Clic en provincia o sucursal: filtra todo el dashboard.\n"
        "Categoría en el pastel: el mapa muestra solo donde se vende.",
        ha="left", va="center", fontsize=7.4, color="#44546A", linespacing=1.6,
    )
    ax.add_patch(FancyBboxPatch((7.85, 3.55), 3.9, 3.35, boxstyle="round,pad=0.02,rounding_size=0.12",
                                linewidth=1.0, edgecolor="#B8C4D6", facecolor="#F4F7FB"))
    ax.text(9.8, 6.55, "Participación por categoría", ha="center", fontsize=8.2,
            weight="bold", color="#103F77")
    ax.text(9.8, 5.2, "Pastel sincronizado con el mapa\ny con los filtros nativos\nde provincia, categoría,\nsucursal, marca y región.",
            ha="center", va="center", fontsize=7.4, color="#44546A", linespacing=1.6)

    ax.add_patch(FancyBboxPatch((0.25, 2.75), 11.5, 0.6, boxstyle="round,pad=0.02,rounding_size=0.10",
                                linewidth=1.0, edgecolor="#B8C4D6", facecolor="#EDF3FB"))
    ax.text(6.0, 3.05, "Evolución mensual de ventas netas", ha="center", va="center",
            fontsize=8, weight="bold", color="#103F77")

    rows = [
        (1.85, ["Ventas por categoría", "Desempeño por sucursal", "Ventas por segmento"]),
        (1.05, ["Ventas por marca", "Descuento por categoría", "Ventas por región", "Ventas por canal"]),
        (0.25, ["Marca más vendida", "Categoría más vendida", "Sucursal líder", "Pérdidas por sucursal", "Pérdidas por fecha"]),
    ]
    for y, labels in rows:
        n = len(labels)
        w = (11.5 - 0.15 * (n - 1)) / n
        for i, label in enumerate(labels):
            x = 0.25 + i * (w + 0.15)
            ax.add_patch(FancyBboxPatch((x, y), w, 0.62, boxstyle="round,pad=0.02,rounding_size=0.08",
                                        linewidth=0.9, edgecolor="#C9D2E0", facecolor="#F7F9FC"))
            ax.text(x + w / 2, y + 0.31, label, ha="center", va="center",
                    fontsize=6.9, color="#44546A")

    ax.text(6.0, 8.75, "Dashboard ejecutivo en Apache Superset", ha="center",
            fontsize=12, weight="bold", color="#103F77")
    ax.text(6.0, 8.45, "Un solo universo validado: 6.800 líneas de venta y 50 rechazos documentados",
            ha="center", fontsize=8, style="italic", color="#6B7785")
    save_figure(fig, "fig_dashboard.png")

    kpi_fig, kax = plt.subplots(figsize=(11.2, 2.1))
    kax.set_xlim(0, 12)
    kax.set_ylim(0, 2)
    kax.axis("off")
    for i, (label, value) in enumerate(kpis):
        x = 0.15 + i * 1.47
        kax.add_patch(FancyBboxPatch((x, 0.25), 1.33, 1.5, boxstyle="round,pad=0.02,rounding_size=0.08",
                                     linewidth=0.9, edgecolor="#B8C4D6", facecolor="#EDF3FB"))
        kax.text(x + 0.665, 1.18, value, ha="center", va="center", fontsize=7.6,
                 weight="bold", color="#103F77")
        kax.text(x + 0.665, 0.62, label, ha="center", va="center", fontsize=6.2, color="#44546A")
    save_figure(kpi_fig, "fig_superset_kpis.png")

    seal = Image.new("RGB", (420, 420), "white")
    draw = ImageDraw.Draw(seal)
    draw.ellipse((18, 18, 402, 402), outline="#333333", width=4)
    draw.ellipse((34, 34, 386, 386), outline="#777777", width=1)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 42
        )
        small = ImageFont.truetype(
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 15
        )
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    draw.multiline_text((210, 195), "SELLO\nUCE", font=font, fill="#333333", anchor="mm", align="center", spacing=8)
    draw.text((210, 285), "UNIVERSIDAD CENTRAL DEL ECUADOR", font=small, fill="#555555", anchor="mm")
    seal.save(ASSETS / "sello_placeholder.png")


def set_run_font(run, name="Times New Roman", size=12, bold=None, italic=None, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def set_style_font(style, name="Times New Roman", size=12, bold=None, italic=None):
    style.font.name = name
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def add_page_field(paragraph):
    run = paragraph.add_run()
    set_run_font(run, "Times New Roman", 12, bold=False)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(text)
    run._r.append(fld_end)


def set_page_number_format(section, fmt: str, start: int = 1):
    sect_pr = section._sectPr
    pg_num = sect_pr.find(qn("w:pgNumType"))
    if pg_num is None:
        pg_num = OxmlElement("w:pgNumType")
        sect_pr.append(pg_num)
    pg_num.set(qn("w:fmt"), fmt)
    pg_num.set(qn("w:start"), str(start))


def setup_section(section):
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)


def add_header_page_number(section):
    section.header.is_linked_to_previous = False
    header = section.header
    header.is_linked_to_previous = False
    for p in list(header.paragraphs):
        p._element.getparent().remove(p._element)
    paragraph = header.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    add_page_field(paragraph)


def no_indent(paragraph):
    paragraph.paragraph_format.first_line_indent = Cm(0)
    return paragraph


def body_p(doc, text="", indent=True, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, italic=False, size=12, name="Times New Roman", space_after=0, line_spacing=2.0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.first_line_indent = Cm(1.27) if indent else Cm(0)
    if text:
        run = p.add_run(text)
        set_run_font(run, name, size, bold=bold, italic=italic)
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(level=level)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    if level == 1:
        set_run_font(run, "Times New Roman", 12, bold=True)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif level == 2:
        set_run_font(run, "Times New Roman", 12, bold=True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif level == 3:
        set_run_font(run, "Times New Roman", 12, bold=True, italic=True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif level == 4:
        set_run_font(run, "Times New Roman", 12, bold=True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Cm(1.27)
    else:
        set_run_font(run, "Times New Roman", 12, bold=True, italic=True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Cm(1.27)
    return p


def add_toc_entry(doc, text, page, level=0):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(0 if level == 0 else 0.75)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    run = p.add_run(f"{text}\t{page}")
    set_run_font(run, "Times New Roman", 12)
    return p


def add_list_entry(doc, text, page):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    run = p.add_run(f"{text}\t{page}")
    set_run_font(run, "Times New Roman", 12)
    return p


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    for old in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        if edge in ("top", "bottom"):
            element.set(qn("w:val"), "single")
            element.set(qn("w:sz"), "6")
            element.set(qn("w:space"), "0")
            element.set(qn("w:color"), "000000")
        else:
            element.set(qn("w:val"), "nil")
        borders.append(element)
    tbl_pr.append(borders)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_table_together(table):
    rows = table.rows
    for idx, row in enumerate(rows):
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)
        if idx < len(rows) - 1:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.keep_with_next = True


def style_cell(cell, text, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = str(text)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for p in cell.paragraphs:
        p.alignment = align
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        for run in p.runs:
            set_run_font(run, "Arial", 8, bold=bold)


def add_table_caption(doc, number, title):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(f"Tabla {number}")
    set_run_font(run, "Times New Roman", 12, bold=True)
    run.add_break()
    run2 = p.add_run(title)
    set_run_font(run2, "Times New Roman", 12, italic=True)
    return p


def add_note(doc, text, size=8):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run("Nota. ")
    set_run_font(run, "Arial", size, italic=True)
    run2 = p.add_run(text)
    set_run_font(run2, "Arial", size)
    return p


def add_table(doc, number, title, headers, rows, widths=None, note=None, align_left_cols=()):
    add_table_caption(doc, number, title)
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    hdr = table.rows[0].cells
    for i, header in enumerate(headers):
        style_cell(hdr[i], header, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            align = WD_ALIGN_PARAGRAPH.LEFT if i in align_left_cols else WD_ALIGN_PARAGRAPH.CENTER
            style_cell(cells[i], value, align=align)
    if widths:
        table.autofit = False
        for i, width in enumerate(widths):
            table.columns[i].width = Inches(width)
            for cell in table.columns[i].cells:
                cell.width = Inches(width)
        tbl_pr = table._tbl.tblPr
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tbl_pr.append(layout)
    set_table_borders(table)
    set_repeat_header(table.rows[0])
    keep_table_together(table)
    if note:
        add_note(doc, note)
    return table


def add_figure_caption(doc, number, title):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(f"Figura {number}")
    set_run_font(run, "Times New Roman", 12, bold=True)
    run.add_break()
    run2 = p.add_run(title)
    set_run_font(run2, "Times New Roman", 12, italic=True)
    return p


def add_figure(doc, number, title, path, width=6.3, note=None):
    add_figure_caption(doc, number, title)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    run.add_picture(str(path), width=Inches(width))
    if note:
        add_note(doc, note)
    return p


def add_code(doc, text):
    for line in text.strip("\n").splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line if line else " ")
        set_run_font(run, "Courier New", 10)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_reference(doc, prefix, italic_text, suffix=""):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(-1.27)
    p.paragraph_format.left_indent = Cm(1.27)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    r1 = p.add_run(prefix)
    set_run_font(r1, "Times New Roman", 12)
    r2 = p.add_run(italic_text)
    set_run_font(r2, "Times New Roman", 12, italic=True)
    r3 = p.add_run(suffix)
    set_run_font(r3, "Times New Roman", 12)
    return p


def centered_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", 12, bold=True)
    return p


def build_prelim(doc, portada: dict, data: dict, page_map: dict):
    section = doc.sections[0]
    setup_section(section)
    set_page_number_format(section, "lowerRoman", 1)
    add_header_page_number(section)

    normal = doc.styles["Normal"]
    set_style_font(normal, "Times New Roman", 12)
    normal.paragraph_format.line_spacing = 2.0
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.first_line_indent = Cm(1.27)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    for level in range(1, 6):
        style = doc.styles[f"Heading {level}"]
        set_style_font(style, "Times New Roman", 12, bold=True, italic=(level in (3, 5)))
        style.paragraph_format.line_spacing = 2.0
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.first_line_indent = Cm(0)

    doc.core_properties.title = portada["titulo"]
    doc.core_properties.subject = "Informe práctico del Examen Complexivo"
    doc.core_properties.author = ", ".join(a["apellidos_nombres"] for a in portada["autores"])

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    seal_path = ASSETS / "sello_uce.png"
    if not seal_path.exists():
        seal_path = ASSETS / "sello_placeholder.png"
    p.add_run().add_picture(str(seal_path), width=Inches(1.25))

    body_p(doc, "", indent=False)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(portada["titulo"])
    set_run_font(run, "Times New Roman", 12, bold=True)

    body_p(doc, "", indent=False)
    authors = portada["autores"]
    label = "Autor:" if len(authors) == 1 else "Autores:"
    for i, author in enumerate(authors):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 2.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        prefix = f"{label} " if i == 0 else ""
        run = p.add_run(prefix + author["apellidos_nombres"])
        set_run_font(run, "Times New Roman", 12)

    body_p(doc, "", indent=False)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run("Tutor: " + portada["tutor"]["apellidos_nombres"])
    set_run_font(run, "Times New Roman", 12)

    body_p(doc, "", indent=False)
    for line in [portada["facultad"], portada["carrera"], portada["modalidad"]]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 2.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line)
        set_run_font(run, "Times New Roman", 12)

    body_p(doc, "", indent=False)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(f"{portada['ciudad']}, {portada['anio']}")
    set_run_font(run, "Times New Roman", 12)

    authors_names = " y ".join(a["apellidos_nombres"] for a in authors)
    author_ids = ", ".join(
        f"{author['apellidos_nombres']} (C.C. {author['cedula']})" for author in authors
    )
    doc.add_page_break()
    centered_title(doc, "Datos del componente")
    component_rows = [
        ("Componente", portada.get("componente", "")),
        ("Subcomponente", portada.get("subcomponente", "")),
        ("Tema específico", portada.get("tema_especifico", "")),
        ("Propuesta del tema", f"{portada.get('autor_propuesta', '')} (C.C. {portada.get('cedula_propuesta', '')})"),
        ("Autor del informe", author_ids),
        ("Correo institucional", ", ".join(author["correo"] for author in authors)),
        ("Tutor", f"{portada['tutor']['apellidos_nombres']} (C.C. {portada['tutor']['cedula']})"),
        ("Carrera", portada.get("carrera", "")),
        ("Repositorio", portada.get("repositorio", REPO_URL)),
    ]
    for label, value in component_rows:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 2.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(f"{label}: ")
        set_run_font(run, "Times New Roman", 12, bold=True)
        run2 = p.add_run(value)
        set_run_font(run2, "Times New Roman", 12)

    doc.add_page_break()
    centered_title(doc, "Derechos de autor")
    singular = len(authors) == 1
    pronoun = "Yo" if singular else "Nosotros"
    quality = "autor y titular" if singular else "autores y titulares"
    concedo = "concedo" if singular else "concedemos"
    conservo = "Conservo" if singular else "Conservamos"
    posesivo = "mi" if singular else "nuestro"
    autorizo = "autorizo" if singular else "autorizamos"
    declara = "El autor declara" if singular else "Los autores declaran"
    body_p(
        doc,
        f"{pronoun} {authors_names}, en calidad de {quality} de los derechos morales y patrimoniales "
        f"del trabajo de titulación {portada['titulo']}, modalidad Examen Complexivo teórico-práctico, de conformidad "
        "con el Art. 114 del CÓDIGO ORGÁNICO DE LA ECONOMÍA SOCIAL DE LOS CONOCIMIENTOS, CREATIVIDAD E INNOVACIÓN, "
        f"{concedo} a favor de la Universidad Central del Ecuador una licencia gratuita, intransferible y no "
        f"exclusiva para el uso no comercial de la obra, con fines estrictamente académicos. {conservo} a {posesivo} "
        "favor todos los derechos de autor sobre la obra, establecidos en la normativa citada.",
        indent=False,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    body_p(
        doc,
        f"Asimismo, {autorizo} a la Universidad Central del Ecuador para que realice la digitalización y "
        "publicación de este trabajo de titulación en el repositorio virtual, de conformidad con lo dispuesto en el "
        "Art. 144 de la LEY ORGÁNICA DE EDUCACIÓN SUPERIOR.",
        indent=False,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    body_p(
        doc,
        f"{declara} que la obra objeto de la presente autorización es original en su forma de expresión y "
        "no infringe el derecho de autor de terceros, asumiendo la responsabilidad por cualquier reclamación que "
        "pudiera presentarse por esta causa y liberando a la Universidad de toda responsabilidad.",
        indent=False,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    firma_path = BASE / "evidencias" / "firma.png"
    for author in authors:
        body_p(doc, "", indent=False)
        if firma_path.exists():
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.add_run().add_picture(str(firma_path), width=Inches(1.55))
        body_p(doc, "Firma: ______________________________", indent=False)
        body_p(doc, author["apellidos_nombres"], indent=False)
        body_p(doc, f"C.C. {author['cedula']}", indent=False)
        body_p(doc, f"Dirección electrónica: {author['correo']}", indent=False)
    approval_title = centered_title(doc, "Aprobación del tutor")
    approval_title.paragraph_format.page_break_before = True
    body_p(
        doc,
        f"En mi calidad de Tutor del Trabajo de Titulación, presentado por {authors_names}, para optar por el título "
        f"de Ingeniero(a) en Sistemas de Información; cuyo título es: {portada['titulo']}, considero que dicho "
        "trabajo reúne los requisitos y méritos suficientes para ser sometido a la presentación pública y evaluación "
        "por parte del tribunal examinador que se designe.",
        indent=False,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    body_p(doc, f"En la ciudad de Quito, {portada.get('fecha_aprobacion', '____ de __________')} de 2026.", indent=False)
    body_p(doc, "", indent=False)
    body_p(doc, "", indent=False)
    body_p(doc, "____________________________________", indent=False)
    body_p(doc, portada["tutor"]["apellidos_nombres"], indent=False)
    body_p(doc, portada["tutor"]["cargo"], indent=False)
    body_p(doc, f"C.C. {portada['tutor']['cedula']}", indent=False)

    doc.add_page_break()
    centered_title(doc, "Tabla de contenidos")
    for label, key in PRELIM_TOC:
        add_toc_entry(doc, label, page_map.get(key, "00"), level=0)
    for level, text in HEADINGS:
        if level <= 2:
            add_toc_entry(doc, text, page_map.get(f"h:{text}", "00"), level=max(0, level - 1))

    doc.add_page_break()
    centered_title(doc, "Lista de tablas")
    for number, title in TABLES:
        add_list_entry(doc, f"Tabla {number}. {title}", page_map.get(f"table:{number}", "00"))

    doc.add_page_break()
    centered_title(doc, "Lista de figuras")
    for number, title in FIGURES:
        add_list_entry(doc, f"Figura {number}. {title}", page_map.get(f"figure:{number}", "00"))

    doc.add_page_break()
    centered_title(doc, "Lista de anexos")
    for letter, title in ANNEXES:
        add_list_entry(doc, f"Anexo {letter}. {title}", page_map.get(f"annex:{letter}", "00"))

    doc.add_page_break()
    body_p(doc, portada["titulo"], indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    body_p(doc, "Autores: " + authors_names, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
    body_p(doc, "Tutor: " + portada["tutor"]["apellidos_nombres"], indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
    body_p(doc, "", indent=False)
    centered_title(doc, "Resumen")
    resumen = (
        "El presente trabajo desarrolla una prueba de concepto para integrar, limpiar, validar y visualizar datos "
        "comerciales provenientes de cuatro fuentes heterogéneas: clientes, sucursales, productos y ventas. El "
        "problema identificado es la dispersión de la información y la presencia de duplicados, valores nulos, "
        "fechas inválidas, categorías con distinta escritura y claves foráneas inexistentes, lo que afecta la "
        "confiabilidad de los indicadores. La metodología combinó un pipeline ETL con Python y pandas, un modelo "
        "dimensional en esquema estrella y un dashboard en Apache Superset. Se aplicaron reglas de limpieza, "
        "homologación, validación referencial y cálculo de ingresos, margen y ticket promedio. Los resultados "
        "muestran que el universo inicial de 6.870 líneas de venta se redujo a 6.800 registros válidos, con una "
        "cobertura del 98,98 %. El dashboard consolida 7.452.222,71 USD de ingresos netos, 13.817 unidades, "
        "1.966.780,12 USD de margen bruto y 3.587 transacciones. La categoría Accesorios concentra el 20,80 % de "
        "las ventas y el segmento Masivo el 50,85 %. Se concluye que la calidad de datos es una condición necesaria "
        "para que los indicadores comerciales sean auditables y útiles en la toma de decisiones."
    )
    body_p(doc, resumen, indent=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    r1 = p.add_run("Palabras clave: ")
    set_run_font(r1, "Times New Roman", 12, bold=False, italic=True)
    r2 = p.add_run("Inteligencia de negocios, Calidad de datos, ETL, Modelo dimensional")
    set_run_font(r2, "Times New Roman", 12)

    doc.add_page_break()
    body_p(doc, "TITLE: Integration and data quality for commercial analysis: a proof of concept with ETL, data warehouse and an Apache Superset dashboard", indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    body_p(doc, "Authors: " + authors_names, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
    body_p(doc, "Tutor: " + portada["tutor"]["apellidos_nombres"], indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
    body_p(doc, "", indent=False)
    centered_title(doc, "Abstract")
    abstract = (
        "This work develops a proof of concept to integrate, clean, validate and visualize commercial data from "
        "four heterogeneous sources: customers, branches, products and sales. The identified problem is the "
        "dispersion of information and the presence of duplicates, null values, invalid dates, inconsistent "
        "category spellings and non-existent foreign keys, which affect the reliability of the indicators. The "
        "methodology combined an ETL pipeline with Python and pandas, a star-schema dimensional model and an "
        "Apache Superset dashboard. Cleaning, homologation, referential validation and revenue, margin and average "
        "ticket calculations were applied. The results show that the initial universe of 6,870 sales lines was "
        "reduced to 6,800 valid records, with 98.98 % coverage. The dashboard consolidates USD 7,452,222.71 in net "
        "revenue, 13,817 units, USD 1,966,780.12 in gross margin and 3,587 transactions. The Accessories category "
        "accounts for 20.80 % of sales and the Masivo segment for 50.85 %. It is concluded that data quality is a "
        "necessary condition for commercial indicators to be auditable and useful for decision-making."
    )
    body_p(doc, abstract, indent=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    r1 = p.add_run("Keywords: ")
    set_run_font(r1, "Times New Roman", 12, bold=False, italic=True)
    r2 = p.add_run("Business intelligence, Data quality, ETL, Dimensional modeling")
    set_run_font(r2, "Times New Roman", 12)


def build_body(doc, data: dict):
    k = data["kpi"]
    total = k["ingresos"]
    q = data["quality"]
    qmap = {row["Entidad"]: row for _, row in q.iterrows()}
    cat = data["category"]
    branch = data["branch"]
    seg = data["segment"]
    chan = data["channel"]
    pay = data["payment"]
    months = data["months"]
    region = data["region"]
    dims = data["dim_counts"]
    period_start = str(data["period"][0])[:10]
    period_end = str(data["period"][1])[:10]
    months_count = len(months)
    top_cat = cat.iloc[0]
    top_branch = branch.iloc[0]
    top_seg = seg.iloc[0]
    top_product = data["top_products"].iloc[0]
    rejects = data["rejects"]

    heading(doc, "Introducción", 1)
    body_p(
        doc,
        "Las organizaciones comerciales generan datos en múltiples sistemas: registros de clientes, catálogos de "
        "productos, información de sucursales y transacciones de venta. Cuando esas fuentes no comparten claves, "
        "formatos ni reglas de negocio, los reportes pueden mostrar cifras inconsistentes y las decisiones se "
        "apoyan en información parcial. La inteligencia de negocios surge precisamente para convertir esos datos "
        "dispersos en información útil para el análisis y la gestión (Sharda et al., 2020). Sin embargo, la "
        "visualización por sí sola no corrige los problemas de origen; antes es necesario integrar, limpiar y "
        "validar los datos (Kimball & Ross, 2013).",
    )
    body_p(
        doc,
        "La presente prueba de concepto aborda ese problema en un escenario académico con cuatro fuentes "
        "heterogéneas. El proceso construye un pipeline ETL, genera un data warehouse en esquema estrella, calcula "
        "ocho indicadores comerciales y de calidad y publica un dashboard interactivo. La evidencia se documenta con reportes "
        "de perfilado, comparación antes/después, reglas de transformación y un log de rechazos, de modo que cada "
        "cifra publicada pueda rastrearse hasta su origen.",
    )

    heading(doc, "Planteamiento del problema", 2)
    body_p(
        doc,
        "Las fuentes del caso presentan problemas típicos de integración: 6.870 líneas de venta con 20 duplicados "
        "exactos, 30 registros con claves foráneas inexistentes y 20 filas con fechas o valores numéricos inválidos. "
        "Además, los catálogos contienen duplicados, valores nulos y categorías escritas de formas distintas. Si "
        "esos registros se cargan sin control, el dashboard puede sumar ventas sin cliente, producto o sucursal, o "
        "contar dos veces una misma operación. El problema, por tanto, no es solo técnico: afecta la confianza en "
        "los indicadores y la calidad de las decisiones comerciales.",
    )
    body_p(
        doc,
        "La pregunta que orienta el trabajo es la siguiente: ¿cómo integrar y depurar cuatro fuentes comerciales "
        "heterogéneas para producir un conjunto de indicadores trazables, reproducibles y útiles para la toma de "
        "decisiones? Para responderla se diseña una PoC que prioriza la evidencia cuantificable de calidad y la "
        "trazabilidad de cada KPI.",
    )

    heading(doc, "Objetivos", 2)
    heading(doc, "Objetivo general", 3)
    body_p(
        doc,
        "Diseñar e implementar una prueba de concepto de integración, calidad de datos y visualización comercial "
        "que permita obtener indicadores confiables a partir de cuatro fuentes heterogéneas, con trazabilidad "
        "completa desde el dato de origen hasta el dashboard.",
    )
    heading(doc, "Objetivos específicos", 3)
    objetivos = [
        "Integrar las fuentes de clientes, sucursales, productos y ventas mediante un pipeline ETL reproducible.",
        "Aplicar reglas de limpieza, homologación y validación referencial, documentando los registros rechazados y su motivo.",
        "Construir un data warehouse en esquema estrella con dimensiones de tiempo, cliente, producto y sucursal, y una tabla de hechos de ventas.",
        "Calcular los indicadores de ingresos netos, unidades vendidas, margen bruto y número de transacciones.",
        "Publicar un dashboard interactivo en Apache Superset y una evidencia HTML que permita contrastar los resultados.",
        "Verificar la consistencia entre la fuente, el data warehouse y el dashboard, y documentar las limitaciones de la PoC.",
    ]
    for i, objetivo in enumerate(objetivos, 1):
        body_p(doc, f"{i}. {objetivo}", indent=False)

    heading(doc, "Justificación", 2)
    body_p(
        doc,
        "La PoC se justifica porque demuestra, con datos verificables, que la calidad de datos cambia el universo "
        "analítico y la interpretación de los resultados. No se limita a mover archivos: documenta cuántos registros "
        "se eliminan, por qué se eliminan y cómo se evita el doble conteo. Esa evidencia es relevante para un tribunal "
        "académico y para una mesa de decisiones, porque permite distinguir entre un dato faltante y un dato "
        "inválido, y entre una venta real y una venta huérfana.",
    )
    body_p(
        doc,
        "Adicionalmente, la solución utiliza herramientas abiertas y contenedores, lo que reduce el costo de "
        "experimentación y facilita la reproducción en distintos entornos. El diseño puede escalar a producción con "
        "un orquestador, una base PostgreSQL gestionada y un gobierno de datos formal, sin reescribir las reglas de "
        "negocio principales.",
    )

    heading(doc, "Alcance y estructura del documento", 2)
    body_p(
        doc,
        "El alcance cubre la integración batch de cuatro fuentes, la construcción del modelo estrella, el cálculo "
        "de indicadores comerciales y de calidad y la publicación de un dashboard. No incluye carga incremental, streaming, modelos "
        "predictivos, presupuestos por meta ni gobierno de datos corporativo. Los datos son de carácter académico y "
        "no representan personas reales; aun así, el diseño prevé la anonimización como requisito para un entorno "
        "productivo.",
    )
    body_p(
        doc,
        "El documento se organiza en ocho secciones. La introducción presenta el problema y los objetivos; la teoría "
        "define los conceptos de BI, ETL, calidad, modelo dimensional y dashboards; la metodología describe las "
        "fuentes, las fases y las reglas aplicadas; el análisis presenta los resultados; la discusión interpreta los "
        "hallazgos y sus limitaciones; las conclusiones y recomendaciones cierran el estudio; finalmente se incluyen "
        "las referencias y los anexos técnicos. El formato del documento se apega a los lineamientos de publicación "
        "de la Universidad Central del Ecuador (2022) y a la estructura de la guía metodológica del examen complexivo "
        "(Universidad Central del Ecuador, Facultad de Ingeniería y Ciencias Aplicadas, 2026).",
    )

    heading(doc, "Teoría", 1)
    heading(doc, "Inteligencia de negocios y analítica", 2)
    body_p(
        doc,
        "La inteligencia de negocios (BI) comprende las prácticas, tecnologías y aplicaciones que permiten "
        "recopilar, integrar, analizar y presentar información para apoyar la toma de decisiones (Sharda et al., "
        "2020). Su valor no reside únicamente en el reporte final, sino en la capacidad de convertir datos operativos "
        "en una representación coherente del negocio. La analítica, por su parte, añade métodos para explorar "
        "patrones y generar conocimiento a partir de los datos (Provost & Fawcett, 2013).",
    )
    body_p(
        doc,
        "En una organización comercial, la BI permite responder preguntas como qué categorías generan más ingresos, "
        "qué sucursales tienen mejor desempeño o qué segmentos concentran el volumen. Para que esas respuestas sean "
        "válidas, el dato debe ser consistente, completo y trazable. De ahí la importancia de un proceso ETL y de un "
        "modelo de datos bien definido.",
    )

    heading(doc, "ETL y data warehouse", 2)
    body_p(
        doc,
        "El ETL (extract, transform, load) es el proceso que extrae datos de las fuentes, los transforma según reglas "
        "de negocio y los carga en un repositorio analítico. Kimball y Ross (2013) plantean que el data warehouse "
        "debe organizarse alrededor de procesos de negocio y de un modelo dimensional que facilite la consulta. En "
        "ese enfoque, la tabla de hechos almacena las métricas y las dimensiones describen el contexto: quién, qué, "
        "cuándo y dónde.",
    )
    body_p(
        doc,
        "El pipeline de la PoC sigue esa lógica. Primero extrae los archivos originales a una zona de staging; luego "
        "perfila, limpia, homologa y valida; después transforma las reglas de negocio y finalmente carga el modelo "
        "estrella en SQLite y, si está configurado, en PostgreSQL. La separación por etapas permite auditar cada "
        "paso y repetir el proceso con los mismos insumos.",
    )

    heading(doc, "Calidad de datos", 2)
    body_p(
        doc,
        "La calidad de datos se evalúa a partir de dimensiones como exactitud, completitud, consistencia, "
        "oportunidad y unicidad (Batini et al., 2009; Pipino et al., 2002). La norma ISO 8000-61 propone un modelo "
        "de referencia para gestionar la calidad como un proceso, no como una revisión aislada (ISO, 2016). En la "
        "práctica, esto implica definir reglas, medir el efecto de cada regla y conservar evidencia de los registros "
        "que no cumplen.",
    )
    body_p(
        doc,
        "La PoC operacionaliza esas dimensiones con controles concretos: eliminación de duplicados exactos, "
        "tratamiento de nulos, normalización de fechas y descuentos, homologación de categorías y validación de "
        "claves foráneas. Los registros que no superan los controles se excluyen del hecho y se registran en "
        "log_rechazos.csv con su motivo. Así, la calidad no se declara: se mide y se documenta.",
    )

    heading(doc, "Modelo dimensional", 2)
    body_p(
        doc,
        "El modelo estrella es una estructura compuesta por una tabla de hechos central y dimensiones que la "
        "rodean. La tabla de hechos contiene las claves foráneas y las métricas del proceso; las dimensiones "
        "contienen atributos descriptivos y jerarquías. Este diseño simplifica las consultas analíticas y mejora el "
        "rendimiento frente a un modelo normalizado (Kimball & Ross, 2013).",
    )
    body_p(
        doc,
        "En el caso de estudio, la tabla FactVentas tiene grano de línea de venta, es decir, una fila por producto "
        "vendido dentro de una transacción. Las dimensiones DimTiempo, DimCliente, DimProducto y DimSucursal "
        "permiten filtrar por fecha, segmento, categoría y sucursal. Las métricas venta_neta, costo_total y margen "
        "se calculan con reglas explícitas para que el dashboard no replique la lógica en cada consulta.",
    )

    heading(doc, "KPIs y dashboards", 2)
    body_p(
        doc,
        "Un KPI es un indicador cuantificable que refleja el desempeño de un proceso o de un objetivo de negocio. "
        "Para que sea útil, debe tener una definición estable, una fuente identificable y una fórmula reproducible. "
        "Few (2006) señala que un dashboard efectivo prioriza la información necesaria para decidir y evita el "
        "exceso de gráficos sin contexto.",
    )
    body_p(
        doc,
        "La PoC define cuatro indicadores principales: ingresos netos, unidades vendidas, margen bruto y número de "
        "transacciones. A ellos se suman el ticket promedio, el margen porcentual, el descuento otorgado y la pérdida "
        "estimada por rechazos. Cada indicador se calcula sobre el mismo universo validado y se complementa con cortes "
        "por tiempo, categoría, sucursal, segmento, marca, región y canal. El dashboard incluye filtros y una nota "
        "metodológica para recordar que las cifras representan el universo válido, no una estimación de ventas "
        "faltantes.",
    )

    heading(doc, "Apache Superset y tecnologías del stack", 2)
    body_p(
        doc,
        "Apache Superset es una plataforma de BI de código abierto que permite conectar bases de datos, crear "
        "datasets, gráficos y dashboards interactivos (Apache Software Foundation, 2026). Su integración con "
        "PostgreSQL y su despliegue mediante contenedores la hacen adecuada para una PoC reproducible. El dashboard "
        "se complementa con una versión HTML generada desde SQLite, útil como evidencia cuando no se dispone de un "
        "servidor de BI.",
    )
    body_p(
        doc,
        "El procesamiento se realiza con Python y pandas, que ofrecen operaciones vectorizadas para limpieza y "
        "transformación (pandas Development Team, 2026). PostgreSQL actúa como motor del data warehouse para "
        "Superset (PostgreSQL Global Development Group, 2026), mientras que SQLite sirve como respaldo local. Docker "
        "facilita la ejecución portable (Docker Inc., 2026) y Northflank permite publicar los servicios en la nube "
        "(Northflank, 2026).",
    )

    heading(doc, "Marco metodológico", 2)
    body_p(
        doc,
        "El trabajo se apoya en un enfoque aplicado, cuantitativo y descriptivo. La metodología de investigación "
        "guía la formulación del problema, la recolección de evidencia y la interpretación de resultados "
        "(Hernández-Sampieri & Mendoza, 2018). Para el ciclo de vida de los datos se toma como referencia CRISP-DM, "
        "que organiza el trabajo en comprensión del negocio, comprensión de los datos, preparación, modelado, "
        "evaluación y despliegue (Wirth & Hipp, 2000).",
    )
    body_p(
        doc,
        "La adaptación de CRISP-DM a esta PoC es directa: el negocio se traduce en indicadores comerciales y de calidad; los datos se "
        "perfilan; la preparación corresponde al ETL; el modelado es el esquema estrella; la evaluación se realiza "
        "con comparaciones antes/después y controles de totales; y el despliegue se concreta en Docker, Northflank y "
        "Superset. Esta correspondencia permite justificar cada etapa con evidencia verificable.",
    )

    heading(doc, "Metodología experimental", 1)
    heading(doc, "Enfoque y diseño", 2)
    body_p(
        doc,
        "La investigación es aplicada, cuantitativa y descriptiva. Es aplicada porque resuelve un problema concreto "
        "de integración y análisis comercial; es cuantitativa porque mide registros, proporciones e indicadores; y "
        "es descriptiva porque caracteriza el estado de las fuentes y el efecto de las reglas de calidad. El diseño "
        "es no experimental y transversal: no se manipulan variables del negocio, sino que se observa el resultado "
        "del pipeline sobre un corte de datos de enero de 2024 a agosto de 2026.",
    )
    body_p(
        doc,
        "La unidad de análisis es la línea de venta. Cada fila de FactVentas representa un producto dentro de una "
        "transacción; por eso una misma venta puede tener varias líneas. Esta decisión es importante: si se contara "
        "el número de filas como número de ventas, se sobreestimaría el indicador de transacciones. El conteo de "
        "transacciones se realiza con COUNT(DISTINCT id_venta), mientras que los ingresos, las unidades y el margen "
        "se suman por línea.",
    )
    body_p(
        doc,
        "El procedimiento se ejecutó en seis momentos: caracterización de fuentes, definición de reglas, "
        "implementación del ETL, construcción del modelo estrella, cálculo y publicación de KPIs, y verificación de "
        "consistencia. Todos los scripts y reportes quedaron versionados en el repositorio, de modo que el resultado "
        "pueda reproducirse con los mismos archivos de entrada.",
    )

    heading(doc, "Fuentes de datos", 2)
    body_p(
        doc,
        "Se utilizaron cuatro fuentes: clientes y sucursales en CSV, productos en Excel y ventas en CSV. La Tabla 1 "
        "resume el volumen y la función de cada una. Las ventas son la fuente principal del hecho; las demás "
        "alimentan las dimensiones y permiten segmentar los resultados.",
    )
    source_rows = []
    for name, info in data["sources"].items():
        source_rows.append(
            [
                name.capitalize(),
                info["archivo"],
                info["tipo"],
                integer(info["filas"]),
                info["clave"],
                info["uso"],
            ]
        )
    add_table(
        doc,
        1,
        "Fuentes de datos del caso de estudio",
        ["Fuente", "Archivo", "Tipo", "Filas", "Clave", "Uso"],
        source_rows,
        widths=[0.8, 1.3, 0.5, 0.5, 0.9, 2.5],
        note="Elaboración propia a partir de los archivos de 01_datos/raw. Las filas corresponden a los registros originales, antes de la limpieza.",
        align_left_cols=(0, 1, 5),
    )
    body_p(
        doc,
        "La fuente de ventas contiene 6.870 líneas y 3.600 identificadores únicos de venta antes de la limpieza, lo "
        "que confirma que el grano es la línea y no la transacción. El catálogo de productos tiene 123 filas y 120 "
        "claves únicas; el de clientes, 1.006 filas y 1.000 claves; y el de sucursales, 12 filas sin duplicados. "
        "Esas diferencias son la primera señal de que los catálogos requieren depuración antes de relacionarse con "
        "el hecho.",
    )
    body_p(
        doc,
        "La Figura 1 resume la arquitectura de la solución. Las fuentes alimentan un ETL que deja evidencia de "
        "calidad, carga un data warehouse en esquema estrella y publica los resultados en Superset y en un "
        "dashboard HTML. El mismo universo validado se utiliza para el análisis, los controles y la visualización.",
    )
    add_figure(
        doc,
        1,
        "Arquitectura de la solución",
        ASSETS / "fig_arquitectura.png",
        width=6.4,
        note="Elaboración propia a partir de 02_etl/, 03_dw/, 04_dashboard/ y docker/.",
    )

    heading(doc, "Fases del pipeline ETL", 2)
    body_p(
        doc,
        "El pipeline se implementó en Python con módulos separados por responsabilidad: extract.py, profile.py, "
        "clean.py, homologate.py, validate.py, transform.py, load.py y main.py. La separación permite probar cada "
        "fase y reemplazarla sin reescribir todo el proceso. La Figura 2 muestra la secuencia general.",
    )
    add_figure(
        doc,
        2,
        "Flujo del pipeline ETL",
        ASSETS / "fig_flujo_etl.png",
        width=6.4,
        note="Elaboración propia a partir de 02_etl/main.py. La validación alimenta el log de rechazos y separa los registros que no pueden formar parte del hecho.",
    )
    heading(doc, "Extracción", 3)
    body_p(
        doc,
        "La extracción copia los archivos originales a la zona de staging y los lee con pandas. Para CSV se usa "
        "codificación UTF-8 con BOM y para Excel se lee la primera hoja. En esta fase no se modifica el contenido: "
        "se conserva una copia del dato original para poder comparar antes y después. La evidencia de perfilado se "
        "genera antes de cualquier transformación.",
    )
    heading(doc, "Perfilado", 3)
    body_p(
        doc,
        "El perfilado describe filas, columnas, claves únicas, valores nulos, duplicados exactos y distribución de "
        "valores categóricos. Su objetivo es detectar problemas antes de decidir una regla. Por ejemplo, el "
        "perfilado de clientes mostró 1.006 filas con 1.000 claves únicas y 10 valores nulos en segmento; el de "
        "productos, 123 filas con 120 claves y 5 marcas nulas; y el de ventas, 6.870 filas con 3.600 claves únicas "
        "y 27 nulos repartidos entre canal y método de pago.",
    )
    heading(doc, "Limpieza", 3)
    body_p(
        doc,
        "La limpieza normaliza cadenas, elimina espacios, convierte valores vacíos en nulos y ajusta tipos de datos. "
        "En ventas se eliminan duplicados exactos, se interpretan las fechas con pandas.to_datetime y se convierten cantidad, precio y descuento a "
        "numérico. En productos se convierte el costo unitario. En clientes y sucursales se normalizan fechas. La "
        "limpieza no imputa valores de negocio: cuando un dato no existe, se deja como nulo o se reemplaza por una "
        "categoría explícita de no especificado, según la regla definida.",
    )
    heading(doc, "Homologación", 3)
    body_p(
        doc,
        "La homologación unifica variantes de escritura. En categorías, TECNOLOGÍA, tecnologia y tecnología se "
        "transforman en Tecnología. En segmento, los valores vacíos se convierten en Sin segmento. En canal y método "
        "de pago, los vacíos se convierten en No especificado. Esta fase evita que una misma categoría aparezca como "
        "varias series en el dashboard y hace visible la incertidumbre en lugar de ocultarla.",
    )
    heading(doc, "Validación y rechazo", 3)
    body_p(
        doc,
        "La validación comprueba que las claves foráneas de ventas existan en clientes, productos y sucursales. "
        "También verifica que la fecha sea válida, que la cantidad sea mayor que cero, que el precio no sea negativo "
        "y que el descuento esté entre 0 y 1. Las filas que no cumplen se excluyen del hecho y se registran en "
        "log_rechazos.csv con el motivo. Esta decisión evita ventas huérfanas y permite monitorear la tasa de "
        "rechazo como un indicador de calidad del origen.",
    )
    heading(doc, "Transformación", 3)
    body_p(
        doc,
        "La transformación aplica las reglas de negocio: venta_bruta = cantidad × precio_unitario; venta_neta = "
        "venta_bruta × (1 − descuento); costo_total = cantidad × costo_unitario; y margen = venta_neta − costo_total. "
        "El descuento se normaliza antes de calcular: si un valor es mayor que 1, se interpreta como porcentaje y se "
        "divide para 100. Cuando el costo de un producto es desconocido, no se imputa cero, porque eso "
        "sobreestimaría el margen; el margen queda como desconocido y se excluye del agregado correspondiente.",
    )
    heading(doc, "Carga", 3)
    body_p(
        doc,
        "La carga escribe el modelo estrella en SQLite y, si la variable DATABASE_URL está definida, también en "
        "PostgreSQL. Las vistas KPI se recrean en cada ejecución para que Superset y el dashboard HTML consuman el "
        "mismo universo validado. La carga es idempotente: si se vuelve a ejecutar el pipeline, las tablas se "
        "reemplazan y los resultados son los mismos para los mismos insumos.",
    )

    heading(doc, "Reglas de calidad", 2)
    body_p(
        doc,
        "La Tabla 2 resume los problemas observados, la fuente afectada, la regla aplicada y el efecto esperado. "
        "Las reglas se diseñaron para preservar la mayor cantidad de información posible sin aceptar registros que "
        "distorsionen los agregados. Cuando una fila no se puede integrar, se rechaza y se documenta; no se fuerza "
        "su inclusión.",
    )
    rule_rows = [
        ["Duplicados exactos", "Las cuatro fuentes", "Eliminar filas idénticas; en catálogos conservar una fila por clave natural", "Evitar doble conteo y claves repetidas"],
        ["Fechas heterogéneas o inválidas", "Clientes, sucursales y ventas", "Parsear con pandas.to_datetime; excluir ventas sin fecha válida", "Dimensión tiempo con fechas válidas y agrupación mensual confiable"],
        ["Descuentos en decimal o porcentaje", "Ventas", "Valores mayores que 1 se dividen para 100", "Descuento entre 0 y 1 para calcular venta neta"],
        ["Categorías con distinta escritura", "Productos", "Homologar mayúsculas, minúsculas y acentos a un catálogo canónico", "Una sola serie por categoría en el dashboard"],
        ["Segmento, canal o método vacío", "Clientes y ventas", "Reemplazar vacío por una categoría explícita de no especificado", "No perder filas y hacer visible la incertidumbre"],
        ["Claves foráneas inexistentes", "Ventas", "Registrar el rechazo y excluir la línea del hecho integrado", "Impedir ventas huérfanas que distorsionen filtros y agregados"],
        ["Costo de producto desconocido", "Productos", "No imputar cero; conservar el margen como desconocido", "No sobreestimar artificialmente el margen bruto"],
        ["Tipos numéricos almacenados como texto", "Ventas y productos", "Convertir cantidad, precio, descuento y costo a numérico", "Cálculos reproducibles de ingresos y margen"],
    ]
    add_table(
        doc,
        2,
        "Problemas observados y reglas de transformación",
        ["Problema", "Fuente", "Regla aplicada", "Efecto esperado"],
        rule_rows,
        widths=[1.35, 1.05, 2.35, 1.75],
        note="Elaboración propia a partir de 06_calidad/reglas_transformacion.md y de la implementación en 02_etl/.",
        align_left_cols=(0, 1, 2, 3),
    )

    heading(doc, "Modelo dimensional del data warehouse", 2)
    body_p(
        doc,
        "El modelo estrella resultante tiene una tabla de hechos y cuatro dimensiones. La Tabla 3 describe el grano, "
        "las claves y las métricas principales. La dimensión tiempo usa una clave inteligente con formato AAAAMMDD; "
        "las dimensiones de cliente, producto y sucursal usan claves sustitutas enteras para desacoplar el modelo de "
        "las claves naturales del origen.",
    )
    model_rows = [
        ["FactVentas", "Línea de venta", "id_venta_pk; id_tiempo, id_cliente, id_producto, id_sucursal", "cantidad, precio_unitario, descuento_pct, venta_bruta, venta_neta, costo_total, margen"],
        ["DimTiempo", "Día", "id_tiempo", "fecha, anio, mes, mes_nombre, trimestre, semana, dia_semana"],
        ["DimCliente", "Cliente", "id_cliente; cod_cliente", "nombre, segmento, ciudad, provincia, fecha_registro, estado"],
        ["DimProducto", "Producto", "id_producto; cod_producto", "nombre, categoria, subcategoria, marca, costo_unitario, estado"],
        ["DimSucursal", "Sucursal", "id_sucursal; cod_sucursal", "nombre, ciudad, provincia, region, fecha_apertura, estado"],
    ]
    add_table(
        doc,
        3,
        "Estructura del modelo estrella",
        ["Tabla", "Grano", "Claves", "Atributos o métricas"],
        model_rows,
        widths=[0.95, 0.85, 1.75, 2.95],
        note="Elaboración propia a partir de 03_dw/schema.sql y 03_dw/schema_sqlite.sql.",
        align_left_cols=(0, 1, 2, 3),
    )

    heading(doc, "Definición de KPIs", 2)
    body_p(
        doc,
        "Los indicadores principales se definen sobre FactVentas para garantizar que todos los cortes utilicen la "
        "misma base. La Tabla 4 presenta la expresión SQL y la interpretación de cada indicador. El ticket promedio "
        "se calcula por transacción, no por línea: primero se suman las líneas de cada id_venta y luego se promedia, "
        "para no sesgar el resultado hacia ventas con más productos. El descuento otorgado y la pérdida estimada por "
        "rechazos se incorporan como indicadores complementarios de gestión comercial y de calidad.",
    )
    kpi_rows = [
        ["Ingresos netos", "SUM(venta_neta)", "Dinero efectivamente reconocido después del descuento"],
        ["Unidades vendidas", "SUM(cantidad)", "Volumen físico de productos vendidos"],
        ["Margen bruto", "SUM(margen)", "Diferencia entre venta neta y costo de los productos"],
        ["Transacciones", "COUNT(DISTINCT id_venta)", "Número de operaciones comerciales, no de líneas"],
        ["Ticket promedio", "SUM(venta_neta) / COUNT(DISTINCT id_venta)", "Venta neta media por operación"],
        ["Margen %", "SUM(margen) / SUM(venta_neta)", "Rentabilidad relativa sobre ingresos netos"],
        ["Descuento otorgado", "SUM(venta_bruta − venta_neta)", "Monto cedido por descuentos; se analiza por categoría y provincia"],
        ["Pérdida por rechazos", "SUM(venta_perdida) en fact_rechazos", "Venta estimada que no entró al hecho; se monitorea por sucursal y fecha"],
    ]
    add_table(
        doc,
        4,
        "Definición de los indicadores del dashboard",
        ["Indicador", "Expresión", "Interpretación"],
        kpi_rows,
        widths=[1.25, 1.95, 3.3],
        note="Elaboración propia a partir de 04_dashboard/kpi_views_postgres.sql y del notebook 02_etl/01_etl_pipeline.ipynb.",
        align_left_cols=(0, 1, 2),
    )
    body_p(
        doc,
        "Además de los ocho indicadores, el dashboard presenta cortes por categoría, sucursal, segmento, marca, "
        "región, canal y método de pago. Cada corte se calcula sobre el mismo universo y se expresa como participación "
        "porcentual sobre los ingresos netos. El mapa provincial funciona como filtro: al seleccionar una provincia o "
        "una sucursal, el resto de gráficos se recalcula; al seleccionar una categoría en el pastel, el mapa muestra "
        "solo las sucursales donde se vende esa categoría y colorea por intensidad de venta.",
    )

    heading(doc, "Construcción del dashboard", 2)
    body_p(
        doc,
        "El dashboard Sales Analytics se organiza en capas de decisión. La primera fila contiene ocho tarjetas de "
        "KPI: ingresos netos, unidades, margen bruto, descuento otorgado, transacciones, ticket promedio, margen "
        "porcentual y pérdida por rechazos. La segunda fila combina el mapa provincial con el pastel de participación "
        "por categoría. Debajo se presenta la evolución mensual y, luego, los cortes de categoría, sucursal, segmento, "
        "marca, descuento, región y canal. La última sección muestra los líderes (marca, categoría y sucursal) y las "
        "pérdidas por sucursal y por fecha.",
    )
    body_p(
        doc,
        "El mapa es el filtro principal. Los polígonos representan provincias y los puntos rojos, sucursales. Al hacer "
        "clic en una provincia o en una sucursal, Superset emite un filtro cruzado y todos los gráficos se recalculan. "
        "Al seleccionar una categoría en el pastel, el mapa se filtra y colorea por la intensidad de venta de esa "
        "categoría, de modo que se identifican las sucursales donde se comercializa. La leyenda explica la escala de "
        "color y el borde regional: turquesa para la Costa, café para la Sierra y verde para la Amazonía.",
    )
    body_p(
        doc,
        "La construcción sigue tres pasos. Primero se crean las vistas KPI en la base de datos, incluida la vista de "
        "detalle que comparte dimensiones para habilitar el filtrado cruzado. Segundo se definen los datasets y "
        "gráficos en Superset. Tercero se valida que los totales del dashboard coincidan con la consulta de control "
        "sobre FactVentas. Esa validación es la que convierte el dashboard en evidencia y no solo en una ilustración.",
    )

    heading(doc, "Despliegue y reproducibilidad", 2)
    body_p(
        doc,
        f"La solución puede ejecutarse de forma local o en la nube. El código fuente y los entregables están "
        f"disponibles en el repositorio {REPO_URL}. En local, el comando run_local.bat o docker compose levanta "
        "PostgreSQL, Jupyter y Superset. En la nube, el job ETL de Northflank carga los datos en Neon y el servicio "
        "Superset los publica en el puerto 8008. El ETL se ejecuta mediante el job dedicado o al arrancar Jupyter; "
        "después, Superset consume las tablas y vistas del data warehouse.",
    )
    body_p(
        doc,
        "La reproducibilidad se apoya en cuatro elementos: archivos de entrada versionados, scripts con rutas "
        "relativas, variables de entorno para credenciales y un log de ejecución con los conteos de duplicados, "
        f"rechazos y filas del hecho. Cualquier persona con el repositorio ({REPO_URL}) y las dependencias puede "
        "repetir el proceso y obtener las mismas cifras. La Tabla 5 resume las tecnologías y su función.",
    )
    tech_rows = [
        ["Extracción y transformación", "Python + pandas", "Lectura de CSV/Excel, limpieza, homologación y cálculo de métricas"],
        ["Data warehouse local", "SQLite", "Evidencia reproducible y respaldo del dashboard HTML"],
        ["Data warehouse en BI", "PostgreSQL", "Almacenamiento del modelo estrella para Superset"],
        ["Visualización", "Apache Superset", "Dashboard interactivo con mapa-filtro, ocho KPIs y filtros cruzados"],
        ["Evidencia HTML", "HTML + JavaScript", "Versión portable del dashboard generada desde SQLite"],
        ["Contenedores", "Docker / Docker Compose", "Ejecución portable de Jupyter, PostgreSQL y Superset"],
        ["Nube", "Northflank + Neon", "Job ETL y servicio Superset en el puerto 8008"],
    ]
    add_table(
        doc,
        5,
        "Tecnologías utilizadas y función en la solución",
        ["Capa", "Tecnología", "Función"],
        tech_rows,
        widths=[1.7, 1.5, 3.3],
        note="Elaboración propia a partir de requirements.txt, docker/ y deploy/SUPERSET_DEPLOY.md.",
        align_left_cols=(0, 1, 2),
    )

    heading(doc, "Consideraciones éticas", 2)
    body_p(
        doc,
        "Los datos utilizados son de carácter académico y no corresponden a personas reales. Aun así, el diseño "
        "contempla la minimización de datos, la anonimización de nombres y la restricción de acceso a credenciales. "
        "Las variables de entorno se mantienen fuera del repositorio y las contraseñas de ejemplo no deben reutilizarse "
        "en producción. La publicación de resultados agregados evita exponer información individual.",
    )

    heading(doc, "Análisis y resultados", 1)
    heading(doc, "Perfilado inicial", 2)
    body_p(
        doc,
        f"El perfilado se realizó antes de cualquier transformación. El periodo analizado comprende del "
        f"{period_start} al {period_end}, con {months_count} meses. La fuente de ventas tenía 6.870 líneas, "
        f"3.600 identificadores únicos y 27 valores nulos; clientes tenía 1.006 filas, 1.000 claves únicas y 10 "
        f"nulos en segmento; productos tenía 123 filas, 120 claves únicas y 5 marcas nulas; y sucursales tenía 12 "
        f"filas completas. Los duplicados exactos fueron 20 en ventas, 6 en clientes y 3 en productos.",
    )
    body_p(
        doc,
        "El perfilado también mostró variantes de escritura en categorías (por ejemplo, TECNOLOGÍA frente a "
        "Tecnología) y en ciudades (QUITO, Quito y quito). Esos hallazgos justificaron una fase de homologación "
        "antes de la validación, porque de lo contrario una misma categoría se habría dividido en varias series y "
        "habría distorsionado la participación porcentual.",
    )

    heading(doc, "Comparación de calidad antes y después", 2)
    body_p(
        doc,
        "La Tabla 6 compara el estado de las entidades antes y después del ETL. En ventas, la diferencia de 70 "
        "filas se explica por 20 duplicados exactos, 30 registros con claves foráneas inválidas y 20 filas con "
        "fecha o valores numéricos inválidos. En clientes se eliminaron 6 duplicados y en productos 3. El total de "
        "duplicados exactos en las cuatro fuentes fue 29: 20 en ventas y 9 en los catálogos. Las 70 filas "
        "excluidas del hecho corresponden solo a ventas: 20 duplicados, 30 claves inválidas y 20 fechas o valores inválidos.",
    )
    quality_rows = []
    for entity in ["clientes", "sucursales", "productos", "ventas"]:
        row = qmap[entity]
        quality_rows.append(
            [
                entity.capitalize(),
                integer(row["Filas antes"]),
                integer(row["Filas despues"]),
                integer(row["Diferencia"]),
                integer(row["Nulos antes"]),
                integer(row["Nulos despues"]),
                integer(row["Duplicados exactos antes"]),
                integer(row["Claves unicas despues"]),
            ]
        )
    add_table(
        doc,
        6,
        "Comparación de calidad antes y después del ETL",
        ["Entidad", "Filas antes", "Filas después", "Diferencia", "Nulos antes", "Nulos después", "Duplicados", "Claves únicas"],
        quality_rows,
        widths=[0.85, 0.85, 0.85, 0.75, 0.7, 0.7, 0.85, 0.95],
        note="Elaboración propia a partir de 06_calidad/quality_comparison.csv. Los duplicados corresponden a filas exactas antes de la limpieza.",
        align_left_cols=(0,),
    )
    add_figure(
        doc,
        3,
        "Efecto del proceso de calidad sobre el universo de datos",
        ASSETS / "fig_calidad.png",
        width=6.3,
        note="Elaboración propia con los datos de 06_calidad/quality_comparison.csv y 06_calidad/log_rechazos.csv. La cobertura final es 98,98 %.",
    )
    body_p(
        doc,
        "El resultado más importante es que la reducción no fue arbitraria: cada fila excluida tiene una causa "
        "documentada. Las ventas pasaron de 6.870 a 6.800 líneas, con una cobertura de 98,98 %. Los nulos de ventas "
        "se eliminaron porque las filas afectadas también carecían de fecha o de valores numéricos válidos, o porque "
        "correspondían a duplicados. En clientes quedaron 8 nulos de segmento, que se homologaron como Sin segmento; "
        "en productos quedaron 5 marcas nulas, que no impiden el análisis por categoría.",
    )

    heading(doc, "Registros rechazados", 2)
    body_p(
        doc,
        f"El log de rechazos contiene {len(rejects)} registros: 30 por claves foráneas inexistentes y 20 por fecha "
        "o valores numéricos inválidos. Las claves foráneas se reparten en 12 clientes, 10 productos y 8 sucursales "
        "inexistentes. La Tabla 7 resume los motivos. Estos registros no se imputan ni se fuerzan: se excluyen del "
        "hecho y se conservan como evidencia para que el área de origen corrija la causa.",
    )
    reject_rows = []
    for _, row in data["rejects_by_motive"].iterrows():
        reject_rows.append([row["motivo"], integer(row["total"]), "Excluido del hecho y registrado en log_rechazos.csv"])
    reject_rows.append(["Total de rechazos", integer(len(rejects)), "Tasa de rechazo: 0,73 % sobre 6.850 filas después de deduplicar"])
    add_table(
        doc,
        7,
        "Registros rechazados por motivo",
        ["Motivo", "Registros", "Tratamiento"],
        reject_rows,
        widths=[3.0, 0.8, 2.7],
        note="Elaboración propia a partir de 06_calidad/log_rechazos.csv. La tasa de rechazo se calcula sobre las filas que quedan después de eliminar duplicados exactos.",
        align_left_cols=(0, 2),
    )
    body_p(
        doc,
        f"La tasa de rechazo es un indicador que debe monitorearse. Si aumenta o se concentra en una sucursal o "
        f"categoría, la tendencia observada puede quedar sesgada. Para no perder esa información, los rechazos se "
        f"cargan en la tabla fact_rechazos con su motivo y una pérdida estimada de "
        f"{money(data['rejects_total_loss'])} USD, calculada como cantidad × precio × (1 − descuento). Así, el "
        f"dashboard puede mostrar las pérdidas por sucursal y por fecha sin confundirlas con ventas válidas.",
    )

    heading(doc, "Modelo dimensional resultante", 2)
    body_p(
        doc,
        f"El data warehouse quedó conformado por {integer(dims['FactVentas'])} filas en FactVentas, "
        f"{integer(dims['DimCliente'])} clientes, {integer(dims['DimProducto'])} productos, {integer(dims['DimSucursal'])} "
        f"sucursales y {integer(dims['DimTiempo'])} días con ventas en DimTiempo. La diferencia entre 3.600 identificadores "
        "únicos de venta en la fuente y 3.587 en el hecho se explica por los rechazos: algunas ventas tenían todas "
        "sus líneas inválidas o compartían identificador con registros duplicados. El hecho conserva 6.800 líneas, "
        "que equivalen a 1,90 líneas por transacción en promedio.",
    )
    body_p(
        doc,
        "El modelo permite responder consultas analíticas sin repetir la lógica de negocio. Por ejemplo, la venta "
        "neta ya está calculada en el hecho; el margen ya descuenta el costo; y las dimensiones permiten agrupar por "
        "mes, categoría, sucursal o segmento. Esa separación es la que hace que Superset pueda crear gráficos con "
        "filtros cruzados sin recalcular las reglas en cada visualización.",
    )

    heading(doc, "Indicadores consolidados", 2)
    body_p(
        doc,
        f"La Tabla 8 presenta los indicadores del universo válido. Los ingresos netos ascienden a "
        f"{money(k['ingresos'])} USD; las unidades vendidas, a {integer(k['unidades'])}; el margen bruto, a "
        f"{money(k['margen'])} USD; y las transacciones, a {integer(k['transacciones'])}. El margen representa "
        f"{pct(k['margen_pct'])} de los ingresos y el ticket promedio por transacción es {money(k['ticket_promedio'])} USD. "
        f"El descuento otorgado suma {money(k['descuento'])} USD y la pérdida estimada por rechazos, "
        f"{money(data['rejects_total_loss'])} USD.",
    )
    kpi_result_rows = [
        ["Ingresos netos", "SUM(venta_neta)", money(k["ingresos"])],
        ["Unidades vendidas", "SUM(cantidad)", integer(k["unidades"])],
        ["Margen bruto", "SUM(margen)", money(k["margen"])],
        ["Transacciones", "COUNT(DISTINCT id_venta)", integer(k["transacciones"])],
        ["Ticket promedio", "ingresos / transacciones", money(k["ticket_promedio"])],
        ["Margen %", "margen / ingresos", pct(k["margen_pct"])],
        ["Descuento otorgado", "SUM(venta_bruta − venta_neta)", money(k["descuento"])],
        ["Pérdida por rechazos", "SUM(venta_perdida) en fact_rechazos", money(data["rejects_total_loss"])],
    ]
    add_table(
        doc,
        8,
        "Indicadores consolidados del universo válido",
        ["Indicador", "Expresión", "Resultado"],
        kpi_result_rows,
        widths=[1.5, 2.2, 2.8],
        note="Elaboración propia a partir de la consulta de control sobre FactVentas en 03_dw/dw.db y de 06_calidad/log_rechazos.csv. Cifras en USD y unidades.",
        align_left_cols=(0, 1),
    )
    body_p(
        doc,
        f"El ticket promedio se calculó como ingresos netos divididos para transacciones, no para líneas. Si se "
        f"dividiera para las 6.800 líneas, el resultado sería {money(k['ingresos']/k['lineas'])} USD y estaría "
        "subestimado, porque una transacción con varios productos aporta varias líneas. Esta distinción es "
        "metodológica y debe explicarse en la mesa de decisiones para evitar comparaciones incorrectas.",
    )

    heading(doc, "Evolución mensual de ventas", 2)
    body_p(
        doc,
        f"La Figura 4 muestra la serie mensual de venta neta para los {months_count} meses analizados. El promedio "
        f"mensual es {money(months['venta_neta'].mean())} USD y el máximo se registra en enero de 2026, con "
        f"{money(months['venta_neta'].max())} USD. Se observan caídas en septiembre de 2024 y septiembre de 2025, "
        "seguidas de recuperación en los meses posteriores; ese patrón sugiere estacionalidad y justifica un "
        "análisis específico por campaña y por categoría.",
    )
    add_figure(
        doc,
        4,
        "Evolución mensual de las ventas netas",
        ASSETS / "fig_evolucion.png",
        width=6.4,
        note="Elaboración propia a partir de la vista v_ventas_mes en 03_dw/dw.db. La línea punteada representa el promedio mensual.",
    )
    body_p(
        doc,
        "La serie no debe interpretarse como una proyección. Es una descripción del universo válido y su cobertura "
        "es alta, pero no incorpora carga incremental ni corrige los rechazos. Para proyectar, sería necesario "
        "modelar la estacionalidad, controlar la tasa de rechazo y validar la cobertura de fechas en cada periodo.",
    )

    heading(doc, "Ventas por categoría", 2)
    body_p(
        doc,
        f"La categoría Accesorios lidera con {money(top_cat['venta_neta'])} USD, equivalentes al "
        f"{pct(top_cat['pct_participacion'])} de los ingresos. Le siguen Hogar, con {money(cat.iloc[1]['venta_neta'])} "
        f"USD ({pct(cat.iloc[1]['pct_participacion'])}), y Tecnología, con {money(cat.iloc[2]['venta_neta'])} USD "
        f"({pct(cat.iloc[2]['pct_participacion'])}). Accesorios y Hogar concentran el 40,39 % de las ventas, lo que "
        "sugiere priorizar inventario y campañas en esas categorías antes que en las de menor participación.",
    )
    cat_rows = []
    for _, row in cat.iterrows():
        cat_rows.append(
            [
                row["categoria"],
                money(row["venta_neta"]),
                pct(row["pct_participacion"]),
                money(row["margen"]),
            ]
        )
    add_table(
        doc,
        9,
        "Ventas por categoría y margen bruto",
        ["Categoría", "Venta neta (USD)", "Participación", "Margen bruto (USD)"],
        cat_rows,
        widths=[1.6, 1.7, 1.2, 1.8],
        note="Elaboración propia a partir de v_ventas_categoria y del cruce con DimProducto en 03_dw/dw.db.",
        align_left_cols=(0,),
    )
    add_figure(
        doc,
        5,
        "Participación de las categorías en las ventas netas",
        ASSETS / "fig_categoria.png",
        width=6.4,
        note="Elaboración propia a partir de v_ventas_categoria. Los porcentajes se calculan sobre los ingresos netos totales.",
    )
    body_p(
        doc,
        "El margen bruto por categoría no sigue exactamente el orden de las ventas. Hogar aporta "
        f"{money(cat.loc[cat['categoria']=='Hogar','margen'].iloc[0])} USD de margen, ligeramente por encima de "
        f"Accesorios ({money(cat.loc[cat['categoria']=='Accesorios','margen'].iloc[0])} USD), aunque Accesorios "
        "vende más. Esa diferencia muestra por qué conviene analizar ingresos y margen en conjunto: una categoría "
        "puede liderar ventas y no ser la más rentable.",
    )

    heading(doc, "Desempeño por sucursal", 2)
    body_p(
        doc,
        f"La sucursal con mayor venta neta es {top_branch['nombre_sucursal']}, con {money(top_branch['venta_neta'])} "
        f"USD ({pct(top_branch['venta_neta']/total*100)}). Le siguen Guayaquil Norte y Loja. La diferencia entre la "
        "primera y la última sucursal es de aproximadamente 132.851 USD, lo que refleja una distribución relativamente "
        "homogénea, aunque con oportunidades de mejora en las sucursales de menor volumen. La región Sierra concentra "
        f"{pct(region.iloc[0]['venta_neta']/total*100)} de los ingresos y la Costa el {pct(region.iloc[1]['venta_neta']/total*100)}.",
    )
    branch_rows = []
    for _, row in branch.iterrows():
        branch_rows.append(
            [
                row["nombre_sucursal"],
                row["region"],
                money(row["venta_neta"]),
                pct(row["venta_neta"]/total*100),
                integer(row["num_ventas"]),
                money(row["ticket_promedio"]),
            ]
        )
    add_table(
        doc,
        10,
        "Desempeño por sucursal",
        ["Sucursal", "Región", "Venta neta (USD)", "Participación", "Transacciones", "Ticket promedio (USD)"],
        branch_rows,
        widths=[1.35, 0.7, 1.3, 0.9, 1.05, 1.2],
        note="Elaboración propia a partir de v_ventas_sucursal. El ticket promedio se calcula por transacción.",
        align_left_cols=(0, 1),
    )
    add_figure(
        doc,
        6,
        "Desempeño de las sucursales por región",
        ASSETS / "fig_sucursal.png",
        width=6.4,
        note="Elaboración propia a partir de v_ventas_sucursal. Azul: Sierra; rojo: Costa.",
    )
    body_p(
        doc,
        "El ticket promedio más alto corresponde a Ambato (2.360,68 USD), seguido de Guayaquil Norte (2.335,66 USD) "
        "y Santo Domingo (2.250,55 USD). Guayaquil Centro, en cambio, tiene el mayor volumen pero un ticket de "
        "2.055,89 USD. Esa combinación sugiere que el volumen no siempre acompaña al ticket y que las acciones "
        "comerciales deben diferenciarse: en las sucursales de mayor ticket conviene proteger la venta cruzada; en "
        "las de mayor volumen, aumentar el valor promedio por operación.",
    )

    heading(doc, "Ventas por segmento", 2)
    body_p(
        doc,
        f"El segmento Masivo concentra {money(top_seg['venta_neta'])} USD, equivalentes al "
        f"{pct(top_seg['venta_neta']/total*100)} de los ingresos, con {integer(top_seg['num_ventas'])} transacciones. "
        f"Le sigue Frecuente, con {money(seg.iloc[1]['venta_neta'])} USD ({pct(seg.iloc[1]['venta_neta']/total*100)}), "
        f"y Premium, con {money(seg.iloc[2]['venta_neta'])} USD ({pct(seg.iloc[2]['venta_neta']/total*100)}). El "
        "segmento Corporativo aporta 4,96 % y el grupo Sin segmento 1,14 %, lo que evidencia el efecto de los nulos "
        "homologados.",
    )
    seg_rows = []
    for _, row in seg.iterrows():
        seg_rows.append(
            [
                row["segmento"],
                money(row["venta_neta"]),
                pct(row["venta_neta"]/total*100),
                integer(row["num_ventas"]),
                money(row["ticket_promedio"]),
            ]
        )
    add_table(
        doc,
        11,
        "Ventas por segmento de cliente",
        ["Segmento", "Venta neta (USD)", "Participación", "Transacciones", "Ticket promedio (USD)"],
        seg_rows,
        widths=[1.4, 1.5, 1.1, 1.1, 1.5],
        note="Elaboración propia a partir de v_ventas_segmento. El segmento Sin segmento agrupa los valores nulos homologados.",
        align_left_cols=(0,),
    )
    add_figure(
        doc,
        7,
        "Participación de los segmentos de cliente",
        ASSETS / "fig_segmento.png",
        width=6.4,
        note="Elaboración propia a partir de v_ventas_segmento. Los porcentajes se calculan sobre los ingresos netos totales.",
    )
    body_p(
        doc,
        "El ticket promedio más alto se observa en el grupo Sin segmento (2.352,57 USD), seguido de Frecuente (2.137,63 USD). "
        "El segmento Masivo, aunque concentra el volumen, tiene un ticket de 2.052,68 USD. Esto sugiere que las "
        "campañas de fidelización en Frecuente podrían aumentar la recurrencia sin sacrificar valor por operación, "
        "mientras que en Masivo el foco debería estar en el volumen y en la venta cruzada.",
    )

    heading(doc, "Canales y métodos de pago", 2)
    body_p(
        doc,
        "Los canales de venta están distribuidos de forma equilibrada: Marketplace, Web, Aplicación móvil y Tienda "
        "física aportan entre 24,31 % y 25,44 % cada uno. El canal No especificado representa apenas 0,21 %. En "
        "métodos de pago, Efectivo lidera con 21,11 %, seguido de Tarjeta de débito (20,38 %), Billetera digital "
        "(20,09 %), Tarjeta de crédito (19,31 %) y Transferencia (18,89 %). Esa distribución indica que la operación "
        "no depende de un único canal ni de un único medio de pago.",
    )
    channel_rows = []
    for _, row in chan.iterrows():
        channel_rows.append(["Canal", row["canal_venta"], money(row["venta_neta"]), pct(row["venta_neta"]/total*100)])
    for _, row in pay.iterrows():
        channel_rows.append(["Método de pago", row["metodo_pago"], money(row["venta_neta"]), pct(row["venta_neta"]/total*100)])
    table12 = add_table(
        doc,
        12,
        "Canales de venta y métodos de pago",
        ["Dimensión", "Categoría", "Venta neta (USD)", "Participación"],
        channel_rows,
        widths=[1.3, 2.2, 1.6, 1.4],
        note="Elaboración propia a partir de las vistas v_ventas_canal y de la consulta agrupada por metodo_pago en 03_dw/dw.db.",
        align_left_cols=(0, 1),
    )
    for row_index in range(2, 6):
        table12.cell(row_index, 0).text = ""
    for row_index in range(7, 12):
        table12.cell(row_index, 0).text = ""
    merged_channel = table12.cell(1, 0).merge(table12.cell(5, 0))
    merged_payment = table12.cell(6, 0).merge(table12.cell(11, 0))
    for merged, label in ((merged_channel, "Canal"), (merged_payment, "Método de pago")):
        merged.text = label
        for paragraph in merged.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.line_spacing = 1.0
            for run in paragraph.runs:
                set_run_font(run, "Arial", 8, bold=False)
        merged.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    body_p(
        doc,
        f"El producto con mayor venta neta es {top_product['nombre_producto']}, de la categoría "
        f"{top_product['categoria']}, con {money(top_product['venta_neta'])} USD. Le siguen dos productos de "
        "Accesorios, uno de Oficina y uno de Tecnología. La concentración en productos específicos refuerza la necesidad de analizar "
        "el surtido y el inventario, no solo la categoría agregada.",
    )

    heading(doc, "Evidencia del dashboard", 2)
    body_p(
        doc,
        "La Figura 8 representa la estructura del dashboard ejecutivo publicado en Apache Superset. La primera fila "
        "contiene ocho tarjetas de KPI; luego se ubican el mapa provincial y el pastel de participación por categoría; "
        "después, la evolución mensual y los cortes de categoría, sucursal, segmento, marca, descuento, región y canal. "
        "La sección final muestra los líderes por marca, categoría y sucursal, y las pérdidas por sucursal y fecha.",
    )
    body_p(
        doc,
        "El mapa funciona como filtro principal. Los polígonos representan provincias y los puntos rojos, sucursales. "
        "Al hacer clic en una provincia o en una sucursal, Superset emite un filtro cruzado y todos los gráficos se "
        "recalculan. Al seleccionar una categoría en el pastel, el mapa se filtra y colorea por la intensidad de venta "
        "de esa categoría, lo que permite identificar las sucursales donde se comercializa. La leyenda del mapa "
        "explica la escala de color y el borde regional: turquesa para la Costa, café para la Sierra y verde para la "
        "Amazonía. Los filtros nativos de provincia, categoría, sucursal, marca y región complementan la interacción.",
    )
    add_figure(
        doc,
        8,
        "Dashboard Sales Analytics generado desde el data warehouse",
        ASSETS / "fig_dashboard.png",
        width=6.4,
        note="Esquema del dashboard Sales Analytics en Apache Superset sobre PostgreSQL. La interactividad se verificó con los filtros cruzados y las consultas de control.",
    )

    heading(doc, "Indicadores complementarios de gestión", 2)
    body_p(
        doc,
        f"El descuento otorgado asciende a {money(k['descuento'])} USD y se concentra en Accesorios y Hogar. La "
        f"pérdida estimada por rechazos es {money(data['rejects_total_loss'])} USD sobre {len(rejects)} registros; "
        "la mayor pérdida se observa en Ambato, Santo Domingo y Manta. Estos indicadores permiten priorizar la "
        "revisión de descuentos por categoría y la corrección del origen de los registros rechazados, en lugar de "
        "tratarlos como una simple exclusión.",
    )
    add_figure(
        doc,
        9,
        "Marcas líderes por venta neta",
        ASSETS / "fig_marca.png",
        width=6.3,
        note="Elaboración propia a partir de v_ventas_detalle y DimProducto en 03_dw/dw.db. Puma lidera la venta neta.",
    )
    add_figure(
        doc,
        10,
        "Descuento otorgado por categoría",
        ASSETS / "fig_descuento_categoria.png",
        width=6.3,
        note="Elaboración propia a partir de FactVentas y DimProducto. El descuento se calcula como venta_bruta − venta_neta.",
    )
    add_figure(
        doc,
        11,
        "Pérdida estimada por rechazos según sucursal",
        ASSETS / "fig_rechazos_sucursal.png",
        width=6.3,
        note="Elaboración propia a partir de 06_calidad/log_rechazos.csv. La pérdida se estima como cantidad × precio × (1 − descuento).",
    )

    heading(doc, "Cumplimiento de objetivos", 2)
    body_p(
        doc,
        "La Tabla 13 relaciona cada objetivo específico con la evidencia producida y su estado. Todos los "
        "objetivos se cumplen dentro del alcance de la PoC. La evidencia incluye scripts, reportes de calidad, "
        "modelo estrella, vistas KPI, notebook, dashboard y guía de despliegue.",
    )
    objective_rows = [
        ["Integrar las cuatro fuentes", "Pipeline 02_etl/main.py y staging limpio", "Cumplido"],
        ["Aplicar reglas de calidad y documentar rechazos", "profile_report.md, quality_comparison.md y log_rechazos.csv", "Cumplido"],
        ["Construir el modelo estrella", "schema.sql, schema_sqlite.sql y dw.db", "Cumplido"],
        ["Calcular los indicadores comerciales", "Consulta de control y notebook 01_etl_pipeline.ipynb", "Cumplido"],
        ["Publicar dashboard interactivo", "Apache Superset y dashboard.html", "Cumplido"],
        ["Verificar consistencia y documentar limitaciones", "Auditoría de cifras y sección de discusión", "Cumplido"],
    ]
    add_table(
        doc,
        13,
        "Cumplimiento de los objetivos específicos",
        ["Objetivo", "Evidencia", "Estado"],
        objective_rows,
        widths=[2.3, 3.2, 1.0],
        note="Elaboración propia a partir de los entregables del repositorio.",
        align_left_cols=(0, 1),
    )

    heading(doc, "Auditoría de consistencia de cifras", 2)
    body_p(
        doc,
        "La auditoría comparó los totales del dashboard con la consulta de control sobre FactVentas. Los ingresos "
        f"netos coinciden en {money(k['ingresos'])} USD, las unidades en {integer(k['unidades'])}, el margen en "
        f"{money(k['margen'])} USD y las transacciones en {integer(k['transacciones'])}. También se verificó que la "
        "suma de las categorías, sucursales y segmentos coincida con el total, salvo diferencias de redondeo de "
        "centavos.",
    )
    body_p(
        doc,
        "Durante la auditoría se detectó una discrepancia menor en el reporte de comparación: una fila indicaba 21 "
        "fechas inválidas, mientras que el log y la verificación directa mostraban 20. La diferencia se explica "
        "porque el reporte contabilizó una fecha inválida que también estaba afectada por otro control y que, tras "
        "la depuración, quedó registrada una sola vez. Para el informe se adopta el valor verificable en el log y en "
        "la base final. Esta incidencia se documenta como una lección de calidad del propio reporte: los controles "
        "también deben auditarse.",
    )

    heading(doc, "Discusión de resultados", 1)
    heading(doc, "Interpretación comercial", 2)
    body_p(
        doc,
        f"El primer hallazgo es que la calidad cambia el universo analítico. De 6.870 líneas de venta, 70 no "
        f"llegaron al hecho, lo que representa el 1,02 % del total: 20 duplicados y 50 rechazos. Esa proporción puede parecer pequeña, pero "
        "su efecto no es neutro: las filas excluidas incluían ventas sin cliente, producto o sucursal, y fechas "
        "inválidas que habrían impedido agrupar correctamente la serie temporal. Al excluirlas, el dashboard deja de "
        "publicar ingresos que no pueden atribuirse a una dimensión válida.",
    )
    body_p(
        doc,
        "El segundo hallazgo es la concentración de las ventas. Accesorios y Hogar aportan el 40,39 % de los "
        "ingresos, mientras que el segmento Masivo concentra el 50,85 %. Esa estructura sugiere dos líneas de "
        "acción: proteger el surtido de las categorías líderes y diseñar campañas de recurrencia para el segmento "
        "Frecuente, que aporta 28,45 % y tiene un ticket promedio ligeramente superior al de Masivo. Las sucursales "
        "de la Sierra concentran el 57,99 % de los ingresos, pero la Costa muestra un desempeño cercano, lo que "
        "permite comparar prácticas comerciales entre regiones.",
    )
    body_p(
        doc,
        "El tercer hallazgo es la utilidad del margen como contrapeso a los ingresos. Hogar y Accesorios tienen "
        "márgenes brutos similares, aunque Accesorios vende más. Si la gerencia priorizara solo la participación en "
        "ventas, podría asignar recursos a una categoría con menor retorno relativo. El tablero, al incluir margen y "
        "ticket promedio, permite una lectura más equilibrada y evita decisiones basadas en un único indicador.",
    )
    body_p(
        doc,
        "Finalmente, la distribución de canales y métodos de pago es equilibrada. Ningún canal supera el 25,44 % ni "
        "ningún método supera el 21,11 %. Esa diversificación reduce la dependencia de un único punto de contacto, "
        "pero también exige monitorear la calidad de cada fuente: un error en un canal pequeño puede pasar "
        "desapercibido, mientras que un error en un canal grande afecta de inmediato los totales.",
    )

    heading(doc, "Contraste con la teoría", 2)
    body_p(
        doc,
        "Los resultados confirman lo planteado por Kimball y Ross (2013): un modelo dimensional bien definido "
        "simplifica las consultas y hace explícito el grano del negocio. En esta PoC, la diferencia entre línea y "
        "transacción fue decisiva para calcular correctamente el ticket promedio y el número de operaciones. Si el "
        "modelo hubiera mezclado ambos niveles, los indicadores habrían sido inconsistentes aunque las cifras "
        "parecieran razonables.",
    )
    body_p(
        doc,
        "La experiencia también coincide con Batini et al. (2009) y Pipino et al. (2002) en que la calidad debe "
        "medirse con dimensiones explícitas. La PoC no se limita a decir que los datos están limpios: cuantifica "
        "duplicados, nulos, rechazos y cobertura. Esa evidencia permite comparar el antes y el después, y sostener "
        "que el universo final es más confiable aunque sea más pequeño.",
    )
    body_p(
        doc,
        "El dashboard sigue los principios de Few (2006): prioriza pocos indicadores, evita el exceso de gráficos "
        "y ofrece filtros para explorar. La diferencia respecto de un reporte estático es que el usuario puede "
        "preguntar por sucursal, categoría o segmento sin solicitar una nueva extracción. La limitación es que la "
        "PoC no incluye alertas ni metas, que serían el siguiente nivel de madurez del tablero.",
    )

    heading(doc, "Limitaciones", 2)
    body_p(
        doc,
        "La primera limitación es el carácter académico y sintético de los datos. Aunque los volúmenes y problemas "
        "son realistas, no provienen de una operación comercial en producción. Por tanto, los hallazgos no deben "
        "generalizarse a una empresa específica sin una validación con datos reales. La segunda limitación es que la "
        "carga es batch y no incremental: el pipeline reconstruye el data warehouse en cada ejecución, lo que es "
        "adecuado para una PoC pero no para un volumen alto ni para datos que cambian durante el día.",
    )
    body_p(
        doc,
        "La tercera limitación es la ausencia de inferencia estadística y de modelos predictivos. El trabajo "
        "describe el universo válido y sugiere relaciones, pero no prueba causalidad ni proyecta ventas futuras. "
        "La cuarta es que el análisis de costos y rentabilidad se limita al margen bruto: no incluye gastos "
        "operativos, logísticos ni de marketing. La quinta es que el gobierno de datos es incipiente: no hay "
        "catálogo de datos, dueños de dominio ni acuerdos de nivel de servicio formales.",
    )
    body_p(
        doc,
        "También existe una limitación técnica: la versión HTML del dashboard es estática y no reemplaza la "
        "interactividad de Superset. Se incluyó como evidencia y como plan de contingencia, no como el producto "
        "final. En un entorno real, Superset debería ejecutarse con una base de metadatos persistente, respaldo y "
        "control de acceso por roles.",
    )

    heading(doc, "Validez y amenazas", 2)
    body_p(
        doc,
        "La validez interna se apoya en la reproducibilidad del pipeline y en la comparación de totales entre la "
        "fuente, el data warehouse y el dashboard. La validez de constructo se sostiene en la definición explícita "
        "de cada KPI y en el uso del grano de línea para las métricas. La validez externa es limitada por el "
        "carácter académico de los datos y por el periodo de 32 meses; los resultados describen ese caso, no una "
        "población de empresas.",
    )
    body_p(
        doc,
        "La principal amenaza a la conclusión es la tasa de rechazo. Si los registros excluidos se concentraran en "
        "una categoría o sucursal, las comparaciones podrían estar sesgadas. Para mitigarlo, el log permite "
        "desagregar los rechazos y monitorearlos. Otra amenaza es la calidad del propio reporte de comparación, como "
        "mostró la discrepancia de 21 frente a 20 fechas inválidas; por eso se recomienda auditar también los "
        "reportes de control y no solo los datos de origen.",
    )

    heading(doc, "Conclusiones", 1)
    body_p(
        doc,
        "La prueba de concepto demostró que es posible integrar cuatro fuentes comerciales heterogéneas y producir "
        "indicadores trazables con herramientas abiertas. El pipeline ETL documenta cada transformación, el modelo "
        "estrella separa hechos y dimensiones, y el dashboard presenta los resultados sobre el mismo universo "
        "validado.",
    )
    body_p(
        doc,
        "La calidad de datos no es un paso accesorio: modificó el universo de 6.870 a 6.800 líneas y evitó que "
        "ventas huérfanas o duplicadas distorsionaran los totales. La cobertura final de 98,98 % es alta, pero debe "
        "monitorearse porque una tasa de rechazo creciente reduciría la representatividad del análisis.",
    )
    body_p(
        doc,
        f"Los indicadores consolidados son consistentes: {money(k['ingresos'])} USD de ingresos netos, "
        f"{integer(k['unidades'])} unidades, {money(k['margen'])} USD de margen bruto y {integer(k['transacciones'])} "
        f"transacciones. El margen representa {pct(k['margen_pct'])} de los ingresos, un dato que debe leerse junto "
        "con la categoría y la sucursal, no de forma aislada.",
    )
    body_p(
        doc,
        "El dashboard permite identificar que Accesorios y Hogar concentran la mayor participación, que el segmento "
        "Masivo explica la mitad de los ingresos y que la Sierra aporta cerca del 58 % de las ventas. Esas lecturas "
        "son un punto de partida para decisiones de inventario, campañas y asignación comercial, no una respuesta "
        "definitiva.",
    )
    body_p(
        doc,
        "La principal contribución metodológica es haber convertido la calidad en evidencia cuantificable. El log de "
        "rechazos, la comparación antes/después y la auditoría de totales permiten defender cada cifra ante un "
        "tribunal o una mesa de decisiones. Esa trazabilidad es más valiosa que la cifra aislada.",
    )
    body_p(
        doc,
        "Como trabajo futuro se recomienda incorporar carga incremental, orquestación, pruebas automatizadas, "
        "catálogo de datos y metas por sucursal. Con esas mejoras, la PoC podría evolucionar hacia un producto de "
        "BI operativo sin perder la trazabilidad que la caracteriza.",
    )

    heading(doc, "Recomendaciones", 1)
    recomendaciones = [
        "Implementar carga incremental y un orquestador (por ejemplo, Airflow o un job programado) para evitar reconstruir todo el data warehouse en cada ejecución.",
        "Automatizar pruebas de calidad y de regresión sobre los totales, de modo que un cambio en el origen no pase inadvertido.",
        "Monitorear la tasa de rechazo por fuente, sucursal y categoría, y establecer un umbral de alerta cuando supere el nivel aceptado por el negocio.",
        "Documentar un catálogo de datos con definiciones de KPIs, dueños de dominio, granularidad y reglas de negocio.",
        "Incluir metas y presupuestos por sucursal para que el dashboard no solo describa, sino que también evalúe cumplimiento.",
        "Ampliar el análisis de rentabilidad con costos operativos y logísticos, porque el margen bruto no refleja la utilidad final.",
        "Reforzar la seguridad de Superset con roles, autenticación corporativa y respaldo de la base de metadatos.",
        "Validar la solución con datos reales anonimizados antes de generalizar los hallazgos a una organización específica.",
    ]
    for i, recomendacion in enumerate(recomendaciones, 1):
        body_p(doc, f"{i}. {recomendacion}", indent=False)

    heading(doc, "Referencias", 1)
    references = [
        ("Apache Software Foundation. (2026). ", "Apache Superset documentation", ". https://superset.apache.org/docs/intro"),
        ("Batini, C., Cappiello, C., Francalanci, C., & Maurino, A. (2009). Methodologies for data quality assessment and improvement. ", "ACM Computing Surveys, 41", "(3), 1–52. https://doi.org/10.1145/1541880.1541883"),
        ("Docker Inc. (2026). ", "Docker documentation", ". https://docs.docker.com/"),
        ("Few, S. (2006). ", "Information dashboard design: The effective visual communication of data", ". O'Reilly Media."),
        ("Hernández-Sampieri, R., & Mendoza, C. (2018). ", "Metodología de la investigación: Las rutas cuantitativa, cualitativa y mixta", ". McGraw-Hill."),
        ("ISO. (2016). ", "ISO 8000-61:2016 Data quality — Part 61: Data quality management: Process reference model", ". International Organization for Standardization. https://www.iso.org/standard/62383.html"),
        ("Kimball, R., & Ross, M. (2013). ", "The data warehouse toolkit: The definitive guide to dimensional modeling", " (3rd ed.). Wiley."),
        ("Northflank. (2026). ", "Northflank documentation", ". https://northflank.com/docs"),
        ("pandas Development Team. (2026). ", "pandas documentation", ". https://pandas.pydata.org/docs/"),
        ("Pipino, L. L., Lee, Y. W., & Wang, R. Y. (2002). Data quality assessment. ", "Communications of the ACM, 45", "(4), 211–218. https://doi.org/10.1145/505999.506010"),
        ("PostgreSQL Global Development Group. (2026). ", "PostgreSQL documentation", ". https://www.postgresql.org/docs/"),
        ("Provost, F., & Fawcett, T. (2013). ", "Data science for business: What you need to know about data mining and data-analytic thinking", ". O'Reilly Media."),
        ("Sharda, R., Delen, D., & Turban, E. (2020). ", "Analytics, data science, & artificial intelligence: Systems for decision support", " (11th ed.). Pearson."),
        ("Universidad Central del Ecuador. (2022). ", "Lineamientos para la publicación de trabajos de titulación de pregrado y posgrado con aplicación de la norma APA 7 en el repositorio institucional", ". UCE."),
        ("Universidad Central del Ecuador, Facultad de Ingeniería y Ciencias Aplicadas. (2026). ", "Guía metodológica del examen complexivo 2025-2026", ". UCE."),
        ("Wirth, R., & Hipp, J. (2000). CRISP-DM: Towards a standard process model for data mining. ", "Proceedings of the 4th International Conference on the Practical Application of Knowledge Discovery and Data Mining", ", 29–39."),
    ]
    for prefix, italic_text, suffix in references:
        add_reference(doc, prefix, italic_text, suffix)

    heading(doc, "Anexos", 1)
    heading(doc, "Anexo A. Esquema del modelo estrella", 2)
    body_p(
        doc,
        "El siguiente extracto corresponde al DDL PostgreSQL utilizado para crear el modelo estrella. El esquema "
        "SQLite mantiene la misma estructura y se usa como respaldo local para la evidencia.",
    )
    add_code(doc, (BASE / "03_dw" / "schema.sql").read_text(encoding="utf-8"))

    heading(doc, "Anexo B. Vistas KPI", 2)
    body_p(
        doc,
        "Las vistas KPI encapsulan los agregados que consume Apache Superset. Se recrean en cada carga para "
        "garantizar que el dashboard y la evidencia utilicen el mismo universo validado.",
    )
    add_code(doc, (BASE / "04_dashboard" / "kpi_views_postgres.sql").read_text(encoding="utf-8"))

    heading(doc, "Anexo C. Evidencia de rechazos", 2)
    body_p(
        doc,
        f"El archivo log_rechazos.csv contiene {len(rejects)} registros. A continuación se presenta una muestra "
        "de las primeras filas; el archivo completo se conserva en 06_calidad/.",
    )
    sample = rejects.head(10).to_csv(index=False, encoding="utf-8-sig")
    add_code(doc, sample)

    heading(doc, "Anexo D. Reproducibilidad", 2)
    body_p(
        doc,
        f"Los comandos siguientes permiten regenerar la evidencia y el dashboard desde la raíz del repositorio "
        f"({REPO_URL}). El ETL utiliza SQLite en local y PostgreSQL o Neon cuando ETL_TARGET=postgres.",
    )
    add_code(
        doc,
        """
python 02_etl/main.py
python 04_dashboard/build_dashboard.py

docker compose -f docker/docker-compose.yml up --build
docker compose -f docker/docker-compose.superset.yml up -d --build
docker compose -f docker/docker-compose.superset.yml run --rm etl

# Archivos de evidencia
06_calidad/profile_report.md
06_calidad/quality_comparison.md
06_calidad/reglas_transformacion.md
06_calidad/log_rechazos.csv
03_dw/dw.db
02_etl/01_etl_pipeline.ipynb
""".strip()
    )
    body_p(
        doc,
        "La estructura del repositorio separa datos, ETL, data warehouse, dashboard, calidad y presentación. Esa "
        "separación facilita la revisión por parte de terceros y permite reemplazar una capa sin afectar las demás. "
        "El informe y sus figuras se generan con 07_presentacion/build_informe.py, que consulta la base y los "
        "reportes de calidad para mantener las cifras sincronizadas.",
    )

    doc.add_page_break()
    heading(doc, "Anexo E. Evidencias del proceso ETL y del dashboard en la nube", 2)
    body_p(
        doc,
        "Las siguientes capturas documentan la ejecución del pipeline, la calidad de los datos, la carga en Neon "
        "y la publicación del dashboard en Apache Superset. Se añaden tres evidencias específicas de los cambios: el "
        "modelo con FactRechazos y las vistas nuevas, el dashboard ejecutivo con mapa-filtro y leyenda, y la gestión "
        "de pérdidas por rechazos y descuentos por categoría. Se incluyen como evidencia de trazabilidad del "
        "proyecto y conservan la numeración consecutiva de las figuras del informe.",
    )
    evidence = [
        (
            12,
            "Notebook de Jupyter con la ejecución del pipeline ETL",
            "jupiterNotebook.png",
            "Captura de la ejecución de 02_etl/01_etl_pipeline.ipynb en Jupyter.",
        ),
        (
            13,
            "Datos procesados en la etapa de staging",
            "datosProcesados.png",
            "Captura de 01_datos/staging/clean_clientes.csv generado por el ETL.",
        ),
        (
            14,
            "Tablas originales y transformadas cargadas en Neon",
            "baseDatos.png",
            "Captura de la consola de Neon con las tablas stg_*, clean_*, dim_* y fact_ventas.",
        ),
        (
            15,
            "Comparación de calidad antes y después del ETL",
            "comparacion.png",
            "Captura de 06_calidad/quality_comparison.csv.",
        ),
        (
            16,
            "Reglas de transformación y justificación",
            "reglas.png",
            "Captura de 06_calidad/reglas_transformacion.md.",
        ),
        (
            17,
            "Dashboard Sales Analytics en Apache Superset",
            "sales-analytics-2026-10-26T19-28-35.152Z.jpg",
            "Captura del dashboard publicado en Apache Superset con datos de Neon.",
        ),
        (
            18,
            "Modelo analítico actualizado con FactRechazos y vistas nuevas",
            "modelo_actual.png",
            "Esquema propio a partir de 03_dw/schema.sql y 04_dashboard/kpi_views_postgres.sql. Incluye FactRechazos y las vistas v_ventas_detalle, v_mapa_consolidado y v_rechazos.",
        ),
        (
            19,
            "Dashboard ejecutivo actualizado: KPIs, mapa-filtro y leyenda",
            "dashboard_actual.png",
            "Evidencia del dashboard Sales Analytics en Apache Superset. Resume los ocho KPIs, el mapa-filtro y la leyenda de color y región.",
        ),
        (
            20,
            "Pérdidas por rechazos y descuentos por categoría",
            "rechazos_descuento.png",
            "Evidencia de gestión: pérdida estimada por sucursal y descuento otorgado por categoría, ambos filtrables desde el dashboard.",
        ),
    ]
    for number, title, filename, note in evidence:
        add_figure(
            doc,
            number,
            title,
            BASE / "evidencias" / filename,
            width=6.3,
            note=f"{note} Elaboración propia.",
        )


def to_roman(number: int) -> str:
    values = [
        (1000, "m"), (900, "cm"), (500, "d"), (400, "cd"),
        (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
        (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i"),
    ]
    result = []
    for value, symbol in values:
        while number >= value:
            result.append(symbol)
            number -= value
    return "".join(result)


def build_docx(data: dict, portada: dict, page_map: dict) -> None:
    doc = Document()
    build_prelim(doc, portada, data, page_map)
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    setup_section(section)
    set_page_number_format(section, "decimal", 1)
    add_header_page_number(section)
    build_body(doc, data)
    doc.save(DOCX_PATH)


def convert_pdf() -> None:
    if PDF_PATH.exists():
        PDF_PATH.unlink()
    profile_dir = Path(f"/tmp/lo_profile_informe_{os.getpid()}")
    if profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    profile = f"file://{profile_dir}"
    library_dir = Path("/tmp/lo_libs")
    library_dir.mkdir(parents=True, exist_ok=True)
    boost_target = library_dir / "libboost_locale.so.1.92.0"
    boost_source = Path("/usr/lib/libboost_locale.so.1.91.0")
    if boost_source.exists():
        if boost_target.is_symlink() or boost_target.exists():
            boost_target.unlink()
        boost_target.symlink_to(boost_source)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"{library_dir}:{env.get('LD_LIBRARY_PATH', '')}"
    try:
        subprocess.run(
            [
                "soffice",
                "--headless",
                f"-env:UserInstallation={profile}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(OUT),
                str(DOCX_PATH),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=240,
            env=env,
        )
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)
    if not PDF_PATH.exists():
        raise RuntimeError("LibreOffice no generó el PDF esperado")


def pdf_pages(pdf_path: Path) -> list[str]:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    text = result.stdout.decode("utf-8", errors="replace")
    return text.split("\f")


def find_line(pages: list[str], text: str, start: int = 0):
    target = norm(text)
    for index in range(max(0, start), len(pages)):
        for line in pages[index].splitlines():
            if norm(line) == target:
                return index
    return None


def find_prefix(pages: list[str], prefix: str, start: int = 0):
    target = norm(prefix)
    for index in range(max(0, start), len(pages)):
        for line in pages[index].splitlines():
            value = norm(line)
            if value == target or value.startswith(target + ".") or value.startswith(target + " "):
                return index
    return None


def extract_page_map(pdf_path: Path) -> dict:
    pages = pdf_pages(pdf_path)
    page_map = {}
    start = 0
    toc_page = None
    for label, key in PRELIM_TOC:
        if label == "Lista de tablas" and toc_page is not None:
            start = toc_page + 1
        index = find_line(pages, label, start)
        if index is not None:
            page_map[key] = to_roman(index + 1)
            start = index + 1
            if label == "Tabla de contenidos":
                toc_page = index

    abstract_page = find_line(pages, "Abstract", 0)
    body_start = find_line(pages, "Introducción", (abstract_page or 0) + 1)
    if body_start is None:
        body_start = 0

    current = body_start
    for level, text in HEADINGS:
        index = find_line(pages, text, current)
        if index is not None:
            page_map[f"h:{text}"] = str(index - body_start + 1)
            current = index

    for number, _ in TABLES:
        index = find_prefix(pages, f"Tabla {number}", body_start)
        if index is not None:
            page_map[f"table:{number}"] = str(index - body_start + 1)

    for number, _ in FIGURES:
        index = find_prefix(pages, f"Figura {number}", body_start)
        if index is not None:
            page_map[f"figure:{number}"] = str(index - body_start + 1)

    for letter, _ in ANNEXES:
        index = find_prefix(pages, f"Anexo {letter}", body_start)
        if index is not None:
            page_map[f"annex:{letter}"] = str(index - body_start + 1)

    return page_map


def main() -> None:
    portada = json.loads((OUT / "datos_portada.json").read_text(encoding="utf-8"))
    data = load_data()
    generate_assets(data)

    page_map = {}
    stable = False
    for _ in range(5):
        build_docx(data, portada, page_map)
        convert_pdf()
        new_map = extract_page_map(PDF_PATH)
        if new_map == page_map:
            stable = True
            break
        page_map = new_map

    if not stable:
        build_docx(data, portada, page_map)
        convert_pdf()

    pages = pdf_pages(PDF_PATH)
    print(f"DOCX: {DOCX_PATH}")
    print(f"PDF:  {PDF_PATH}")
    print(f"Páginas: {len([p for p in pages if p.strip()])}")
    print(f"Entradas de índice resueltas: {len(page_map)}")


if __name__ == "__main__":
    main()
