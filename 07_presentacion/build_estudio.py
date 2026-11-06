#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Presentación de estudio (versión completa con teoría, glosario y Q&A)."""

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
    add_table,
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


def build_estudio(data, charts, title_bg):
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
        ("Problema y objetivos", "Contexto, pregunta y alcance"),
        ("Marco teórico", "BI, ETL, calidad y modelo dimensional"),
        ("Metodología", "Enfoque, pipeline y arquitectura"),
        ("Resultados", "Calidad, KPIs y análisis comercial"),
        ("Discusión y cierre", "Hallazgos, conclusiones y futuro"),
        ("Glosario y preguntas", "Conceptos clave y simulación de jurado"),
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

    section_slide(prs, lay_section, "01", "Problema y objetivos", "Del dato disperso a la decisión basada en evidencia")

    # Problema ---------------------------------------------------------------
    s = new("El problema: datos dispersos, indicadores poco confiables")
    add_text(s, 0.9, 1.62, 5.2, 0.3, "CUATRO FUENTES, CUATRO REALIDADES", size=9.5, color=GRAY_L, bold=True)
    add_text(
        s,
        0.9,
        1.95,
        5.25,
        1.35,
        "Cuando las fuentes no comparten claves, formatos ni reglas de negocio, los reportes muestran cifras inconsistentes y las decisiones se apoyan en información parcial.",
        size=11.5,
        color=TEXT,
        line_spacing=1.03,
    )
    sources = [
        ("Clientes · CRM", "1.006 filas · segmento, ciudad y provincia"),
        ("Sucursales · SQL", "12 puntos de venta · región y provincia"),
        ("Productos · Excel", "123 registros · categoría, marca y costo"),
        ("Ventas · CSV", "6.870 líneas · grano de línea de venta"),
    ]
    for i, (t, sub) in enumerate(sources):
        y = 3.42 + i * 0.72
        add_rect(s, 0.9, y, 5.25, 0.62, LIGHT, line=BORDER, radius=0.08)
        add_plain_rect(s, 0.9, y, 0.06, 0.62, NAVY if i < 3 else RED)
        add_text(s, 1.12, y + 0.06, 1.6, 0.24, t, size=11, color=NAVY, bold=True)
        add_text(s, 1.12, y + 0.3, 4.85, 0.26, sub, size=9, color=GRAY)
    metrics = [
        ("6.870", "líneas en ventas"),
        ("20", "duplicados exactos"),
        ("30", "FK inválidas"),
        ("21", "fechas o valores inválidos"),
    ]
    for i, (v, lab) in enumerate(metrics):
        col, row = i % 2, i // 2
        x = 6.55 + col * 3.0
        y = 1.72 + row * 1.45
        add_rect(s, x, y, 2.85, 1.28, WHITE, line=BORDER, radius=0.08)
        add_text(s, x + 0.18, y + 0.08, 1.5, 0.45, v, size=25, color=RED if i in (1, 3) else NAVY, bold=True, font=TITLE_FONT)
        add_text(s, x + 0.18, y + 0.65, 2.5, 0.5, lab, size=9, color=GRAY)
    add_rect(s, 6.55, 4.72, 5.85, 1.72, NAVY, line=None, radius=0.05)
    add_text(s, 6.8, 4.86, 5.3, 0.24, "PREGUNTA DE INVESTIGACIÓN", size=9.5, color=LIGHT2, bold=True)
    add_text(
        s,
        6.8,
        5.18,
        5.3,
        1.1,
        "¿Cómo integrar y depurar cuatro fuentes comerciales heterogéneas para producir indicadores trazables, reproducibles y útiles para decidir?",
        size=12,
        color=WHITE,
        line_spacing=1.02,
    )
    add_text(s, 0.9, 6.62, 5.3, 0.3, "Sin control, el dashboard suma ventas huérfanas o duplica operaciones.", size=9.2, color=GRAY_L, italic=True)

    # Objetivos --------------------------------------------------------------
    s = new("Objetivos de la prueba de concepto")
    add_rect(s, 0.9, 1.62, 11.53, 1.22, NAVY, line=None, radius=0.05)
    add_text(s, 1.12, 1.72, 2.3, 0.22, "OBJETIVO GENERAL", size=9.5, color=LIGHT2, bold=True)
    add_text(
        s,
        1.12,
        1.98,
        11.0,
        0.78,
        "Diseñar e implementar una prueba de concepto de integración, calidad de datos y visualización comercial que genere indicadores confiables, con trazabilidad desde el dato de origen hasta el dashboard.",
        size=11,
        color=WHITE,
        line_spacing=1.0,
    )
    objectives = [
        "Integrar clientes, sucursales, productos y ventas con un pipeline ETL reproducible.",
        "Aplicar reglas de limpieza, homologación y validación, documentando los rechazos.",
        "Construir un data warehouse en esquema estrella con una tabla de hechos y cuatro dimensiones.",
        "Calcular ingresos netos, unidades vendidas, margen bruto y transacciones.",
        "Publicar un dashboard interactivo en Apache Superset con evidencia HTML.",
        "Verificar la consistencia fuente–DW–dashboard y documentar las limitaciones.",
    ]
    x0, y0, w, h, gx, gy = 0.9, 3.06, 3.76, 1.6, 0.2, 0.16
    for i, txt in enumerate(objectives):
        col, row = i % 3, i // 3
        x = x0 + col * (w + gx)
        y = y0 + row * (h + gy)
        add_rect(s, x, y, w, h, LIGHT, line=BORDER, radius=0.08)
        add_badge(s, x + 0.18, y + 0.17, 0.38, str(i + 1), fill=NAVY, size=11)
        add_text(s, x + 0.66, y + 0.14, w - 0.8, h - 0.2, txt, size=10.3, color=TEXT, line_spacing=1.02)

    # Justificación ----------------------------------------------------------
    s = new("Aporte y alcance de la PoC")
    add_text(
        s,
        0.9,
        1.62,
        11.5,
        0.45,
        "La contribución no es solo un tablero: es un método reproducible para convertir fuentes dispersas en indicadores defendibles.",
        size=11.5,
        color=GRAY,
    )
    aportes = [
        ("Aporte académico", "Integra BI, calidad, ETL y modelado dimensional en un caso completo y documentado.", NAVY),
        ("Aporte práctico", "Entrega un dashboard funcional y un conjunto de reglas reutilizables por otra área.", NAVY),
        ("Aporte metodológico", "Combina CRISP-DM con controles de calidad medibles y evidencia de cada exclusión.", RED),
        ("Aporte gerencial", "Permite priorizar categorías, sucursales y segmentos con cifras trazables.", RED),
    ]
    for i, (t, body, col) in enumerate(aportes):
        col_i, row = i % 2, i // 2
        x = 0.9 + col_i * 5.88
        y = 2.38 + row * 1.95
        add_rect(s, x, y, 5.65, 1.75, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x, y, 0.07, 1.75, col)
        add_text(s, x + 0.24, y + 0.16, 5.15, 0.32, t, size=13, color=NAVY, bold=True)
        add_text(s, x + 0.24, y + 0.55, 5.15, 1.05, body, size=10.5, color=TEXT, line_spacing=1.02)
    add_rect(s, 0.9, 6.25, 11.53, 0.55, LIGHT, line=BORDER, radius=0.05)
    add_text(
        s,
        1.1,
        6.34,
        11.1,
        0.35,
        "Alcance: cuatro fuentes, 32 meses, una tabla de hechos y cuatro dimensiones; no incluye carga incremental ni gobierno de datos.",
        size=9.2,
        color=GRAY,
    )

    section_slide(prs, lay_section, "02", "Marco teórico", "Los conceptos que sostienen la solución")

    # Marco teórico ----------------------------------------------------------
    s = new("Marco teórico: cinco conceptos integradores")
    concepts = [
        ("Inteligencia de negocios", "Prácticas y tecnologías que integran y presentan datos para apoyar la toma de decisiones.", "Sharda et al., 2020", NAVY),
        ("ETL y data warehouse", "Extrae, transforma y carga datos en un repositorio organizado por procesos de negocio.", "Kimball & Ross, 2013", NAVY),
        ("Calidad de datos", "Se mide con exactitud, completitud, consistencia y unicidad; no se declara.", "Batini et al., 2009; ISO 8000-61", RED),
        ("Modelo dimensional", "Tabla de hechos con métricas y dimensiones que dan contexto: quién, qué, cuándo y dónde.", "Kimball & Ross, 2013", NAVY),
        ("KPIs y dashboards", "Indicadores con definición estable y fórmula reproducible; pocos y con contexto.", "Few, 2006", RED),
    ]
    for i, (t, body, cite, col) in enumerate(concepts[:3]):
        x = 0.9 + i * 3.92
        add_rect(s, x, 1.62, 3.76, 2.15, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x, 1.62, 3.76, 0.06, col)
        add_text(s, x + 0.2, 1.8, 3.35, 0.5, t, size=13.5, color=NAVY, bold=True)
        add_text(s, x + 0.2, 2.32, 3.35, 1.0, body, size=10, color=TEXT, line_spacing=1.02)
        add_text(s, x + 0.2, 3.34, 3.35, 0.3, cite, size=8.5, color=GRAY_L, italic=True)
    for i, (t, body, cite, col) in enumerate(concepts[3:]):
        x = 0.9 + i * 5.88
        add_rect(s, x, 4.02, 5.65, 1.9, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x, 4.02, 5.65, 0.06, col)
        add_text(s, x + 0.24, 4.2, 5.15, 0.35, t, size=13.5, color=NAVY, bold=True)
        add_text(s, x + 0.24, 4.6, 5.15, 0.9, body, size=10.5, color=TEXT, line_spacing=1.02)
        add_text(s, x + 0.24, 5.52, 5.15, 0.28, cite, size=8.5, color=GRAY_L, italic=True)
    add_text(
        s,
        0.9,
        6.25,
        11.53,
        0.4,
        "La PoC conecta los cinco conceptos: BI define el propósito, ETL mueve el dato, calidad lo hace confiable, el modelo lo organiza y los KPIs lo vuelven accionable.",
        size=9.5,
        color=GRAY,
        italic=True,
    )

    # ETL y DW ---------------------------------------------------------------
    s = new("ETL y data warehouse: del origen al repositorio analítico")
    stages = [
        ("Extract", "Lectura de CSV y Excel, copia a staging y perfilado inicial.", NAVY),
        ("Transform", "Limpieza, homologación, validación y cálculo de métricas.", BLUE),
        ("Load", "Carga del modelo estrella en SQLite y PostgreSQL.", RED),
    ]
    for i, (t, body, col) in enumerate(stages):
        x = 0.9 + i * 3.92
        add_rect(s, x, 1.62, 3.76, 1.55, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x, 1.62, 3.76, 0.06, col)
        add_text(s, x + 0.2, 1.78, 3.35, 0.35, f"{i+1}. {t}", size=14, color=NAVY, bold=True)
        add_text(s, x + 0.2, 2.18, 3.35, 0.85, body, size=10, color=TEXT, line_spacing=1.02)
    add_rect(s, 0.9, 3.5, 11.53, 1.55, LIGHT, line=BORDER, radius=0.05)
    add_text(s, 1.12, 3.66, 2.2, 0.3, "¿QUÉ GARANTIZA?", size=9.5, color=GRAY_L, bold=True)
    add_bullets(
        s,
        1.12,
        3.98,
        11.0,
        1.0,
        [
            ("Reproducibilidad: ", "el mismo dato y las mismas reglas producen el mismo resultado."),
            ("Auditabilidad: ", "staging conserva el original y el log explica cada exclusión."),
            ("Consistencia: ", "una sola definición de venta neta, margen y transacción."),
        ],
        size=10.5,
        space_after=2,
    )
    add_rect(s, 0.9, 5.25, 5.65, 1.35, NAVY, line=None, radius=0.05)
    add_text(s, 1.12, 5.38, 5.15, 0.3, "DATA WAREHOUSE", size=9.5, color=LIGHT2, bold=True)
    add_text(
        s,
        1.12,
        5.68,
        5.15,
        0.8,
        "Organiza el dato por procesos de negocio para que las consultas agregadas sean simples y rápidas.",
        size=10.5,
        color=WHITE,
        line_spacing=1.0,
    )
    add_rect(s, 6.78, 5.25, 5.65, 1.35, LIGHT, line=BORDER, radius=0.05)
    add_text(s, 7.0, 5.38, 5.15, 0.3, "DECISIÓN DE DISEÑO", size=9.5, color=GRAY_L, bold=True)
    add_text(
        s,
        7.0,
        5.68,
        5.15,
        0.8,
        "Se prioriza el esquema estrella sobre el modelo normalizado: menos joins y KPIs más legibles.",
        size=10.5,
        color=TEXT,
        line_spacing=1.0,
    )

    # Calidad de datos -------------------------------------------------------
    s = new("Calidad de datos: dimensiones que se miden")
    dims = [
        ("Exactitud", "El dato coincide con la realidad o con la fuente autorizada."),
        ("Completitud", "No faltan valores necesarios para el análisis."),
        ("Consistencia", "El mismo dato mantiene formato y significado entre fuentes."),
        ("Unicidad", "No hay registros duplicados para una misma clave."),
        ("Integridad referencial", "Toda clave foránea existe en su dimensión; si no, se rechaza."),
        ("Homologación", "Variantes de escritura se unifican en un valor canónico."),
    ]
    x0, y0, w, h, gx, gy = 0.9, 1.62, 3.76, 1.62, 0.2, 0.18
    for i, (t, body) in enumerate(dims):
        col, row = i % 3, i // 3
        x = x0 + col * (w + gx)
        y = y0 + row * (h + gy)
        add_rect(s, x, y, w, h, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x, y, 0.07, h, RED if i in (4, 5) else NAVY)
        add_text(s, x + 0.22, y + 0.16, w - 0.4, 0.32, t, size=12.5, color=NAVY, bold=True)
        add_text(s, x + 0.22, y + 0.56, w - 0.4, 0.95, body, size=9.8, color=TEXT, line_spacing=1.0)
    add_rect(s, 0.9, 5.35, 11.53, 1.15, NAVY, line=None, radius=0.05)
    add_text(
        s,
        1.15,
        5.5,
        11.0,
        0.85,
        "La calidad no se declara: se mide antes y después del ETL. Cada regla tiene problema, criterio y efecto documentado.",
        size=12,
        color=WHITE,
        line_spacing=1.02,
    )

    # Modelo dimensional -----------------------------------------------------
    s = new("Modelo dimensional: hechos, dimensiones y grano")
    add_connector(s, 3.95, 3.4, 3.95, 2.78, BLUE_L, 1.4)
    add_connector(s, 3.95, 4.5, 3.95, 5.1, BLUE_L, 1.4)
    add_connector(s, 3.0, 3.95, 2.72, 3.95, BLUE_L, 1.4)
    add_connector(s, 5.0, 3.95, 5.3, 3.95, BLUE_L, 1.4)
    for x, y, w, h, t, sub in [
        (3.0, 1.78, 1.9, 1.0, "DimTiempo", "fecha · año · mes"),
        (3.0, 5.1, 1.9, 1.0, "DimSucursal", "ciudad · región"),
        (0.9, 3.45, 1.8, 1.0, "DimCliente", "segmento · ciudad"),
        (5.3, 3.45, 1.8, 1.0, "DimProducto", "categoría · marca"),
    ]:
        add_rect(s, x, y, w, h, WHITE, line=BORDER, radius=0.08)
        add_plain_rect(s, x, y, 0.06, h, NAVY)
        add_text(s, x + 0.14, y + 0.2, w - 0.24, 0.28, t, size=10.5, color=NAVY, bold=True)
        add_text(s, x + 0.14, y + 0.5, w - 0.24, 0.42, sub, size=8, color=GRAY)
    add_rect(s, 3.0, 3.4, 2.0, 1.1, NAVY, line=None, radius=0.07)
    add_text(s, 3.14, 3.52, 1.75, 0.28, "FactVentas", size=12, color=WHITE, bold=True)
    add_text(s, 3.14, 3.82, 1.75, 0.55, "línea de venta\nventa_neta · margen", size=8, color=LIGHT2, line_spacing=1.0)
    add_text(s, 7.25, 1.62, 5.15, 0.3, "DECISIONES DE MODELADO", size=9.5, color=GRAY_L, bold=True)
    bullets = [
        ("Grano explícito. ", "Una fila de FactVentas es una línea de venta, no una transacción."),
        ("Medidas aditivas. ", "cantidad, venta_neta, costo_total y margen se suman por dimensión."),
        ("Dimensiones conformadas. ", "Tiempo, cliente, producto y sucursal se comparten entre KPIs."),
        ("Claves sustitutas. ", "Cada dimensión tiene su id para desacoplar el origen."),
        ("Sin ventas huérfanas. ", "Toda FK debe existir; si no, la fila se rechaza."),
    ]
    add_bullets(s, 7.25, 2.0, 5.1, 4.2, bullets, size=11, bullet_color=BLUE, space_after=11)
    add_text(
        s,
        0.9,
        6.35,
        11.53,
        0.3,
        "El modelo estrella hace que el negocio entienda la estructura y que los KPIs sean reproducibles.",
        size=9.5,
        color=GRAY_L,
        italic=True,
    )

    # KPIs y dashboards ------------------------------------------------------
    s = new("KPIs y dashboards: pocos, definidos y accionables")
    good = [
        ("Definición estable", "Fórmula documentada, dueño y fuente única."),
        ("Contexto", "Comparación con meta, periodo o promedio."),
        ("Pocos indicadores", "Cuatro o cinco KPIs evitan distraer la decisión."),
        ("Interactividad", "Filtros que responden preguntas de negocio, no curiosidad."),
    ]
    for i, (t, body) in enumerate(good):
        x = 0.9 + (i % 2) * 5.88
        y = 1.62 + (i // 2) * 1.55
        add_rect(s, x, y, 5.65, 1.38, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x, y, 0.07, 1.38, NAVY if i % 2 == 0 else RED)
        add_text(s, x + 0.24, y + 0.14, 5.15, 0.32, t, size=13, color=NAVY, bold=True)
        add_text(s, x + 0.24, y + 0.52, 5.15, 0.78, body, size=10.5, color=TEXT, line_spacing=1.0)
    add_rect(s, 0.9, 4.85, 11.53, 1.62, LIGHT, line=BORDER, radius=0.05)
    add_text(s, 1.15, 5.0, 2.3, 0.3, "PRINCIPIO RECTOR", size=9.5, color=GRAY_L, bold=True)
    add_text(
        s,
        1.15,
        5.32,
        11.0,
        1.0,
        "Un dashboard no es un depósito de gráficos: es una interfaz para decidir. Cada visual debe responder una pregunta y cada KPI debe tener una acción asociada.",
        size=12.5,
        color=NAVY,
        line_spacing=1.02,
    )

    section_slide(prs, lay_section, "03", "Metodología", "Enfoque, pipeline y arquitectura de la solución")

    # Enfoque ----------------------------------------------------------------
    s = new("Enfoque metodológico")
    add_text(
        s,
        0.9,
        1.62,
        11.5,
        0.55,
        "Investigación aplicada, cuantitativa y descriptiva, con diseño no experimental y corte transversal.",
        size=12.5,
        color=TEXT,
    )
    chars = [
        ("Aplicada", "Resuelve un problema concreto de integración comercial."),
        ("Cuantitativa", "Trabaja con métricas, conteos y agregados verificables."),
        ("Descriptiva", "Caracteriza el universo de ventas y su calidad."),
        ("No experimental", "No manipula las variables; observa y depura el dato."),
        ("Transversal", "Cubre enero 2024 – agosto 2026 (32 meses)."),
    ]
    for i, (t, body) in enumerate(chars):
        x = 0.9 + i * 2.34
        add_rect(s, x, 2.4, 2.2, 2.55, WHITE, line=BORDER, radius=0.07)
        add_badge(s, x + 0.18, 2.56, 0.4, str(i + 1), fill=RED if i == 4 else NAVY, size=10.5)
        add_text(s, x + 0.18, 3.08, 1.85, 0.5, t, size=11.5, color=NAVY, bold=True)
        add_text(s, x + 0.18, 3.62, 1.85, 1.15, body, size=9.2, color=TEXT, line_spacing=1.0)
    add_rect(s, 0.9, 5.22, 11.53, 0.72, NAVY, line=None, radius=0.05)
    add_text(s, 1.12, 5.36, 11.0, 0.45, "CRISP-DM: negocio → datos → preparación → modelado → evaluación → despliegue.", size=11.5, color=WHITE, bold=True)
    add_text(
        s,
        0.9,
        6.12,
        11.53,
        0.5,
        "La metodología se adapta al examen complexivo: el énfasis está en la evidencia y en la reproducibilidad, no en la inferencia estadística.",
        size=9.5,
        color=GRAY,
        italic=True,
    )

    # Pipeline ---------------------------------------------------------------
    s = new("Pipeline ETL: siete etapas con control")
    steps = [
        ("1", "Extracción", "Copia a staging sin modificar el dato original."),
        ("2", "Perfilado", "Filas, claves, nulos, duplicados y rangos."),
        ("3", "Limpieza", "Tipos, espacios, fechas y duplicados exactos."),
        ("4", "Homologación", "Categorías, segmentos y vacíos a valor canónico."),
        ("5", "Validación", "FK, fechas, cantidades, precios y descuentos."),
        ("6", "Transformación", "Venta neta, costo total y margen."),
        ("7", "Carga", "Modelo estrella en SQLite y PostgreSQL."),
    ]
    for i, (num, name, desc) in enumerate(steps):
        col, row = i % 4, i // 4
        row_offset = 0.0 if row == 0 else 1.46
        x = 0.9 + row_offset + col * 2.92
        y = 1.66 + row * 1.95
        add_rect(s, x, y, 2.76, 1.72, LIGHT, line=BORDER, radius=0.07)
        add_plain_rect(s, x, y, 2.76, 0.06, RED if i == 6 else NAVY)
        add_badge(s, x + 0.16, y + 0.18, 0.38, num, fill=RED if i == 6 else NAVY, size=10.5)
        add_text(s, x + 0.62, y + 0.18, 2.0, 0.34, name, size=11.5, color=NAVY, bold=True)
        add_text(s, x + 0.16, y + 0.7, 2.45, 0.92, desc, size=9.2, color=TEXT, line_spacing=1.0)
    add_rect(s, 0.9, 5.68, 11.53, 0.75, WHITE, line=BORDER, radius=0.05)
    add_text(
        s,
        1.12,
        5.8,
        11.1,
        0.5,
        "Cada etapa deja un artefacto verificable: staging, profile_report, reglas, log_rechazos y quality_comparison.",
        size=10.5,
        color=GRAY,
        line_spacing=1.0,
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
    s = new("Modelo estrella: una tabla de hechos y cuatro dimensiones")
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

    # Diccionario de datos ---------------------------------------------------
    s = new("Diccionario de datos del data warehouse")
    data_tbl = [
        ["Tabla", "Grano / clave", "Campos principales", "Uso"],
        ["FactVentas", "Línea de venta", "cantidad, venta_neta, costo_total, margen", "KPIs y agregados"],
        ["DimTiempo", "Día", "fecha, año, mes, trimestre, semana", "Serie temporal"],
        ["DimCliente", "Cliente", "segmento, ciudad, provincia", "Segmentación"],
        ["DimProducto", "Producto", "categoría, marca, costo unitario", "Categorías y margen"],
        ["DimSucursal", "Sucursal", "ciudad, provincia, región", "Ranking territorial"],
    ]
    add_table(s, 0.9, 1.7, 11.53, data_tbl, [1.55, 2.2, 4.65, 3.13], row_h=0.55, font_size=10, header_size=10)
    add_rect(s, 0.9, 5.2, 11.53, 1.25, LIGHT, line=BORDER, radius=0.05)
    add_text(s, 1.12, 5.32, 2.4, 0.3, "REGLA DE ORO", size=9.5, color=GRAY_L, bold=True)
    add_text(
        s,
        1.12,
        5.62,
        11.1,
        0.72,
        "El grano se define antes de calcular: si una fila es una línea de venta, las transacciones se cuentan con COUNT(DISTINCT id_venta) y el ticket se calcula por transacción.",
        size=10.5,
        color=TEXT,
        line_spacing=1.0,
    )

    # Reglas de calidad ------------------------------------------------------
    s = new("Reglas de transformación y su efecto")
    rules = [
        ["Problema", "Regla aplicada", "Efecto"],
        ["Duplicados exactos", "Eliminar filas idénticas; conservar una por clave natural", "Evita doble conteo"],
        ["Fechas inválidas", "Parsear y excluir ventas sin fecha válida", "Serie temporal consistente"],
        ["Descuentos decimal/porcentaje", "Valores > 1 se dividen para 100", "Descuento entre 0 y 1"],
        ["Categorías mal escritas", "Homologar a catálogo canónico", "Una sola serie por categoría"],
        ["FK inexistente", "Registrar rechazo y excluir del hecho", "Sin ventas huérfanas"],
        ["Costo desconocido", "No imputar cero; margen desconocido", "No sobreestimar margen"],
    ]
    add_table(s, 0.9, 1.66, 11.53, rules, [2.5, 5.1, 3.93], row_h=0.52, font_size=9.8, header_size=10)
    add_text(
        s,
        0.9,
        5.9,
        11.53,
        0.6,
        "Cada regla se documenta con problema, criterio y efecto esperado; el log de rechazos conserva el detalle para corregir el origen.",
        size=10,
        color=GRAY,
        line_spacing=1.0,
    )

    # Trazabilidad -----------------------------------------------------------
    s = new("Trazabilidad y linaje: de la fuente al indicador")
    stages = [
        ("Fuente", "CSV / Excel / SQL", NAVY),
        ("Staging", "copia sin transformar", BLUE),
        ("Transformación", "limpieza + reglas", BLUE),
        ("FactVentas", "modelo estrella", NAVY),
        ("Vista KPI", "agregados", BLUE),
        ("Dashboard", "Superset", RED),
    ]
    for i, (t, sub, col) in enumerate(stages):
        x = 0.9 + i * 1.93
        add_rect(s, x, 1.9, 1.78, 1.15, WHITE, line=BORDER, radius=0.08)
        add_plain_rect(s, x, 1.9, 1.78, 0.06, col)
        add_text(s, x + 0.1, 2.05, 1.58, 0.3, t, size=10.5, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        add_text(s, x + 0.1, 2.4, 1.58, 0.5, sub, size=8.5, color=GRAY, align=PP_ALIGN.CENTER, line_spacing=1.0)
        if i < len(stages) - 1:
            add_text(s, x + 1.78, 2.32, 0.15, 0.3, "›", size=14, color=BLUE_L, bold=True)
    controls = [
        ("En staging: ", "profile_report: filas, nulos, claves y duplicados."),
        ("En transformación: ", "reglas_transformacion: problema, criterio y efecto."),
        ("En validación: ", "log_rechazos: motivo y fila excluida."),
        ("En carga: ", "consultas de control: SUM y COUNT(DISTINCT)."),
        ("En dashboard: ", "cuadre contra FactVentas y filtros interactivos."),
    ]
    add_rect(s, 0.9, 3.35, 11.53, 1.95, LIGHT, line=BORDER, radius=0.05)
    add_text(s, 1.12, 3.5, 4.0, 0.3, "CONTROLES EN CADA ETAPA", size=9.5, color=GRAY_L, bold=True)
    add_bullets(s, 1.12, 3.85, 11.0, 1.35, controls, size=10.5, bullet_color=BLUE, space_after=4)
    evidence = [
        ("profile_report", "perfil inicial de las cuatro fuentes", NAVY),
        ("quality_comparison", "antes y después del ETL", BLUE),
        ("log_rechazos", "50 filas con motivo documentado", RED),
    ]
    for i, (t, body, col) in enumerate(evidence):
        x = 0.9 + i * 3.92
        add_rect(s, x, 5.48, 3.76, 0.95, WHITE, line=BORDER, radius=0.06)
        add_plain_rect(s, x, 5.48, 0.06, 0.95, col)
        add_text(s, x + 0.18, 5.57, 3.4, 0.28, t, size=10.5, color=NAVY, bold=True)
        add_text(s, x + 0.18, 5.87, 3.4, 0.42, body, size=8.8, color=GRAY)
    add_text(
        s,
        0.9,
        6.6,
        11.53,
        0.3,
        "La trazabilidad permite reconstruir el recorrido de cualquier cifra publicada.",
        size=9.5,
        color=GRAY_L,
        italic=True,
    )

    section_slide(prs, lay_section, "04", "Resultados", "Calidad, indicadores y lectura comercial")

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
        color=TEXT,
        line_spacing=1.0,
    )

    # Rechazos y lectura -----------------------------------------------------
    s = new("Rechazos: qué se excluyó y por qué")
    add_picture_fit(s, charts["rechazos"], 0.8, 1.6, 6.6, 3.9)
    add_text(s, 7.65, 1.62, 4.75, 0.3, "LECTURA DE LA EXCLUSIÓN", size=9.5, color=GRAY_L, bold=True)
    add_bullets(
        s,
        7.65,
        1.98,
        4.75,
        4.1,
        [
            ("20 fechas inválidas: ", "no se puede ubicar la venta en el tiempo."),
            ("30 FK inválidas: ", "12 cliente, 10 producto y 8 sucursal inexistentes."),
            ("50 rechazos: ", "representan el 0,73 % de las 6.850 filas depuradas."),
            ("No se imputan: ", "no se inventan ventas ni dimensiones."),
            ("Riesgo: ", "si los rechazos se concentran, la comparación puede sesgarse."),
        ],
        size=10.5,
        bullet_color=RED,
        space_after=10,
    )
    add_rect(s, 0.9, 5.72, 11.53, 0.85, NAVY, line=None, radius=0.05)
    add_text(
        s,
        1.12,
        5.85,
        11.0,
        0.6,
        "Universo válido: 6.800 de 6.870 líneas (98,98 %). La exclusión reduce cobertura, pero evita distorsionar ingresos y margen.",
        size=10.5,
        color=WHITE,
        line_spacing=1.0,
    )

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

    # Evolución --------------------------------------------------------------
    s = new("Evolución mensual de las ventas netas")
    add_picture_fit(s, charts["evolucion"], 0.7, 1.55, 11.95, 3.75)
    stats = [
        ("32", "meses analizados"),
        ("232.881,96", "promedio mensual USD"),
        ("332.469,94", "máximo: enero 2026"),
        ("149.758,43", "mínimo: septiembre 2025"),
    ]
    for i, (v, lab) in enumerate(stats):
        x = 0.9 + i * 2.94
        add_rect(s, x, 5.55, 2.78, 0.95, LIGHT, line=BORDER, radius=0.07)
        add_text(s, x + 0.16, 5.64, 2.45, 0.34, v, size=14, color=NAVY, bold=True, font=TITLE_FONT)
        add_text(s, x + 0.16, 6.02, 2.45, 0.3, lab, size=8.5, color=GRAY)
    add_text(
        s,
        0.9,
        6.6,
        11.53,
        0.3,
        "No hay tendencia lineal: la serie combina picos de campaña y caídas estacionales; el promedio sirve de línea base.",
        size=9,
        color=GRAY_L,
        italic=True,
    )

    # Categorías y segmentos -------------------------------------------------
    s = new("Concentración por categoría y segmento")
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
        color=TEXT,
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
        color=TEXT,
        line_spacing=1.0,
    )

    # Sucursales -------------------------------------------------------------
    s = new("Desempeño por sucursal y región")
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

    # Canales y pagos --------------------------------------------------------
    s = new("Canales y medios de pago: una demanda equilibrada")
    add_picture_fit(s, charts["canal"], 0.75, 1.6, 5.85, 3.75)
    add_picture_fit(s, charts["pago"], 6.7, 1.6, 5.85, 3.75)
    add_text(s, 0.9, 5.45, 5.6, 0.3, "Participación por canal de venta", size=10, color=NAVY, bold=True)
    add_text(s, 6.85, 5.45, 5.6, 0.3, "Participación por medio de pago", size=10, color=NAVY, bold=True)
    add_rect(s, 0.9, 5.85, 11.53, 0.82, LIGHT, line=BORDER, radius=0.05)
    add_text(
        s,
        1.12,
        5.94,
        11.1,
        0.62,
        "Ningún canal supera el 25,5 % ni ningún medio de pago el 21,2 %: la operación no depende de un solo punto de contacto.",
        size=10.5,
        color=TEXT,
        line_spacing=1.0,
    )

    # Productos líderes ------------------------------------------------------
    s = new("Productos líderes y concentración del portafolio")
    prod = data["prod"]
    rows = [["Producto", "Categoría", "Ingresos (USD)", "Unidades"]]
    for p in prod:
        money = f"{p['ing']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        units = f"{p['uni']:,}".replace(",", ".")
        rows.append([p["nombre_producto"], p["categoria"], money, units])
    add_table(s, 0.9, 1.7, 7.45, rows, [3.15, 1.45, 1.65, 1.2], row_h=0.55, font_size=9.8, header_size=9.8)
    add_rect(s, 8.65, 1.7, 3.78, 3.9, NAVY, line=None, radius=0.05)
    add_text(s, 8.9, 1.88, 3.3, 0.3, "LECTURA DEL PORTAFOLIO", size=9.5, color=LIGHT2, bold=True)
    add_text(s, 8.9, 2.22, 3.3, 0.65, "148.826 USD", size=20, color=WHITE, bold=True, font=TITLE_FONT)
    add_text(s, 8.9, 2.82, 3.3, 0.5, "aporta el producto líder (2,0 % del total)", size=9, color=LIGHT2, line_spacing=1.0)
    add_text(
        s,
        8.9,
        3.42,
        3.3,
        1.9,
        "La concentración es baja: ningún producto supera el 2 % de los ingresos. El portafolio es amplio y la gestión debe mirar categorías, no solo productos estrella.",
        size=9.5,
        color=WHITE,
        line_spacing=1.02,
    )
    add_text(
        s,
        0.9,
        5.9,
        11.53,
        0.6,
        "Los cinco primeros productos pertenecen a Accesorios, Oficina y Tecnología; el margen se decide en la mezcla, no en un solo artículo.",
        size=10,
        color=GRAY,
        line_spacing=1.0,
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
        add_text(s, 8.18, y + 0.46, 4.05, 0.82, body, size=9.6, color=TEXT, line_spacing=1.0)
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
        "Los 50 rechazos se valorizan como pérdida estimada (cantidad × precio × (1 − descuento)). "
        "El descuento otorgado se analiza por categoría y se filtra por provincia desde el mapa.",
        size=9.6, color=GRAY_L, italic=True, line_spacing=1.0,
    )

    # Marcas y región --------------------------------------------------------
    s = new("Marcas líderes y peso de la región")
    add_picture_fit(s, charts["marca"], 0.65, 1.55, 6.55, 4.15)
    add_picture_fit(s, charts["region"], 7.45, 1.55, 4.75, 4.15)
    add_text(
        s, 0.8, 5.78, 11.6, 0.55,
        "Puma lidera la venta neta. La Sierra aporta 57,99 % de los ingresos y la Costa 42,01 %; "
        "el mapa distingue ambas regiones con el borde de color.",
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

    # Interpretación de KPIs -------------------------------------------------
    s = new("Razón de cada indicador: qué mide y para qué decide")
    kpi_tbl = [
        ["Indicador", "Fórmula sobre FactVentas", "Razón y uso gerencial"],
        ["Ingresos netos", "SUM(venta_neta)", "Valor real después de descuentos; base para comparar periodos."],
        ["Unidades vendidas", "SUM(cantidad)", "Volumen físico; separa precio de cantidad."],
        ["Margen bruto", "SUM(margen)", "Rentabilidad absoluta; evita confundir ingresos con ganancia."],
        ["Transacciones", "COUNT(DISTINCT id_venta)", "Actividad sin doble conteo: 6.800 líneas → 3.587 ventas."],
        ["Ticket promedio", "SUM(venta_neta) / COUNT(DISTINCT id_venta)", "Valor medio por venta, sin sesgo por líneas."],
        ["Margen %", "SUM(margen) / SUM(venta_neta)", "Eficiencia relativa (26,39 %), comparable entre áreas."],
        ["Descuento otorgado", "SUM(venta_bruta − venta_neta)", "Monto cedido; se analiza por categoría y provincia."],
        ["Pérdida por rechazos", "SUM(venta_perdida) en fact_rechazos", "Venta estimada no integrada; se monitorea por sucursal y fecha."],
    ]
    add_table(s, 0.9, 1.62, 11.53, kpi_tbl, [1.65, 3.55, 6.33], row_h=0.49, font_size=8.8, header_size=9.2)
    add_text(
        s,
        0.9,
        5.95,
        11.53,
        0.55,
        "Cada KPI tiene una fórmula única y una decisión asociada; si cambia la definición, cambia la lectura del negocio.",
        size=10,
        color=GRAY,
        line_spacing=1.0,
    )

    # Hallazgos del desarrollo ----------------------------------------------
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
        add_text(s, 1.56, y + 0.16, 5.2, 0.35, t, size=10.8, color=TEXT)
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

    section_slide(prs, lay_section, "05", "Discusión y cierre", "Qué demuestra la PoC y qué falta para producción")

    # Discusión --------------------------------------------------------------
    s = new("Discusión: hallazgos y limitaciones")
    add_rect(s, 0.9, 1.62, 5.78, 4.95, WHITE, line=BORDER, radius=0.05)
    add_text(s, 1.12, 1.78, 5.3, 0.3, "HALLAZGOS", size=10, color=GRAY_L, bold=True)
    hall = [
        ("La calidad cambia el universo.", " 70 de 6.870 líneas (1,02 %) no eran integrables; se evitaron ventas sin dimensión válida."),
        ("Ventas concentradas.", " Accesorios y Hogar 40,39 %; Masivo 50,85 %; Sierra 57,99 %."),
        ("El margen matiza el ranking.", " La categoría líder en ventas no es necesariamente la más rentable."),
    ]
    for i, (lead, rest) in enumerate(hall):
        y = 2.2 + i * 1.4
        add_badge(s, 1.12, y, 0.4, str(i + 1), fill=NAVY, size=10.5)
        add_text(s, 1.66, y - 0.02, 4.8, 1.2, lead + rest, size=10.8, color=TEXT, line_spacing=1.02)
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
        add_text(s, x + 0.86, y + 0.68, 4.55, 1.1, body, size=10.8, color=TEXT, line_spacing=1.02)
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
        add_text(s, x + 0.18, y + 0.72, w - 0.34, h - 0.8, txt, size=9.8, color=TEXT, line_spacing=1.02)
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

    section_slide(prs, lay_section, "06", "Glosario y preguntas", "Conceptos clave y simulación de jurado")

    # Glosario 1 -------------------------------------------------------------
    glossaries = [
        (
            "Glosario: datos y ETL",
            [
                ("ETL", "Extraer, transformar y cargar datos desde fuentes heterogéneas hacia un repositorio analítico."),
                ("Staging", "Zona intermedia donde se copia el dato original sin modificarlo, para poder auditarlo."),
                ("Data warehouse", "Repositorio central, organizado por procesos de negocio, que alimenta los indicadores."),
                ("Modelo estrella", "Esquema con una tabla de hechos al centro y dimensiones alrededor."),
                ("Hecho", "Tabla con métricas del negocio y claves hacia dimensiones."),
                ("Grano", "Nivel de detalle de una fila del hecho; aquí, una línea de venta."),
            ],
        ),
        (
            "Glosario: calidad de datos",
            [
                ("Exactitud", "El dato coincide con la realidad o con la fuente autorizada."),
                ("Completitud", "No faltan valores necesarios para el análisis."),
                ("Consistencia", "El mismo dato mantiene formato y significado entre fuentes."),
                ("Unicidad", "No hay registros duplicados para una misma clave."),
                ("Integridad referencial", "Toda clave foránea existe en su dimensión; si no, se rechaza."),
                ("Homologación", "Variantes de escritura se unifican en un valor canónico."),
            ],
        ),
        (
            "Glosario: indicadores y negocio",
            [
                ("KPI", "Indicador clave con fórmula estable y reproducible para medir un objetivo."),
                ("Venta neta", "cantidad × precio × (1 − descuento); ingreso real después del descuento."),
                ("Margen bruto", "Venta neta − costo total; rentabilidad absoluta."),
                ("Ticket promedio", "Ingreso neto / número de transacciones."),
                ("Margen %", "Margen bruto / ingreso neto; eficiencia relativa."),
                ("Transacción", "Operación comercial única (id_venta); puede tener varias líneas."),
            ],
        ),
        (
            "Glosario: tecnologías y método",
            [
                ("pandas", "Librería de Python para leer, limpiar y transformar datos."),
                ("SQLite", "Base de datos ligera en archivo, usada para la evidencia local."),
                ("PostgreSQL", "Base de datos relacional usada por el data warehouse y Superset."),
                ("Apache Superset", "Herramienta de BI para construir dashboards interactivos."),
                ("Docker", "Empaqueta la aplicación y sus dependencias para ejecutarla igual en cualquier entorno."),
                ("CRISP-DM", "Método: negocio, datos, preparación, modelado, evaluación y despliegue."),
            ],
        ),
    ]
    for title, terms in glossaries:
        s = new(title)
        x0, y0, w, h, gx, gy = 0.9, 1.62, 5.68, 1.52, 0.17, 0.16
        for i, (term, definition) in enumerate(terms):
            col, row = i % 2, i // 2
            x = x0 + col * (w + gx)
            y = y0 + row * (h + gy)
            add_rect(s, x, y, w, h, WHITE, line=BORDER, radius=0.07)
            add_plain_rect(s, x, y, 0.07, h, RED if i % 3 == 2 else NAVY)
            add_text(s, x + 0.22, y + 0.13, w - 0.4, 0.3, term, size=12, color=NAVY, bold=True)
            add_text(s, x + 0.22, y + 0.46, w - 0.4, h - 0.52, definition, size=9.6, color=TEXT, line_spacing=1.0)

    # Q&A intro --------------------------------------------------------------
    s = new("Preguntas y respuestas")
    add_text(s, 0.9, 1.72, 11.5, 0.5, "Simulación de jurado: 12 preguntas probables y sus respuestas", size=13, color=GRAY)
    add_rect(s, 0.9, 2.42, 11.53, 2.05, LIGHT, line=BORDER, radius=0.05)
    add_text(s, 1.2, 2.56, 10.9, 0.4, "CÓMO USAR ESTE BLOQUE", size=9.5, color=GRAY_L, bold=True)
    add_bullets(
        s,
        1.2,
        2.92,
        10.9,
        1.4,
        [
            "Cada pregunta tiene una respuesta breve y una idea de respaldo.",
            "Si el jurado pide más detalle, recurrir al informe y a los anexos.",
            "Mantener la respuesta en 30–45 segundos y volver al mensaje central.",
            "No defender cifras sin fuente: la trazabilidad es parte de la respuesta.",
        ],
        size=10.5,
        space_after=4,
    )
    topics = [
        ("Arquitectura", "modelo, grano y SQL"),
        ("Calidad", "reglas, rechazos y control"),
        ("Indicadores", "fórmulas y lectura"),
        ("Operación", "despliegue y límites"),
    ]
    for i, (t, body) in enumerate(topics):
        x = 0.9 + i * 2.92
        add_rect(s, x, 4.78, 2.76, 1.35, WHITE, line=BORDER, radius=0.07)
        add_plain_rect(s, x, 4.78, 2.76, 0.06, RED if i == 3 else NAVY)
        add_text(s, x + 0.18, 4.94, 2.4, 0.3, t, size=12, color=NAVY, bold=True)
        add_text(s, x + 0.18, 5.28, 2.4, 0.7, body, size=9.5, color=GRAY, line_spacing=1.0)

    # Q&A --------------------------------------------------------------------
    qa = [
        ("¿Por qué usar un esquema estrella y no un modelo normalizado?", [
            "BI prioriza consultas de agregación, no transacciones.",
            "Menos joins: una tabla de hechos y cuatro dimensiones.",
            "El negocio entiende el modelo y los KPIs son reproducibles.",
            "La normalización se reserva para sistemas transaccionales.",
        ]),
        ("¿Cómo garantiza que las cifras del dashboard son correctas?", [
            "Reglas de negocio documentadas y aplicadas en el ETL.",
            "Auditoría fuente → staging → FactVentas → dashboard.",
            "Totales idénticos: 7.452.222,71 USD; 13.817; 1.966.780,12 USD; 3.587.",
            "El log de rechazos explica cada fila excluida.",
        ]),
        ("¿Qué pasa con las filas descartadas? ¿No sesga el análisis?", [
            "20 duplicados, 30 FK inválidas y 20 fechas inválidas: 70 filas.",
            "No se imputan: no se inventan ventas ni dimensiones.",
            "Universo válido: 6.800 de 6.870 líneas (98,98 %).",
            "La tasa de rechazo se monitorea; si crece, se corrige el origen.",
        ]),
        ("¿Por qué COUNT(DISTINCT id_venta) y no COUNT(*)?", [
            "El grano es la línea de venta: una venta puede tener varios productos.",
            "COUNT(*) contaría 6.800 líneas, no ventas.",
            "COUNT(DISTINCT id_venta) devuelve 3.587 transacciones reales.",
            "Así el ticket promedio no se sesga.",
        ]),
        ("¿Cómo calculó el margen si hay costos desconocidos?", [
            "No se imputó costo cero: eso sobreestimaría el margen.",
            "Si el costo falta, el margen queda desconocido.",
            "En esta fuente los 120 productos tienen costo.",
            "La marca faltante no interviene en el cálculo.",
        ]),
        ("¿Por qué Apache Superset y no Power BI?", [
            "Superset es open source y se despliega con Docker/Northflank.",
            "Se conecta directo a PostgreSQL sin licencias.",
            "Power BI se usó como respaldo local con SQLite.",
            "La elección prioriza reproducibilidad y costo.",
        ]),
        ("¿Cómo se ejecuta y despliega el proyecto?", [
            "Local: python 02_etl/main.py y build_dashboard.py.",
            "Docker Compose: Jupyter, PostgreSQL, ETL y Superset.",
            "Nube: job ETL en Northflank + Superset sobre Neon.",
            "El dashboard HTML se sirve como evidencia estática.",
        ]),
        ("¿Qué diferencia hay entre SQLite y PostgreSQL?", [
            "SQLite: archivo local dw.db para notebook y Power BI.",
            "PostgreSQL: motor del dashboard Superset.",
            "PostgreSQL soporta concurrencia, usuarios y red.",
            "Ambos usan el mismo esquema estrella y las mismas reglas.",
        ]),
        ("¿Cómo midió la calidad de datos?", [
            "Dimensiones: exactitud, completitud, consistencia, unicidad e integridad.",
            "Perfil inicial de las cuatro fuentes.",
            "Comparación antes/después y log de rechazos.",
            "Cada regla tiene problema, criterio y efecto documentado.",
        ]),
        ("¿Qué limitaciones tiene la PoC?", [
            "Datos académicos y sintéticos: no generalizar a una empresa real.",
            "Carga batch, no incremental.",
            "Sin inferencia estadística ni modelos predictivos.",
            "Rentabilidad limitada al margen bruto.",
        ]),
        ("¿Qué es el grano y por qué importa?", [
            "Es el nivel de detalle de cada fila del hecho.",
            "Aquí: una línea de venta.",
            "Definirlo evita doble conteo y hace consistentes los KPIs.",
            "Permite separar líneas de transacciones.",
        ]),
        ("¿Cómo homologó categorías y valores vacíos?", [
            "Catálogo canónico: TECNOLOGÍA/TECNOLOGIA/tecnología → Tecnología.",
            "Segmento vacío → Sin segmento.",
            "Canal y método vacíos → No especificado.",
            "Evita que una categoría se parta en varias series.",
        ]),
    ]
    qa_keys = [
        ("4 dimensiones", "Una tabla de hechos y cuatro dimensiones: menos joins y KPIs legibles."),
        ("7.452.222,71 USD", "Total auditado; coincide con la fuente, FactVentas y el dashboard."),
        ("98,98 %", "Cobertura del universo válido; 50 rechazos documentados."),
        ("3.587", "Transacciones reales; COUNT(*) daría 6.800 líneas."),
        ("120", "Productos con costo; no se imputa costo cero."),
        ("Open source", "Sin licencias y desplegable con Docker/Northflank."),
        ("3 entornos", "Local, Docker Compose y nube (Northflank + Neon)."),
        ("2 motores", "SQLite y PostgreSQL con el mismo esquema estrella."),
        ("5 dimensiones", "Exactitud, completitud, consistencia, unicidad e integridad."),
        ("32 meses", "Alcance enero 2024 – agosto 2026."),
        ("1,90", "Líneas por transacción; el grano es la línea de venta."),
        ("5 categorías", "Catálogo canónico; los vacíos se hicieron explícitos."),
    ]
    for i, ((question, answers), (keyv, keyl)) in enumerate(zip(qa, qa_keys), start=1):
        s = new(f"Pregunta {i} de 12")
        add_rect(s, 0.9, 1.62, 11.53, 1.1, NAVY, line=None, radius=0.05)
        add_text(s, 1.15, 1.78, 10.9, 0.8, question, size=15, color=WHITE, bold=True, line_spacing=1.0)
        add_text(s, 0.9, 2.95, 2.2, 0.26, "RESPUESTA", size=9.5, color=GRAY_L, bold=True)
        add_bullets(s, 0.9, 3.32, 11.3, 2.35, answers, size=12.5, bullet_color=RED, space_after=9)
        add_rect(s, 0.9, 5.9, 11.53, 0.8, LIGHT, line=BORDER, radius=0.05)
        add_plain_rect(s, 0.9, 5.9, 0.07, 0.8, RED)
        add_text(s, 1.12, 5.97, 2.2, 0.24, "DATO CLAVE", size=8.5, color=GRAY_L, bold=True)
        add_text(s, 1.12, 6.2, 2.4, 0.35, keyv, size=12.5, color=NAVY, bold=True)
        add_text(s, 3.55, 6.04, 8.65, 0.55, keyl, size=9.8, color=TEXT, line_spacing=1.0)


    closing_slide(prs, lay_title, title_bg)
    return prs

