#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades compartidas para reconstruir las presentaciones UCE."""

from __future__ import annotations

import sqlite3
import zipfile
from pathlib import Path

import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
TEMPLATE = BASE / "PlantillaoficialUCE.pptx"
ASSETS = BASE / "assets"
DB = ROOT / "03_dw" / "dw.db"

NAVY = RGBColor(0x10, 0x3F, 0x77)
NAVY_D = RGBColor(0x0B, 0x2E, 0x5A)
RED = RGBColor(0xAB, 0x19, 0x26)
BLUE = RGBColor(0x2B, 0x6C, 0xB0)
BLUE_L = RGBColor(0x5B, 0x9B, 0xD5)
TEXT = RGBColor(0x26, 0x2E, 0x3B)
GRAY = RGBColor(0x5A, 0x64, 0x72)
GRAY_L = RGBColor(0x8A, 0x94, 0xA6)
LIGHT = RGBColor(0xF3, 0xF6, 0xFB)
LIGHT2 = RGBColor(0xE8, 0xEE, 0xF8)
BORDER = RGBColor(0xDD, 0xE4, 0xEF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x2E, 0x7D, 0x32)

TITLE_FONT = "Calibri Light"
BODY_FONT = "Calibri"

FULL_TITLE = (
    "Integración y calidad de datos para el análisis comercial: "
    "prueba de concepto con ETL, data warehouse y dashboard en Apache Superset"
)
AUTHOR = "David Sebastián Malquin Pozo"
TUTOR = "Kevin Segundo Atudillo Quimbiulco"
EMAIL = "dsmalquin@uce.edu.ec"
REPO = "github.com/DavCoder22/Proyecto34"
CAREER = "Carrera de Sistemas de Información"
FACULTY = "Facultad de Ingeniería y Ciencias Aplicadas"
FOOTER_TEXT = "Integración y calidad de datos · Examen Complexivo UCE"


