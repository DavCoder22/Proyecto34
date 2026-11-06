#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Presentación de defensa (versión ejecutiva)."""

from __future__ import annotations

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

from pres_common import (
    BLUE,
    BLUE_L,
    BORDER,
    GRAY,
    GRAY_L,
    GREEN,
    LIGHT,
    LIGHT2,
    NAVY,
    RED,
    TEXT,
    TITLE_FONT,
    WHITE,
    _layouts,
    add_badge,
    add_bullets,
    add_connector,
    add_picture_fit,
    add_plain_rect,
    add_rect,
    add_text,
    base_presentation,
    chip,
    closing_slide,
    content_slide,
    cover_slide,
    info_card,
    kpi_tile,
    section_slide,
)


def build_defensa(data, charts, title_bg):
    prs = base_presentation()
    _, lay_content, lay_section = _layouts(prs)
    lay_title = prs.slide_layouts[0]
    n = 0

    def new(title):
        nonlocal n
        n = len(prs.slides) + 1
        return content_slide(prs, lay_content, title, n)

    cover_slide(prs, lay_title, title_bg)

    # Agenda -----------------------------------------------------------------
    n = len(prs.slides) + 1
    s = content_slide(prs, lay_content, "Contenido de la exposición", n)
    items = [
        ("Problema y objetivos", "Por qué la calidad cambia la decisión"),
        ("Metodología y calidad", "Pipeline ETL y reglas auditables"),
        ("Arquitectura y modelo", "Esquema estrella y tecnologías"),
        ("Resultados comerciales", "KPIs, categorías y sucursales"),
        ("Dashboard y evidencia", "Superset y auditoría de cifras"),
        ("Discusión y cierre", "Hallazgos, conclusiones y futuro"),
    ]
    x0, y0, w, h, gx, gy = 0.9, 1.62, 3.76, 2.05, 0.2, 0.18
    for i, (t, sub) in enumerate(items):
        col, row = i % 3, i // 3
        x = x0 + col * (w + gx)
        y = y0 + row * (h + gy)
        add_rect(s, x, y, w, h, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x + 0.03, y + 0.09, 0.06, h - 0.18, RED if i in (0, 5) else NAVY)
        add_badge(s, x + 0.28, y + 0.28, 0.48, str(i + 1), fill=NAVY if i not in (0, 5) else RED, size=14)
        add_text(s, x + 0.92, y + 0.25, w - 1.05, 0.55, t, size=15.5, color=NAVY, bold=True)
        add_text(s, x + 0.92, y + 0.78, w - 1.05, 0.9, sub, size=10.5, color=GRAY)
        add_text(s, x + w - 0.38, y + 0.3, 0.2, 0.3, "›", size=22, color=BLUE_L, bold=True)

    section_slide(prs, lay_section, "01", "Contexto y problema", "Por qué la calidad de los datos es una decisión de negocio")

    # Problema ---------------------------------------------------------------
    s = new("Cuatro fuentes, un solo indicador: el reto de integrar")
    add_text(s, 0.9, 1.62, 5.2, 0.3, "FUENTES DEL ECOSISTEMA COMERCIAL", size=9.5, color=GRAY_L, bold=True)
    sources = [
        ("Clientes · CRM", "1.006 filas · ciudad, provincia y segmento"),
        ("Sucursales · SQL", "12 puntos de venta · región y provincia"),
        ("Productos · Excel", "123 registros · categoría, marca y costo"),
        ("Ventas · CSV", "6.870 líneas · grano de línea de venta"),
    ]
    for i, (t, sub) in enumerate(sources):
        y = 2.0 + i * 0.78
        add_rect(s, 0.9, y, 5.25, 0.66, LIGHT, line=BORDER, radius=0.08)
        add_plain_rect(s, 0.9, y, 0.06, 0.66, NAVY if i < 3 else RED)
        add_text(s, 1.12, y + 0.08, 1.6, 0.24, t, size=11.5, color=NAVY, bold=True)
        add_text(s, 1.12, y + 0.32, 4.85, 0.26, sub, size=9.5, color=GRAY)
    add_text(
        s,
        0.9,
        5.28,
        5.25,
        0.9,
        "Sin claves comunes ni reglas únicas, el reporte suma ventas sin cliente, producto o sucursal, y puede contar dos veces la misma operación.",
        size=11,
        color=GRAY,
        line_spacing=1.05,
    )
    metrics = [
        ("6.870", "líneas en la fuente de ventas"),
        ("20", "duplicados exactos en ventas"),
        ("30", "claves foráneas inválidas"),
        ("21", "fechas o valores inválidos"),
    ]
    for i, (v, lab) in enumerate(metrics):
        col, row = i % 2, i // 2
        x = 6.55 + col * 3.0
        y = 1.86 + row * 1.55
        add_rect(s, x, y, 2.85, 1.38, WHITE, line=BORDER, radius=0.08)
        add_text(s, x + 0.18, y + 0.1, 1.5, 0.5, v, size=27, color=RED if i in (1, 3) else NAVY, bold=True, font=TITLE_FONT)
        add_text(s, x + 0.18, y + 0.72, 2.5, 0.55, lab, size=9.5, color=GRAY)
    add_rect(s, 6.55, 5.0, 5.85, 1.55, NAVY, line=None, radius=0.05)
    add_text(s, 6.8, 5.14, 5.3, 0.24, "PREGUNTA DE INVESTIGACIÓN", size=9.5, color=LIGHT2, bold=True)
    add_text(
        s,
        6.8,
        5.45,
        5.3,
        1.0,
        "¿Cómo integrar y depurar cuatro fuentes comerciales heterogéneas para producir indicadores trazables, reproducibles y útiles para decidir?",
        size=12,
        color=WHITE,
        line_spacing=1.02,
    )

    # Objetivos --------------------------------------------------------------
    s = new("Objetivos: de la fuente dispersa al indicador confiable")
    add_rect(s, 0.9, 1.62, 11.53, 1.25, NAVY, line=None, radius=0.05)
    add_text(s, 1.12, 1.73, 2.3, 0.22, "OBJETIVO GENERAL", size=9.5, color=LIGHT2, bold=True)
    add_text(
        s,
        1.12,
        1.99,
        11.0,
        0.78,
        "Diseñar e implementar una prueba de concepto de integración, calidad y visualización comercial que genere indicadores trazables desde el dato de origen hasta el dashboard.",
        size=11.2,
        color=WHITE,
        line_spacing=1.0,
    )
    objectives = [
        "Integrar clientes, sucursales, productos y ventas con un pipeline ETL reproducible.",
        "Aplicar limpieza, homologación y validación, documentando cada rechazo.",
        "Construir un data warehouse en esquema estrella: hechos y cuatro dimensiones.",
        "Calcular ingresos netos, unidades vendidas, margen bruto y transacciones.",
        "Publicar un dashboard interactivo en Apache Superset como evidencia.",
        "Auditar la consistencia fuente–DW–dashboard y documentar las limitaciones.",
    ]
    x0, y0, w, h, gx, gy = 0.9, 3.08, 3.76, 1.62, 0.2, 0.16
    for i, txt in enumerate(objectives):
        col, row = i % 3, i // 3
        x = x0 + col * (w + gx)
        y = y0 + row * (h + gy)
        add_rect(s, x, y, w, h, LIGHT, line=BORDER, radius=0.08)
        add_badge(s, x + 0.18, y + 0.17, 0.38, str(i + 1), fill=NAVY, size=11)
        add_text(s, x + 0.66, y + 0.14, w - 0.8, h - 0.2, txt, size=11.2, color=TEXT, line_spacing=1.02, anchor=MSO_ANCHOR.MIDDLE)

    section_slide(prs, lay_section, "02", "Metodología y arquitectura", "Un pipeline auditable y un modelo pensado para decidir")

    # Metodología ------------------------------------------------------------
    s = new("Metodología: enfoque y pipeline ETL")
    chips = [("Aplicada", 1.28), ("Cuantitativa", 1.42), ("Descriptiva", 1.34), ("No experimental", 1.55), ("Transversal", 1.25), ("Ene 2024 – Ago 2026", 2.05)]
    x = 0.9
    for text, w in chips:
        chip(s, x, 1.6, w, text, size=9)
        x += w + 0.12
    steps = [
        ("1", "Extracción", "Copia a staging sin modificar el dato"),
        ("2", "Perfilado", "Filas, claves, nulos y duplicados"),
        ("3", "Limpieza", "Tipos, espacios y duplicados exactos"),
        ("4", "Homologación", "Categorías y vacíos a valor canónico"),
        ("5", "Validación", "FK, fechas y rangos numéricos"),
        ("6", "Transformación", "Venta neta, costo y margen"),
        ("7", "Carga", "Modelo estrella en SQLite y PostgreSQL"),
    ]
    x0, y0, w, h, gap = 0.9, 2.38, 1.52, 2.05, 0.09
    for i, (num, name, desc) in enumerate(steps):
        x = x0 + i * (w + gap)
        add_rect(s, x, y0, w, h, LIGHT, line=BORDER, radius=0.08)
        add_plain_rect(s, x, y0, w, 0.06, RED if i == 6 else NAVY)
        add_badge(s, x + 0.12, y0 + 0.18, 0.34, num, fill=RED if i == 6 else NAVY, size=10)
        add_text(s, x + 0.1, y0 + 0.62, w - 0.2, 0.5, name, size=10.5, color=NAVY, bold=True)
        add_text(s, x + 0.1, y0 + 1.08, w - 0.18, 0.9, desc, size=8.6, color=GRAY, line_spacing=1.0)
        if i < len(steps) - 1:
            add_text(s, x + w - 0.02, y0 + 0.78, 0.16, 0.3, "›", size=15, color=BLUE_L, bold=True)
    add_rect(s, 0.9, 4.72, 11.53, 0.78, NAVY, line=None, radius=0.05)
    add_text(
        s,
        1.12,
        4.85,
        11.0,
        0.52,
        "CRISP-DM aplicado: negocio → datos → preparación → modelado → evaluación → despliegue.",
        size=11.5,
        color=WHITE,
        bold=True,
    )
    add_text(
        s,
        0.9,
        5.72,
        11.53,
        0.9,
        "La calidad no es una etapa aparte: cada transición deja evidencia (perfil, reglas, log de rechazos y comparación antes/después).",
        size=11,
        color=GRAY,
        line_spacing=1.05,
    )

    # Arquitectura -----------------------------------------------------------
    s = new("Arquitectura de la solución")
    add_picture_fit(s, charts["arquitectura"], 1.15, 1.58, 11.0, 4.2)
    tech = ["Python + pandas", "SQLite", "PostgreSQL", "Apache Superset", "Docker", "Northflank + Neon"]
    x = 0.9
    for t in tech:
        chip(s, x, 5.95, 1.82, t, fill=LIGHT, color=NAVY, size=9.5, h=0.5)
        x += 1.95
    # Modelo estrella --------------------------------------------------------
    s = new("Modelo dimensional: esquema estrella")
    add_connector(s, 5.3, 3.58, 5.3, 2.8, BLUE_L, 1.5)
    add_connector(s, 5.3, 4.6, 5.3, 5.42, BLUE_L, 1.5)
    add_connector(s, 4.55, 4.09, 3.47, 4.09, BLUE_L, 1.5)
    add_connector(s, 6.05, 4.09, 7.05, 4.09, BLUE_L, 1.5)
    dims = [
        (3.55, 1.72, "DimTiempo", "fecha · año · mes · trimestre · semana"),
        (3.55, 5.42, "DimSucursal", "ciudad · provincia · región"),
        (0.92, 3.62, "DimCliente", "segmento · ciudad · provincia"),
        (7.05, 3.62, "DimProducto", "categoría · marca · costo unitario"),
    ]
    for x, y, t, sub in dims:
        add_rect(s, x, y, 2.55, 1.08, WHITE, line=BORDER, radius=0.08)
        add_plain_rect(s, x, y, 0.06, 1.08, NAVY)
        add_text(s, x + 0.18, y + 0.13, 2.2, 0.28, t, size=12, color=NAVY, bold=True)
        add_text(s, x + 0.18, y + 0.46, 2.2, 0.5, sub, size=8.8, color=GRAY, line_spacing=1.0)
    add_rect(s, 4.55, 3.58, 1.5, 1.02, NAVY, line=None, radius=0.07)
    add_text(s, 4.68, 3.68, 1.25, 0.3, "FactVentas", size=13, color=WHITE, bold=True)
    add_text(s, 4.68, 3.97, 1.25, 0.55, "Grano: línea de venta", size=8.5, color=LIGHT2, line_spacing=1.0)
    stats = [
        ("6.800", "líneas en FactVentas"),
        ("1.000 · 120 · 12", "clientes · productos · sucursales"),
        ("952", "días con ventas en DimTiempo"),
        ("1,90", "líneas por transacción"),
    ]
    for i, (v, lab) in enumerate(stats):
        y = 1.72 + i * 1.2
        add_rect(s, 9.88, y, 2.55, 1.0, LIGHT, line=BORDER, radius=0.08)
        add_text(s, 10.04, y + 0.1, 2.25, 0.38, v, size=16 if i != 1 else 12.5, color=NAVY, bold=True, font=TITLE_FONT)
        add_text(s, 10.04, y + 0.56, 2.25, 0.32, lab, size=8.5, color=GRAY)
    add_text(
        s,
        0.9,
        6.62,
        11.53,
        0.26,
        "Una tabla de hechos, cuatro dimensiones y un grano explícito: la base para que los filtros no dupliquen cifras.",
        size=9,
        color=GRAY_L,
        italic=True,
    )

    # Calidad ----------------------------------------------------------------
    s = new("Calidad de datos: antes y después del ETL")
    funnel = [
        ("6.870", "líneas originales", NAVY),
        ("6.850", "tras eliminar 20 duplicados", BLUE),
        ("6.800", "líneas válidas tras 50 rechazos", NAVY),
        ("98,98 %", "cobertura final · rechazo 0,73 %", RED),
    ]
    for i, (v, lab, col) in enumerate(funnel):
        y = 1.66 + i * 1.08
        add_rect(s, 0.9, y, 5.0, 0.94, col, line=None, radius=0.06)
        add_text(s, 1.12, y + 0.13, 1.75, 0.5, v, size=22, color=WHITE, bold=True, font=TITLE_FONT)
        add_text(s, 2.86, y + 0.14, 2.82, 0.62, lab, size=10.5, color=WHITE, line_spacing=1.0)
    add_picture_fit(s, charts["rechazos"], 6.2, 1.6, 6.2, 3.65)
    add_text(s, 6.2, 5.32, 6.2, 0.25, "50 registros rechazados por motivo", size=10, color=NAVY, bold=True)
    add_rect(s, 6.2, 5.7, 6.23, 0.82, LIGHT, line=BORDER, radius=0.06)
    add_text(
        s,
        6.4,
        5.8,
        5.85,
        0.62,
        "No se imputan ni se fuerzan: cada fila excluida queda en log_rechazos.csv para que el origen corrija la causa.",
        size=10,
        color=GRAY,
        line_spacing=1.0,
    )

    section_slide(prs, lay_section, "03", "Resultados", "Del dato validado al indicador de negocio")

    # KPIs -------------------------------------------------------------------
    s = new("Indicadores consolidados del universo válido")
    kpis = [
        ("Ingresos netos", "7.452.222,71", "USD · SUM(venta_neta)", NAVY),
        ("Unidades vendidas", "13.817", "unidades · SUM(cantidad)", NAVY),
        ("Margen bruto", "1.966.780,12", "USD · SUM(margen)", RED),
        ("Transacciones", "3.587", "COUNT(DISTINCT id_venta)", NAVY),
    ]
    for i, (lab, val, det, col) in enumerate(kpis):
        x = 0.9 + i * 2.94
        kpi_tile(s, x, 1.62, 2.78, 1.72, lab, val, det, accent=col, value_size=21)
    sub = [
        ("26,39 %", "margen sobre ingresos"),
        ("2.077,56 USD", "ticket promedio por transacción"),
        ("1,90", "líneas por transacción"),
    ]
    for i, (v, lab) in enumerate(sub):
        x = 0.9 + i * 3.92
        add_rect(s, x, 3.62, 3.76, 1.12, LIGHT, line=BORDER, radius=0.08)
        add_text(s, x + 0.2, 3.74, 3.4, 0.42, v, size=20, color=NAVY, bold=True, font=TITLE_FONT)
        add_text(s, x + 0.2, 4.24, 3.4, 0.32, lab, size=9.5, color=GRAY)
    add_rect(s, 0.9, 5.06, 11.53, 1.05, NAVY, line=None, radius=0.05)
    add_text(
        s,
        1.12,
        5.2,
        11.0,
        0.75,
        "Lectura gerencial: 7,45 M USD de ingresos, 26,39 % de margen y 2.077,56 USD por venta.\nEl margen separa el volumen de la rentabilidad: la categoría líder no siempre es la más rentable.",
        size=11.5,
        color=WHITE,
        line_spacing=1.02,
    )
    add_text(
        s,
        0.9,
        6.35,
        11.53,
        0.4,
        "Auditoría: los indicadores coinciden entre la fuente validada, FactVentas y el dashboard. Descuento otorgado: 404.749,54 USD; pérdida por rechazos: 44.001,54 USD.",
        size=10,
        color=GRAY,
        italic=True,
    )

    # Categorías y segmentos -------------------------------------------------
    s = new("Resultados: concentración por categoría y segmento")
    add_picture_fit(s, charts["categoria"], 0.75, 1.55, 7.0, 4.35)
    add_picture_fit(s, charts["segmento"], 7.9, 1.55, 4.5, 4.35)
    add_rect(s, 0.9, 6.0, 5.55, 0.95, LIGHT, line=BORDER, radius=0.06)
    add_text(
        s,
        1.08,
        6.08,
        5.2,
        0.78,
        "Accesorios y Hogar concentran 40,39 % de los ingresos; Hogar lidera el margen (397.149 vs. 396.930 USD).",
        size=9.8,
        color=GRAY,
        line_spacing=1.0,
    )
    add_rect(s, 6.65, 6.0, 5.78, 0.95, LIGHT, line=BORDER, radius=0.06)
    add_text(
        s,
        6.83,
        6.08,
        5.4,
        0.78,
        "Frecuente (28,45 %) tiene el ticket más alto entre los segmentos principales: oportunidad de fidelización.",
        size=9.8,
        color=GRAY,
        line_spacing=1.0,
    )

    # Sucursales -------------------------------------------------------------
    s = new("Resultados: desempeño por sucursal y región")
    add_picture_fit(s, charts["sucursal"], 0.75, 1.55, 7.45, 4.55)
    side = [
        ("57,99 %", "de los ingresos viene de la Sierra; la Costa aporta 42,01 %", NAVY),
        ("686.666 USD", "Guayaquil Centro, la sucursal líder (9,21 %)", RED),
        ("2.360,68 USD", "ticket promedio más alto: Ambato", NAVY),
        ("132.851 USD", "brecha entre la primera y la última sucursal", RED),
    ]
    for i, (v, lab, col) in enumerate(side):
        y = 1.62 + i * 1.16
        add_rect(s, 8.45, y, 3.98, 1.02, LIGHT, line=BORDER, radius=0.07)
        add_plain_rect(s, 8.45, y, 0.06, 1.02, col)
        add_text(s, 8.64, y + 0.1, 3.65, 0.36, v, size=16, color=col, bold=True, font=TITLE_FONT)
        add_text(s, 8.64, y + 0.5, 3.62, 0.46, lab, size=9.2, color=GRAY, line_spacing=1.0)
    add_text(
        s,
        0.9,
        6.3,
        11.53,
        0.3,
        "Doce sucursales, dos regiones y una lectura común: la comparación solo es válida sobre el mismo universo depurado.",
        size=9.5,
        color=GRAY_L,
        italic=True,
    )

    # Dashboard --------------------------------------------------------------
    s = new("Dashboard Sales Analytics: la cara visible del dato")
    add_picture_fit(s, charts["dashboard"], 0.75, 1.55, 6.95, 4.65)
    blocks = [
        ("Contenido", "8 tarjetas de KPI y un mapa-filtro con pastel; evolución, categoría, sucursal, segmento, marca, descuento, región, canal, líderes y pérdidas.", NAVY),
        ("Interactividad", "Clic en provincia o sucursal: todo el dashboard reacciona. Categoría en el pastel: el mapa muestra dónde se vende y colorea por intensidad.", BLUE),
        ("Evidencia", "Superset 3.1.1 sobre PostgreSQL; leyenda de color y región (Costa, Sierra, Amazonía); totales contrastados contra FactVentas.", RED),
    ]
    for i, (t, body, col) in enumerate(blocks):
        y = 1.62 + i * 1.55
        add_rect(s, 7.95, y, 4.48, 1.38, LIGHT, line=BORDER, radius=0.07)
        add_plain_rect(s, 7.95, y, 0.07, 1.38, col)
        add_text(s, 8.18, y + 0.12, 4.05, 0.3, t, size=12.5, color=NAVY, bold=True)
        add_text(s, 8.18, y + 0.46, 4.05, 0.82, body, size=9.6, color=GRAY, line_spacing=1.0)
    add_text(
        s,
        0.9,
        6.3,
        11.53,
        0.3,
        "El dashboard no reemplaza la calidad: la hace visible y verificable para la gerencia.",
        size=9.5,
        color=GRAY_L,
        italic=True,
    )

    # Evidencia Superset -----------------------------------------------------
    s = new("Evidencia: indicadores en Apache Superset")
    add_picture_fit(s, charts["kpis"], 0.9, 1.62, 11.5, 3.55)
    cards = [
        ("8 KPIs", "calculados en Superset sobre PostgreSQL"),
        ("Cuadre exacto", "los totales coinciden con FactVentas"),
        ("Interactivo", "mapa-filtro, pastel y filtros por provincia, categoría, sucursal, marca y región"),
    ]
    for i, (v, lab) in enumerate(cards):
        x = 0.9 + i * 3.92
        add_rect(s, x, 5.42, 3.76, 0.98, LIGHT, line=BORDER, radius=0.07)
        add_text(s, x + 0.18, 5.52, 3.4, 0.3, v, size=13, color=NAVY, bold=True)
        add_text(s, x + 0.18, 5.85, 3.4, 0.42, lab, size=9.2, color=GRAY, line_spacing=1.0)
    add_text(
        s,
        0.9,
        6.62,
        11.53,
        0.26,
        "Fuente: esquema del dashboard Sales Analytics (Superset 3.1.1) sobre PostgreSQL.",
        size=8.5,
        color=GRAY_L,
        italic=True,
    )


    # Pérdidas y descuentos --------------------------------------------------
    s = new("Rechazos como pérdida y descuentos por categoría")
    add_picture_fit(s, charts["rechazos_sucursal"], 0.65, 1.55, 5.95, 3.75)
    add_picture_fit(s, charts["descuento"], 6.75, 1.55, 5.85, 3.75)
    add_text(
        s, 0.8, 5.42, 11.6, 0.7,
        "Los 50 rechazos se valorizan como pérdida estimada. El descuento otorgado se analiza por categoría "
        "y se filtra por provincia desde el mapa.",
        size=9.6, color=GRAY_L, italic=True, line_spacing=1.0,
    )

    # Marcas y región --------------------------------------------------------
    s = new("Marcas líderes y peso de la región")
    add_picture_fit(s, charts["marca"], 0.65, 1.55, 6.55, 4.15)
    add_picture_fit(s, charts["region"], 7.45, 1.55, 4.75, 4.15)
    add_text(
        s, 0.8, 5.78, 11.6, 0.55,
        "Puma lidera la venta neta. La Sierra aporta 57,99 % y la Costa 42,01 %; el mapa distingue "
        "las regiones con el borde de color.",
        size=9.6, color=GRAY_L, italic=True, line_spacing=1.0,
    )


    # Evidencia de los cambios ----------------------------------------------
    s = new("Evidencia de los cambios: modelo, dashboard y pérdidas")
    add_picture_fit(s, charts["modelo_actual"], 0.55, 1.55, 6.05, 3.85)
    add_picture_fit(s, charts["dashboard_actual"], 6.75, 1.55, 5.95, 3.85)
    add_text(
        s, 0.8, 5.5, 11.6, 0.75,
        "El modelo incorpora FactRechazos y vistas analíticas; el dashboard resume ocho KPIs, mapa-filtro y leyenda. "
        "La evidencia de pérdidas y descuentos se obtiene de la misma base validada.",
        size=9.4, color=GRAY_L, italic=True, line_spacing=1.0,
    )

    section_slide(prs, lay_section, "04", "Discusión y cierre", "Qué demuestra la PoC y qué falta para producción")

    # Hallazgos --------------------------------------------------------------
    s = new("Hallazgos del proceso de desarrollo")
    findings = [
        ("Fuentes heterogéneas", "CSV y XLSX con BOM, separadores distintos y hasta 7 columnas vacías; se normalizó el esquema antes de perfilar."),
        ("Grano de ventas", "6.870 líneas frente a 3.600 id_venta únicos: el grano es la línea y las ventas se cuentan con DISTINCT."),
        ("Duplicados y nulos", "20 duplicados en ventas, 6 en clientes y 3 en productos; los vacíos se hicieron explícitos."),
        ("Integridad referencial", "30 líneas con FK inexistente (12 cliente, 10 producto, 8 sucursal) se rechazaron y registraron."),
        ("Fechas y descuentos", "21 fechas inválidas excluidas; descuentos decimal/porcentaje normalizados al rango 0–1."),
        ("Resultado auditable", "6.870 → 6.800 líneas (98,98 %); 20 duplicados y 50 rechazos documentados."),
    ]
    x0, y0, w, h, gx, gy = 0.9, 1.62, 5.68, 1.38, 0.17, 0.18
    for i, (t, body) in enumerate(findings):
        col, row = i % 2, i // 2
        x = x0 + col * (w + gx)
        y = y0 + row * (h + gy)
        info_card(s, x, y, w, h, t, body, badge=str(i + 1), accent=RED if i in (3, 5) else NAVY, title_size=11.5, body_size=9.2)
    add_text(
        s,
        0.9,
        6.6,
        11.53,
        0.3,
        "Lección de despliegue: usar rutas estables o volúmenes nombrados; los bind mounts con ruta absoluta fallan si cambia la unidad.",
        size=9,
        color=GRAY_L,
        italic=True,
    )

    # Cumplimiento -----------------------------------------------------------
    s = new("Cumplimiento de objetivos y auditoría de cifras")
    objs = [
        "Integrar las cuatro fuentes con ETL",
        "Reglas de calidad y registro de rechazos",
        "Modelo estrella (hechos + 4 dimensiones)",
        "Cálculo de los indicadores comerciales y de calidad",
        "Dashboard interactivo en Superset",
        "Verificación de consistencia y limitaciones",
    ]
    for i, t in enumerate(objs):
        y = 1.66 + i * 0.82
        add_rect(s, 0.9, y, 7.55, 0.66, LIGHT, line=BORDER, radius=0.08)
        add_badge(s, 1.02, y + 0.13, 0.4, str(i + 1), fill=NAVY, size=10.5)
        add_text(s, 1.56, y + 0.16, 5.2, 0.35, t, size=10.8, color=GRAY)
        add_rect(s, 7.05, y + 0.13, 1.15, 0.4, GREEN, line=None, radius=0.5)
        add_text(s, 7.05, y + 0.15, 1.15, 0.35, "Cumplido", size=8.5, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_rect(s, 8.72, 1.62, 3.7, 4.85, NAVY, line=None, radius=0.05)
    add_text(s, 8.95, 1.78, 3.25, 0.3, "AUDITORÍA DE CIFRAS", size=9.5, color=LIGHT2, bold=True)
    add_text(s, 8.95, 2.12, 3.25, 0.3, "Fuente = DW = dashboard", size=11.5, color=WHITE, bold=True)
    audit = [("Ingresos", "7.452.222,71 USD"), ("Unidades", "13.817"), ("Margen", "1.966.780,12 USD"), ("Transacciones", "3.587")]
    for i, (k, v) in enumerate(audit):
        y = 2.62 + i * 0.68
        add_text(s, 8.95, y, 1.45, 0.3, k, size=9, color=LIGHT2)
        add_text(s, 8.95, y + 0.2, 3.2, 0.35, v, size=13, color=WHITE, bold=True)
    add_text(
        s,
        8.95,
        5.42,
        3.25,
        0.75,
        "Incidencia: 21 vs 20 fechas inválidas; se adoptó el valor verificable del log.",
        size=8.5,
        color=LIGHT2,
        line_spacing=1.0,
    )
    add_text(
        s,
        0.9,
        6.6,
        11.53,
        0.3,
        "La trazabilidad permite responder por cada cifra y explicar cada exclusión.",
        size=9,
        color=GRAY_L,
        italic=True,
    )

    # Discusión --------------------------------------------------------------
    s = new("Discusión: hallazgos y limitaciones")
    add_rect(s, 0.9, 1.62, 5.78, 4.95, WHITE, line=BORDER, radius=0.05)
    add_text(s, 1.12, 1.78, 5.3, 0.3, "HALLAZGOS", size=10, color=GRAY_L, bold=True)
    hall = [
        ("La calidad cambia el universo.", " 70 de 6.870 líneas (1,02 %) no eran integrables; se evitaron ventas sin dimensión válida."),
        ("Ventas concentradas.", " Accesorios y Hogar 40,39 %; Masivo 50,85 %; Sierra 57,99 %."),
        ("El margen matiza el ranking.", " La categoría líder en ventas no es necesariamente la más rentable."),
        ("Descuentos y rechazos son medibles.", " 404.749,54 USD de descuento otorgado y 44.001,54 USD de pérdida estimada por rechazos."),
    ]
    for i, (lead, rest) in enumerate(hall):
        y = 2.16 + i * 1.08
        add_badge(s, 1.12, y, 0.4, str(i + 1), fill=NAVY, size=10.5)
        add_text(s, 1.66, y - 0.02, 4.8, 1.05, lead + rest, size=9.8, color=GRAY, line_spacing=1.0)
    add_rect(s, 6.65, 1.62, 5.78, 4.95, LIGHT, line=BORDER, radius=0.05)
    add_text(s, 6.9, 1.78, 5.3, 0.3, "LIMITACIONES Y VALIDEZ", size=10, color=GRAY_L, bold=True)
    limits = [
        "Datos académicos y sintéticos: no generalizar a una empresa real.",
        "Carga batch, sin incremental ni orquestación en producción.",
        "Sin inferencia estadística ni modelos predictivos.",
        "Rentabilidad limitada al margen bruto.",
        "Gobierno de datos incipiente.",
    ]
    add_bullets(s, 6.9, 2.2, 5.28, 4.1, limits, size=11.5, bullet_color=RED, space_after=12)
    add_text(
        s,
        0.9,
        6.66,
        11.53,
        0.3,
        "Amenaza principal: si los rechazos se concentran en una categoría o sucursal, la comparación puede sesgarse.",
        size=9,
        color=GRAY_L,
        italic=True,
    )

    # Conclusiones -----------------------------------------------------------
    s = new("Conclusiones")
    concl = [
        ("Integración trazable", "Cuatro fuentes heterogéneas integradas con un pipeline ETL reproducible y herramientas abiertas.", NAVY),
        ("La calidad modifica el universo", "6.870 → 6.800 líneas (98,98 % de cobertura), sin ventas huérfanas ni duplicadas.", NAVY),
        ("Indicadores consistentes", "7,45 M USD de ingresos netos, 13.817 unidades, 1,97 M USD de margen y 3.587 transacciones.", RED),
        ("Calidad como evidencia", "Log de rechazos, comparación antes/después y auditoría permiten defender cada cifra.", RED),
    ]
    for i, (t, body, col) in enumerate(concl):
        col_i, row = i % 2, i // 2
        x = 0.9 + col_i * 5.88
        y = 1.72 + row * 2.08
        add_rect(s, x, y, 5.65, 1.9, LIGHT, line=BORDER, radius=0.07)
        add_plain_rect(s, x, y, 0.07, 1.9, col)
        add_badge(s, x + 0.24, y + 0.22, 0.48, str(i + 1), fill=col, size=13)
        add_text(s, x + 0.86, y + 0.2, 4.55, 0.4, t, size=14.5, color=NAVY, bold=True)
        add_text(s, x + 0.86, y + 0.68, 4.55, 1.1, body, size=10.8, color=GRAY, line_spacing=1.02)
    add_rect(s, 0.9, 5.95, 11.53, 0.72, NAVY, line=None, radius=0.05)
    add_text(
        s,
        1.12,
        6.08,
        11.0,
        0.45,
        "La PoC deja un método reproducible: integrar, medir la calidad y demostrar cada cifra antes de decidir.",
        size=11.5,
        color=WHITE,
        bold=True,
    )

    # Recomendaciones --------------------------------------------------------
    s = new("Recomendaciones y trabajo futuro")
    recs = [
        "Carga incremental y orquestador (Airflow).",
        "Pruebas automatizadas de calidad y regresión de totales.",
        "Monitorear la tasa de rechazo con umbral de alerta.",
        "Catálogo de datos: KPIs, dueños y reglas.",
        "Metas y presupuestos por sucursal en el dashboard.",
        "Costos operativos y logísticos para ampliar rentabilidad.",
        "Superset: roles, autenticación y respaldo.",
        "Validar con datos reales anonimizados.",
    ]
    x0, y0, w, h, gx, gy = 0.9, 1.66, 2.76, 1.72, 0.19, 0.18
    for i, txt in enumerate(recs):
        col, row = i % 4, i // 4
        x = x0 + col * (w + gx)
        y = y0 + row * (h + gy)
        add_rect(s, x, y, w, h, LIGHT, line=BORDER, radius=0.07)
        add_badge(s, x + 0.18, y + 0.18, 0.42, str(i + 1), fill=RED if i >= 4 else NAVY, size=11)
        add_text(s, x + 0.18, y + 0.72, w - 0.34, h - 0.8, txt, size=9.8, color=GRAY, line_spacing=1.02)
    add_rect(s, 0.9, 5.55, 11.53, 0.78, NAVY, line=None, radius=0.05)
    add_text(
        s,
        1.12,
        5.68,
        11.0,
        0.5,
        "Prioridad inmediata: automatizar la carga y monitorear la calidad antes de escalar a producción.",
        size=11.5,
        color=WHITE,
        bold=True,
    )

    closing_slide(prs, lay_title, title_bg)
    return prs