def _font(run, size, color, bold=False, italic=False, font=BODY_FONT):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def add_text(
    slide,
    x,
    y,
    w,
    h,
    text,
    size=16,
    color=TEXT,
    bold=False,
    font=BODY_FONT,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    line_spacing=1.0,
    space_after=0,
    margin=0.02,
    italic=False,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = anchor
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line
        _font(r, size, color, bold, italic, font)
    return box



def _strip_style(shape):
    sp = shape._element
    style = sp.find(qn("p:style"))
    if style is not None:
        sp.remove(style)


def add_rect(slide, x, y, w, h, fill=LIGHT, line=None, radius=0.06, line_w=1.0):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    try:
        shape.adjustments[0] = radius
    except (IndexError, ValueError):
        pass
    if fill is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(line_w)
    shape.shadow.inherit = False
    _strip_style(shape)
    return shape


def add_plain_rect(slide, x, y, w, h, fill, line=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    shape.shadow.inherit = False
    _strip_style(shape)
    return shape


def add_badge(slide, x, y, d, label, fill=NAVY, color=WHITE, size=12, bold=True):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    shape.shadow.inherit = False
    _strip_style(shape)
    tf = shape.text_frame
    tf.word_wrap = False
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(label)
    _font(r, size, color, bold)
    return shape


def add_connector(slide, x1, y1, x2, y2, color=BLUE_L, width=1.5):
    conn = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    return conn


def add_oval_outline(slide, x, y, w, h, color=BORDER, width=2.0):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.background()
    shape.line.color.rgb = color
    shape.line.width = Pt(width)
    shape.shadow.inherit = False
    _strip_style(shape)
    return shape


def add_picture_fit(slide, path, x, y, w, h):
    iw, ih = Image.open(path).size
    ratio = min(w / iw, h / ih)
    nw, nh = iw * ratio, ih * ratio
    nx, ny = x + (w - nw) / 2, y + (h - nh) / 2
    slide.shapes.add_picture(str(path), Inches(nx), Inches(ny), Inches(nw), Inches(nh))


def add_bullets(
    slide,
    x,
    y,
    w,
    h,
    items,
    size=13,
    color=TEXT,
    bullet_color=BLUE,
    space_after=6,
    line_spacing=1.0,
    bullet="•",
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = bullet + "  "
        _font(r, size, bullet_color, True)
        if isinstance(item, tuple):
            lead, rest = item
            r1 = p.add_run()
            r1.text = lead
            _font(r1, size, color, True)
            r2 = p.add_run()
            r2.text = rest
            _font(r2, size, color)
        else:
            r2 = p.add_run()
            r2.text = item
            _font(r2, size, color)
    return box


def _layouts(prs):
    by_name = {layout.name: layout for layout in prs.slide_layouts}
    return (
        by_name["Diapositiva de título"],
        by_name["Solo el título"],
        by_name["Encabezado de sección"],
    )


def _strip_slides(prs):
    sld_id_lst = prs.slides._sldIdLst
    for sld_id in list(sld_id_lst):
        r_id = sld_id.get(qn("r:id"))
        prs.part.drop_rel(r_id)
        sld_id_lst.remove(sld_id)


def _clear_placeholders(slide):
    for ph in list(slide.placeholders):
        ph._element.getparent().remove(ph._element)


def _footer(slide, number):
    add_text(slide, 0.92, 7.0, 8.6, 0.2, FOOTER_TEXT, size=8, color=GRAY_L)
    add_text(
        slide,
        11.55,
        7.0,
        0.82,
        0.2,
        str(number),
        size=8,
        color=GRAY_L,
        align=PP_ALIGN.RIGHT,
    )


def content_slide(prs, layout, title, number):
    slide = prs.slides.add_slide(layout)
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx != 0:
            ph._element.getparent().remove(ph._element)
    title_ph = slide.shapes.title
    title_ph.left = Inches(0.9)
    title_ph.top = Inches(0.68)
    title_ph.width = Inches(11.55)
    title_ph.height = Inches(0.62)
    tf = title_ph.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    p.line_spacing = 0.95
    r = p.add_run()
    r.text = title
    _font(r, 27, NAVY, True, font=TITLE_FONT)
    add_plain_rect(slide, 0.95, 1.32, 0.95, 0.05, RED)
    _footer(slide, number)
    return slide


def section_slide(prs, layout, number, title, subtitle):
    slide = prs.slides.add_slide(layout)
    _clear_placeholders(slide)
    add_oval_outline(slide, 9.2, 1.05, 3.95, 3.95, LIGHT2, 2.4)
    add_oval_outline(slide, 10.15, 2.0, 2.05, 2.05, BORDER, 1.4)
    add_text(
        slide,
        0.82,
        0.78,
        2.6,
        1.55,
        number,
        size=96,
        color=LIGHT2,
        bold=True,
        font=TITLE_FONT,
    )
    add_text(
        slide,
        0.95,
        2.34,
        3.0,
        0.28,
        "SECCIÓN " + number,
        size=10,
        color=GRAY_L,
        bold=True,
    )
    add_plain_rect(slide, 0.97, 2.68, 1.15, 0.06, RED)
    add_text(
        slide,
        0.9,
        2.82,
        11.4,
        0.8,
        title,
        size=34,
        color=NAVY,
        bold=True,
        font=TITLE_FONT,
    )
    add_text(slide, 0.9, 3.66, 10.8, 0.85, subtitle, size=15, color=GRAY)
    return slide


def cover_slide(prs, layout, title_bg):
    slide = prs.slides.add_slide(layout)
    _clear_placeholders(slide)
    slide.shapes.add_picture(
        str(title_bg), 0, 0, width=prs.slide_width, height=prs.slide_height
    )
    x = 7.32
    add_text(
        slide,
        x,
        0.92,
        5.4,
        0.26,
        "UNIVERSIDAD CENTRAL DEL ECUADOR",
        size=10.5,
        color=WHITE,
        bold=True,
    )
    add_text(slide, x, 1.17, 5.4, 0.24, FACULTY.upper(), size=8.5, color=LIGHT2)
    add_plain_rect(slide, x + 0.03, 1.55, 0.95, 0.06, RED)
    add_text(
        slide,
        x,
        1.72,
        5.38,
        2.25,
        FULL_TITLE,
        size=25,
        color=WHITE,
        bold=True,
        line_spacing=0.98,
    )
    add_text(slide, x, 4.02, 5.38, 0.22, "AUTOR", size=8.5, color=LIGHT2, bold=True)
    add_text(slide, x, 4.24, 5.38, 0.3, AUTHOR, size=14, color=WHITE, bold=True)
    add_text(slide, x, 4.62, 5.38, 0.22, "TUTOR", size=8.5, color=LIGHT2, bold=True)
    add_text(slide, x, 4.84, 5.38, 0.3, TUTOR, size=12, color=WHITE)
    add_text(slide, x, 5.2, 5.38, 0.28, CAREER, size=10.5, color=LIGHT2)
    add_text(
        slide,
        x,
        5.48,
        5.38,
        0.48,
        "Trabajo de Titulación · Examen Complexivo",
        size=10.5,
        color=LIGHT2,
    )
    add_text(slide, x, 5.96, 5.38, 0.3, "Quito, 6 de noviembre de 2026", size=10.5, color=WHITE, bold=True)
    return slide


def closing_slide(prs, layout, title_bg):
    slide = prs.slides.add_slide(layout)
    _clear_placeholders(slide)
    slide.shapes.add_picture(
        str(title_bg), 0, 0, width=prs.slide_width, height=prs.slide_height
    )
    x = 7.32
    add_text(slide, x, 1.55, 5.4, 0.3, "EXAMEN COMPLEXIVO", size=10, color=LIGHT2, bold=True)
    add_text(
        slide,
        x,
        1.9,
        5.4,
        0.9,
        "Gracias",
        size=46,
        color=WHITE,
        bold=True,
        font=TITLE_FONT,
    )
    add_text(
        slide,
        x,
        2.95,
        5.4,
        0.55,
        "¿Preguntas?",
        size=24,
        color=LIGHT2,
        font=TITLE_FONT,
    )
    add_plain_rect(slide, x + 0.03, 3.72, 0.95, 0.06, RED)
    add_text(slide, x, 4.05, 5.4, 0.22, "AUTOR", size=8.5, color=LIGHT2, bold=True)
    add_text(slide, x, 4.27, 5.4, 0.3, AUTHOR, size=14, color=WHITE, bold=True)
    add_text(slide, x, 4.66, 5.4, 0.28, EMAIL, size=11.5, color=LIGHT2)
    add_text(slide, x, 5.12, 5.4, 0.22, "REPOSITORIO", size=8.5, color=LIGHT2, bold=True)
    add_text(slide, x, 5.34, 5.4, 0.28, REPO, size=11, color=WHITE)
    add_text(slide, x, 5.95, 5.4, 0.3, "Viernes, 6 de noviembre de 2026", size=10.5, color=LIGHT2)
    return slide


def kpi_tile(slide, x, y, w, h, label, value, detail, accent=NAVY, value_size=29):
    add_rect(slide, x, y, w, h, WHITE, line=BORDER, radius=0.07)
    add_plain_rect(slide, x, y, w, 0.06, accent)
    add_text(
        slide,
        x + 0.2,
        y + 0.17,
        w - 0.34,
        0.22,
        label.upper(),
        size=9,
        color=GRAY,
        bold=True,
    )
    add_text(
        slide,
        x + 0.2,
        y + 0.43,
        w - 0.34,
        0.55,
        value,
        size=value_size,
        color=NAVY,
        bold=True,
        font=TITLE_FONT,
    )
    add_text(
        slide,
        x + 0.2,
        y + h - 0.36,
        w - 0.34,
        0.28,
        detail,
        size=9.5,
        color=GRAY,
    )


def info_card(
    slide,
    x,
    y,
    w,
    h,
    title,
    body,
    badge=None,
    accent=NAVY,
    title_size=13,
    body_size=10.5,
):
    add_rect(slide, x, y, w, h, LIGHT, line=BORDER, radius=0.07)
    add_plain_rect(slide, x, y, 0.07, h, accent)
    tx = x + 0.2
    if badge is not None:
        add_badge(slide, x + 0.18, y + 0.15, 0.38, badge, fill=accent, size=11)
        tx = x + 0.66
    add_text(
        slide,
        tx,
        y + 0.13,
        w - (tx - x) - 0.14,
        0.3,
        title,
        size=title_size,
        color=NAVY,
        bold=True,
    )
    add_text(
        slide,
        tx,
        y + 0.46,
        w - (tx - x) - 0.14,
        h - 0.52,
        body,
        size=body_size,
        color=TEXT,
    )


def chip(slide, x, y, w, text, fill=LIGHT2, color=NAVY, size=9.5, h=0.34, bold=True):
    add_rect(slide, x, y, w, h, fill, line=None, radius=0.5)
    add_text(
        slide,
        x,
        y + 0.02,
        w,
        h - 0.02,
        text,
        size=size,
        color=color,
        bold=bold,
        align=PP_ALIGN.CENTER,
        anchor=MSO_ANCHOR.MIDDLE,
    )


def add_table(slide, x, y, w, data, col_widths, row_h=0.42, font_size=10, header_size=10):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(
        rows, cols, Inches(x), Inches(y), Inches(w), Inches(row_h * rows)
    )
    table = shape.table
    table.first_row = True
    table.horz_banding = False
    for i, cw in enumerate(col_widths):
        table.columns[i].width = Inches(cw)
    for r in range(rows):
        table.rows[r].height = Inches(row_h)
        for c in range(cols):
            cell = table.cell(r, c)
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if r == 0 else (WHITE if r % 2 else LIGHT)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            run = p.add_run()
            run.text = str(data[r][c])
            _font(
                run,
                header_size if r == 0 else font_size,
                WHITE if r == 0 else TEXT,
                bold=(r == 0),
            )
    return shape


def load_data():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    def rows(sql):
        return [dict(r) for r in cur.execute(sql)]

    data = {}
    data["kpi"] = rows(
        "SELECT round(sum(venta_neta),2) ing, sum(cantidad) uni, "
        "round(sum(margen),2) mar, round(sum(venta_bruta - venta_neta),2) desc, "
        "count(distinct id_venta) tx, count(*) lineas "
        'FROM "FactVentas"'
    )[0]
    data["mes"] = rows(
        "SELECT t.anio, t.mes, t.mes_nombre, round(sum(f.venta_neta),2) ing "
        'FROM "FactVentas" f JOIN "DimTiempo" t ON t.id_tiempo=f.id_tiempo '
        "GROUP BY t.anio,t.mes ORDER BY t.anio,t.mes"
    )
    data["anio"] = rows(
        "SELECT t.anio, round(sum(f.venta_neta),2) ing, round(sum(f.margen),2) mar, "
        "sum(f.cantidad) uni, count(distinct f.id_venta) tx "
        'FROM "FactVentas" f JOIN "DimTiempo" t ON t.id_tiempo=f.id_tiempo '
        "GROUP BY t.anio ORDER BY t.anio"
    )
    data["cat"] = rows(
        "SELECT p.categoria, round(sum(f.venta_neta),2) ing, round(sum(f.margen),2) mar, "
        'sum(f.cantidad) uni FROM "FactVentas" f JOIN "DimProducto" p ON p.id_producto=f.id_producto '
        "GROUP BY p.categoria ORDER BY ing DESC"
    )
    data["seg"] = rows(
        "SELECT coalesce(nullif(trim(c.segmento),''),'Sin segmento') seg, "
        "round(sum(f.venta_neta),2) ing, round(sum(f.margen),2) mar, "
        'count(distinct f.id_venta) tx FROM "FactVentas" f JOIN "DimCliente" c ON c.id_cliente=f.id_cliente '
        "GROUP BY seg ORDER BY ing DESC"
    )
    data["suc"] = rows(
        "SELECT s.cod_sucursal, s.nombre_sucursal, s.region, round(sum(f.venta_neta),2) ing, "
        'count(distinct f.id_venta) tx FROM "FactVentas" f JOIN "DimSucursal" s ON s.id_sucursal=f.id_sucursal '
        "GROUP BY s.id_sucursal ORDER BY ing DESC"
    )
    data["region"] = rows(
        "SELECT s.region, round(sum(f.venta_neta),2) ing "
        'FROM "FactVentas" f JOIN "DimSucursal" s ON s.id_sucursal=f.id_sucursal '
        "GROUP BY s.region ORDER BY ing DESC"
    )
    data["marca"] = rows(
        "SELECT p.marca, round(sum(f.venta_neta),2) ing, sum(f.cantidad) uni, "
        "round(sum(f.venta_bruta - f.venta_neta),2) descuento "
        'FROM "FactVentas" f JOIN "DimProducto" p ON p.id_producto=f.id_producto '
        "WHERE p.marca IS NOT NULL AND trim(p.marca)<>'' "
        "GROUP BY p.marca ORDER BY ing DESC"
    )
    data["descuento"] = rows(
        "SELECT p.categoria, round(sum(f.venta_bruta - f.venta_neta),2) descuento, "
        "avg(f.descuento_pct) prom "
        'FROM "FactVentas" f JOIN "DimProducto" p ON p.id_producto=f.id_producto '
        "GROUP BY p.categoria ORDER BY descuento DESC"
    )
    data["canal"] = rows(
        'SELECT canal_venta, round(sum(venta_neta),2) ing FROM "FactVentas" '
        "GROUP BY canal_venta ORDER BY ing DESC"
    )
    data["pago"] = rows(
        'SELECT metodo_pago, round(sum(venta_neta),2) ing FROM "FactVentas" '
        "GROUP BY metodo_pago ORDER BY ing DESC"
    )
    data["prod"] = rows(
        "SELECT p.nombre_producto, p.categoria, round(sum(f.venta_neta),2) ing, sum(f.cantidad) uni "
        'FROM "FactVentas" f JOIN "DimProducto" p ON p.id_producto=f.id_producto '
        "GROUP BY p.id_producto ORDER BY ing DESC LIMIT 5"
    )
    con.close()

    rejects_path = ROOT / "06_calidad" / "log_rechazos.csv"
    data["rechazos_total"] = 0.0
    data["rechazos_suc"] = []
    if rejects_path.exists():
        rej = pd.read_csv(rejects_path, dtype=str, encoding="utf-8-sig")
        if not rej.empty:
            for col in ("cantidad", "precio_unitario", "descuento_pct"):
                rej[col] = pd.to_numeric(rej.get(col), errors="coerce").fillna(0)
            rej["descuento_pct"] = rej["descuento_pct"].where(
                rej["descuento_pct"] <= 1, rej["descuento_pct"] / 100
            )
            rej["venta_perdida"] = (
                rej["cantidad"] * rej["precio_unitario"] * (1 - rej["descuento_pct"])
            )
            codes = {
                row["cod_sucursal"]: row["nombre_sucursal"] for row in data["suc"]
            }
            rej["nombre_sucursal"] = rej["cod_sucursal"].map(codes)
            rej["nombre_sucursal"] = rej["nombre_sucursal"].fillna(rej["cod_sucursal"])
            data["rechazos_total"] = float(rej["venta_perdida"].sum())
            data["rechazos_suc"] = (
                rej.groupby("nombre_sucursal", as_index=False)
                .agg(n=("id_venta", "count"), perdida=("venta_perdida", "sum"))
                .sort_values("perdida", ascending=False)
                .to_dict("records")
            )
    return data


def _style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#C9D2E0")
    ax.spines["bottom"].set_color("#C9D2E0")
    ax.tick_params(colors="#5A6472", labelsize=10)
    ax.grid(True, color="#E6EBF3", linewidth=0.8, axis="x")
    ax.set_axisbelow(True)


def _es(value, decimals=0):
    s = f"{value:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _save(fig, name):
    path = ASSETS / name
    fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.06, facecolor="white")
    plt.close(fig)
    return path


def make_charts(data):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "axes.edgecolor": "#C9D2E0",
        }
    )
    navy = "#103F77"
    red = "#AB1926"
    blue = "#2B6CB0"
    blue_l = "#9DB8DA"
    gray = "#5A6472"
    path = {}

    meses = data["mes"]
    labels = [f"{m['anio']}-{m['mes']:02d}" for m in meses]
    vals = [m["ing"] for m in meses]
    avg = sum(vals) / len(vals)
    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    ax.plot(range(len(vals)), vals, color=navy, linewidth=2.4, marker="o", markersize=3.5, zorder=3)
    ax.fill_between(range(len(vals)), vals, avg, color=blue_l, alpha=0.22, zorder=1)
    ax.axhline(avg, color=red, linestyle="--", linewidth=1.2, zorder=2)
    ax.text(
        1.0,
        avg + (max(vals) - min(vals)) * 0.045,
        f"Promedio {_es(avg)}",
        color=red,
        fontsize=9,
        ha="left",
        va="bottom",
        bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
    )
    imax = max(range(len(vals)), key=lambda i: vals[i])
    ax.annotate(
        f"Máx. {_es(vals[imax])}",
        xy=(imax, vals[imax]),
        xytext=(imax - 4.2, vals[imax] + 12000),
        fontsize=9,
        color=navy,
        arrowprops=dict(arrowstyle="-", color=gray, linewidth=0.8),
    )
    ax.set_xticks(range(0, len(vals), 3))
    ax.set_xticklabels([labels[i] for i in range(0, len(vals), 3)], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: _es(v)))
    ax.set_ylabel("Venta neta (USD)", color=gray, fontsize=10)
    ax.set_ylim(min(vals) * 0.84, max(vals) * 1.12)
    _style_axes(ax)
    ax.grid(True, color="#E6EBF3", linewidth=0.8, axis="y")
    path["evolucion"] = _save(fig, "chart_evolucion_uce.png")

    cats = data["cat"]
    names = [c["categoria"] for c in cats][::-1]
    vcat = [c["ing"] / 1e6 for c in cats][::-1]
    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    colors = [navy if n in ("Accesorios", "Hogar") else "#3F6FA8" for n in names]
    bars = ax.barh(names, vcat, color=colors, height=0.62)
    for bar, c in zip(bars, cats[::-1]):
        ax.text(
            bar.get_width() + 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{c['ing']/1e6:.2f} M · {c['ing']/7452222.71*100:.1f} %".replace(".", ","),
            va="center",
            fontsize=9,
            color=gray,
        )
    ax.set_xlim(0, max(vcat) * 1.28)
    ax.set_xlabel("Venta neta (millones USD)", color=gray, fontsize=10)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}".replace(".", ",")))
    _style_axes(ax)
    path["categoria"] = _save(fig, "chart_categoria_uce.png")

    segs = data["seg"]
    vals_seg = [s["ing"] for s in segs]
    fig, ax = plt.subplots(figsize=(4.6, 3.7))
    palette = [navy, blue, "#6C93C4", "#A7BEDB", "#D3DCEA"]
    wedges, _ = ax.pie(
        vals_seg,
        colors=palette,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.40, edgecolor="white", linewidth=2),
    )
    ax.text(0, 0.08, "3.587", ha="center", va="center", fontsize=18, color=navy, fontweight="bold")
    ax.text(0, -0.12, "transacciones", ha="center", va="center", fontsize=8.5, color=gray)
    ax.legend(
        wedges,
        [f"{s['seg']}  {s['ing']/7452222.71*100:.1f} %".replace(".", ",") for s in segs],
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
        fontsize=8.5,
        labelcolor=gray,
    )
    ax.set_aspect("equal")
    path["segmento"] = _save(fig, "chart_segmento_uce.png")

    suc = data["suc"]
    names_s = [s["nombre_sucursal"] for s in suc][::-1]
    vals_s = [s["ing"] / 1e6 for s in suc][::-1]
    colors_s = [red if s["region"] == "Costa" else navy for s in suc][::-1]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    bars = ax.barh(names_s, vals_s, color=colors_s, height=0.62)
    for bar, s in zip(bars, suc[::-1]):
        ax.text(
            bar.get_width() + 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{s['ing']/1e6:.2f} M".replace(".", ","),
            va="center",
            fontsize=8.5,
            color=gray,
        )
    ax.set_xlim(0, max(vals_s) * 1.18)
    ax.set_xlabel("Venta neta (millones USD)", color=gray, fontsize=10)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}".replace(".", ",")))
    _style_axes(ax)
    from matplotlib.patches import Patch

    ax.legend(
        handles=[Patch(color=navy, label="Sierra"), Patch(color=red, label="Costa")],
        loc="lower right",
        frameon=False,
        fontsize=9,
    )
    path["sucursal"] = _save(fig, "chart_sucursal_uce.png")

    rej = [
        ("Fecha o valor inválido", 20),
        ("Cliente inexistente", 12),
        ("Producto inexistente", 10),
        ("Sucursal inexistente", 8),
    ]
    fig, ax = plt.subplots(figsize=(5.4, 2.8))
    names_r = [r[0] for r in rej][::-1]
    vals_r = [r[1] for r in rej][::-1]
    bars = ax.barh(
        names_r,
        vals_r,
        color=["#8C1420", "#AB1926", "#B93636", "#C04A4A"],
        height=0.58,
    )
    for bar, v in zip(bars, vals_r):
        ax.text(
            bar.get_width() + 0.35,
            bar.get_y() + bar.get_height() / 2,
            str(v),
            va="center",
            fontsize=10,
            color=red,
            fontweight="bold",
        )
    ax.set_xlim(0, 24)
    ax.set_xlabel("Registros rechazados", color=gray, fontsize=9.5)
    _style_axes(ax)
    path["rechazos"] = _save(fig, "chart_rechazos_uce.png")

    canal = data["canal"]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    names_c = [c["canal_venta"] for c in canal][::-1]
    vals_c = [c["ing"] / 1e6 for c in canal][::-1]
    bars = ax.barh(
        names_c,
        vals_c,
        color=[navy if n != "No especificado" else "#B9C6D8" for n in names_c],
        height=0.6,
    )
    for bar, c in zip(bars, canal[::-1]):
        ax.text(
            bar.get_width() + 0.03,
            bar.get_y() + bar.get_height() / 2,
            f"{c['ing']/7452222.71*100:.1f} %".replace(".", ","),
            va="center",
            fontsize=9,
            color=gray,
        )
    ax.set_xlim(0, max(vals_c) * 1.22)
    ax.set_xlabel("Venta neta (millones USD)", color=gray, fontsize=9.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}".replace(".", ",")))
    _style_axes(ax)
    path["canal"] = _save(fig, "chart_canal_uce.png")

    pago = data["pago"]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    names_p = [p["metodo_pago"] for p in pago][::-1]
    vals_p = [p["ing"] / 1e6 for p in pago][::-1]
    bars = ax.barh(
        names_p,
        vals_p,
        color=[blue if n != "No especificado" else "#B9C6D8" for n in names_p],
        height=0.6,
    )
    for bar, p in zip(bars, pago[::-1]):
        ax.text(
            bar.get_width() + 0.03,
            bar.get_y() + bar.get_height() / 2,
            f"{p['ing']/7452222.71*100:.1f} %".replace(".", ","),
            va="center",
            fontsize=9,
            color=gray,
        )
    ax.set_xlim(0, max(vals_p) * 1.22)
    ax.set_xlabel("Venta neta (millones USD)", color=gray, fontsize=9.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}".replace(".", ",")))
    _style_axes(ax)
    path["pago"] = _save(fig, "chart_pago_uce.png")

    anio = data["anio"]
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    labels_y = [str(a["anio"]) for a in anio]
    vals_y = [a["ing"] / 1e6 for a in anio]
    bars = ax.bar(labels_y, vals_y, color=[navy, blue, "#8FB0D8"], width=0.52)
    for bar, a in zip(bars, anio):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.06,
            f"{a['ing']/1e6:.2f} M".replace(".", ","),
            ha="center",
            fontsize=9.5,
            color=gray,
            fontweight="bold",
        )
    ax.set_ylim(0, max(vals_y) * 1.2)
    ax.set_ylabel("Venta neta (millones USD)", color=gray, fontsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}".replace(".", ",")))
    _style_axes(ax)
    ax.grid(True, color="#E6EBF3", linewidth=0.8, axis="y")
    path["anual"] = _save(fig, "chart_anual_uce.png")

    marca = data["marca"][:8][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    bars = ax.barh(
        [m["marca"] for m in marca], [m["ing"] / 1e6 for m in marca],
        color=navy, height=0.62,
    )
    for bar, m in zip(bars, marca):
        ax.text(
            bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
            f"{m['ing']/1e6:.2f} M · {int(m['uni'])} u.".replace(".", ","),
            va="center", fontsize=8.5, color=gray,
        )
    ax.set_xlim(0, max(m["ing"] / 1e6 for m in marca) * 1.3)
    ax.set_xlabel("Venta neta (millones USD)", color=gray, fontsize=9.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}".replace(".", ",")))
    _style_axes(ax)
    path["marca"] = _save(fig, "chart_marca_uce.png")

    desc = data["descuento"][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    bars = ax.barh(
        [d["categoria"] for d in desc], [d["descuento"] / 1000 for d in desc],
        color=red, height=0.62,
    )
    for bar, d in zip(bars, desc):
        ax.text(
            bar.get_width() + 0.6, bar.get_y() + bar.get_height() / 2,
            f"${d['descuento']:,.0f} · {d['prom']*100:.1f}%".replace(",", "."),
            va="center", fontsize=8.3, color=gray,
        )
    ax.set_xlim(0, max(d["descuento"] / 1000 for d in desc) * 1.34)
    ax.set_xlabel("Descuento otorgado (miles USD)", color=gray, fontsize=9.5)
    _style_axes(ax)
    path["descuento"] = _save(fig, "chart_descuento_uce.png")

    rej = data["rechazos_suc"][:8][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    bars = ax.barh(
        [r["nombre_sucursal"] for r in rej],
        [r["perdida"] for r in rej],
        color="#6C93C4", height=0.62,
    )
    for bar, r in zip(bars, rej):
        ax.text(
            bar.get_width() + 90, bar.get_y() + bar.get_height() / 2,
            f"${r['perdida']:,.0f} · {int(r['n'])} reg.".replace(",", "."),
            va="center", fontsize=8.3, color=gray,
        )
    ax.set_xlim(0, max(r["perdida"] for r in rej) * 1.34 if rej else 1)
    ax.set_xlabel("Pérdida estimada (USD)", color=gray, fontsize=9.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:,.0f}".replace(",", ".")))
    _style_axes(ax)
    path["rechazos_sucursal"] = _save(fig, "chart_rechazos_sucursal_uce.png")

    reg = data["region"][::-1]
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    colors_r = [red if r["region"] == "Costa" else navy for r in reg]
    bars = ax.barh([r["region"] for r in reg], [r["ing"] / 1e6 for r in reg], color=colors_r, height=0.55)
    total_reg = sum(r["ing"] for r in data["region"])
    for bar, r in zip(bars, reg):
        ax.text(
            bar.get_width() + 0.03, bar.get_y() + bar.get_height() / 2,
            f"{r['ing']/total_reg*100:.1f} %".replace(".", ","),
            va="center", fontsize=9.5, color=gray, fontweight="bold",
        )
    ax.set_xlim(0, max(r["ing"] / 1e6 for r in reg) * 1.28)
    ax.set_xlabel("Venta neta (millones USD)", color=gray, fontsize=9.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}".replace(".", ",")))
    _style_axes(ax)
    path["region"] = _save(fig, "chart_region_uce.png")

    kpi = data["kpi"]
    fig, ax = plt.subplots(figsize=(10.6, 2.0))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 2)
    ax.axis("off")
    tiles = [
        ("Ingresos", _es(kpi["ing"], 2)),
        ("Unidades", _es(kpi["uni"])),
        ("Margen", _es(kpi["mar"], 2)),
        ("Descuento", _es(kpi.get("desc", 0), 2)),
        ("Transacciones", _es(kpi["tx"])),
        ("Ticket prom.", _es(kpi["ing"] / kpi["tx"], 2)),
        ("Margen %", f"{kpi['mar']/kpi['ing']*100:.1f}%".replace(".", ",")),
        ("Pérdida rechazos", _es(data["rechazos_total"], 2)),
    ]
    for i, (label, value) in enumerate(tiles):
        x = 0.1 + i * 1.48
        ax.add_patch(plt.Rectangle((x, 0.2), 1.34, 1.55, facecolor="#EDF3FB", edgecolor="#B8C4D6", linewidth=0.9))
        ax.text(x + 0.67, 1.18, value, ha="center", va="center", fontsize=8.0, weight="bold", color=navy)
        ax.text(x + 0.67, 0.62, label, ha="center", va="center", fontsize=6.6, color=gray)
    path["kpis"] = _save(fig, "fig_superset_kpis.png")

    fig, ax = plt.subplots(figsize=(10.6, 5.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis("off")

    def dbox(x, y, w, h, label, color="#F7F9FC", edge="#C9D2E0", size=7.0):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor=edge, linewidth=0.9))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=size, color="#44546A")

    ax.text(6, 8.6, "Dashboard ejecutivo en Apache Superset", ha="center", fontsize=12,
            weight="bold", color=navy)
    for i, (label, value) in enumerate(tiles):
        row, col = divmod(i, 4)
        x = 0.2 + col * 2.92
        y = 7.55 - row * 0.9
        dbox(x, y, 2.72, 0.78, f"{label}\n{value}", "#EDF3FB", "#B8C4D6", 6.6)
    dbox(0.2, 3.7, 7.2, 3.25, "", "#EAF1FA", navy, 8)
    ax.text(3.8, 6.55, "Mapa interactivo (provincias y sucursales)", ha="center",
            fontsize=8, weight="bold", color=navy)
    ax.text(0.5, 5.4,
            "Relleno: azul claro → oscuro = intensidad de venta\n"
            "Borde: turquesa Costa · café Sierra · verde Amazonía\n"
            "Puntos rojos: sucursales seleccionables\n"
            "Clic en provincia/sucursal: filtra todo el dashboard\n"
            "Categoría: el mapa muestra dónde se vende",
            ha="left", va="center", fontsize=7.0, color="#44546A", linespacing=1.5)
    dbox(7.7, 3.7, 4.1, 3.25, "", "#F4F7FB", "#B8C4D6", 8)
    ax.text(9.75, 6.55, "Participación por categoría", ha="center", fontsize=8,
            weight="bold", color=navy)
    ax.text(9.75, 5.3, "Pastel sincronizado con\nel mapa y los filtros\nprovincia · categoría\nsucursal · marca · región",
            ha="center", va="center", fontsize=7.0, color="#44546A", linespacing=1.6)
    dbox(0.2, 2.95, 11.6, 0.55, "Evolución mensual de ventas netas", "#EDF3FB", "#B8C4D6", 7.5)
    rows_chart = [
        (2.15, ["Ventas por categoría", "Desempeño por sucursal", "Ventas por segmento"]),
        (1.4, ["Ventas por marca", "Descuento por categoría", "Ventas por región", "Ventas por canal"]),
        (0.65, ["Marca líder", "Categoría líder", "Sucursal líder", "Pérdidas por sucursal", "Pérdidas por fecha"]),
    ]
    for y, labels in rows_chart:
        n = len(labels)
        w = (11.6 - 0.12 * (n - 1)) / n
        for i, label in enumerate(labels):
            dbox(0.2 + i * (w + 0.12), y, w, 0.58, label, "#F7F9FC", "#C9D2E0", 6.4)
    path["dashboard"] = _save(fig, "fig_dashboard.png")

    return path


def prepare_template():
    ASSETS.mkdir(exist_ok=True)
    title_bg = ASSETS / "tpl_title_bg.jpeg"
    if not title_bg.exists():
        with zipfile.ZipFile(TEMPLATE) as zf:
            title_bg.write_bytes(zf.read("ppt/media/image2.jpeg"))
    # figura de arquitectura: se conserva la del informe
    path = {}
    path["arquitectura"] = ASSETS / "fig_arquitectura.png"
    path["dashboard"] = ASSETS / "fig_dashboard.png"
    path["kpis"] = ASSETS / "fig_superset_kpis.png"
    path["estrellas"] = ASSETS / "fig_arquitectura.png"
    path["modelo_actual"] = ROOT / "evidencias" / "modelo_actual.png"
    path["dashboard_actual"] = ROOT / "evidencias" / "dashboard_actual.png"
    path["rechazos_descuento"] = ROOT / "evidencias" / "rechazos_descuento.png"
    return title_bg, path


def base_presentation():
    prs = Presentation(TEMPLATE)
    _strip_slides(prs)
    return prs
