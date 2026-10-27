"""Crea el dashboard Sales Analytics en Superset a partir del DW PostgreSQL.

Se ejecuta dentro del contenedor de Superset después de `superset init`.
Es idempotente: reutiliza datasets, métricas y gráficos existentes y actualiza
el dashboard con los KPIs y la disposición vigente.
"""
import json
import os
import time
import uuid
from pathlib import Path

from flask import g
from sqlalchemy import inspect

from superset.app import create_app

db = None
security_manager = None
SqlaTable = None
SqlMetric = None
Database = None
Dashboard = None
Slice = None

DASHBOARD_SLUG = "sales-analytics"
DASHBOARD_TITLE = "Sales Analytics"
DATABASE_NAME = os.environ.get("SUPERSET_DW_DATABASE_NAME", "PoC DW")


def _normalize_postgres_url(value):
    value = value.strip()
    if value.startswith("postgres://"):
        return "postgresql+psycopg2://" + value[len("postgres://"):]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg2://" + value[len("postgresql://"):]
    return value


DATABASE_URL = _normalize_postgres_url(
    os.environ.get("SUPERSET_DW_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or ""
)
FORCE = os.environ.get("SUPERSET_BOOTSTRAP_FORCE", "").strip().lower() in {
    "1", "true", "yes", "on",
}
ADMIN_USERNAME = os.environ.get("SUPERSET_ADMIN_USER", "admin")
SUM_VENTA_NETA = "SUM(venta_neta)"
COLOR_SCHEME = "uceColors"

DATASETS = {
    "v_ventas_mes": {
        "main_dttm_col": "fecha",
        "metrics": [("sum_venta_neta", SUM_VENTA_NETA)],
    },
    "v_ventas_categoria": {
        "metrics": [("sum_venta_neta", SUM_VENTA_NETA)],
    },
    "v_ventas_sucursal": {
        "metrics": [("sum_venta_neta", SUM_VENTA_NETA)],
    },
    "v_ventas_segmento": {
        "metrics": [("sum_venta_neta", SUM_VENTA_NETA)],
    },
    "v_kpis_consolidados": {
        "metrics": [
            ("kpi_ingresos", "MAX(ingresos)"),
            ("kpi_unidades", "MAX(unidades)"),
            ("kpi_margen", "MAX(margen)"),
            ("kpi_transacciones", "MAX(transacciones)"),
            ("kpi_ticket_promedio", "MAX(ticket_promedio)"),
            ("kpi_margen_pct", "MAX(margen_pct)"),
        ],
    },
}

KPI_CARDS = [
    (
        "Ingresos Netos",
        "kpi_ingresos",
        "$,.2f",
        "USD · universo validado",
        "CHART-KPI-INGRESOS",
    ),
    (
        "Unidades Vendidas",
        "kpi_unidades",
        ",.0f",
        "unidades · datos integrados",
        "CHART-KPI-UNIDADES",
    ),
    (
        "Margen Bruto",
        "kpi_margen",
        "$,.2f",
        "rentabilidad absoluta",
        "CHART-KPI-MARGEN",
    ),
    (
        "Transacciones",
        "kpi_transacciones",
        ",.0f",
        "ventas únicas",
        "CHART-KPI-TRANSACCIONES",
    ),
    (
        "Ticket Promedio",
        "kpi_ticket_promedio",
        "$,.2f",
        "USD por transacción",
        "CHART-KPI-TICKET",
    ),
    (
        "Margen %",
        "kpi_margen_pct",
        ".2%",
        "margen sobre ingresos netos",
        "CHART-KPI-MARGEN-PCT",
    ),
]


def _import_superset():
    global db, security_manager, SqlaTable, SqlMetric, Database, Dashboard, Slice
    from superset import db as superset_db
    from superset import security_manager as superset_security_manager
    from superset.connectors.sqla.models import (
        SqlaTable as SupersetTable,
        SqlMetric as SupersetMetric,
    )
    from superset.models.core import Database as SupersetDatabase
    from superset.models.dashboard import Dashboard as SupersetDashboard
    from superset.models.slice import Slice as SupersetSlice

    db = superset_db
    security_manager = superset_security_manager
    SqlaTable = SupersetTable
    SqlMetric = SupersetMetric
    Database = SupersetDatabase
    Dashboard = SupersetDashboard
    Slice = SupersetSlice


def _chart_uuid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"poc-superset:{name}"))


def _wait_for_views(database, timeout=180):
    deadline = time.time() + timeout
    last_error = None
    views_sql = Path("/app/kpi_views_postgres.sql")
    while time.time() < deadline:
        try:
            with database.get_sqla_engine_with_context() as engine:
                inspector = inspect(engine)
                schema = inspector.default_schema_name or "public"
                names = set(inspector.get_view_names(schema=schema))
                names.update(inspector.get_table_names(schema=schema))
                missing = sorted(set(DATASETS) - names)
                if not missing:
                    return schema
                if views_sql.exists():
                    print(
                        "[bootstrap] Creando vistas KPI faltantes: "
                        + ", ".join(missing)
                    )
                    with engine.begin() as connection:
                        connection.exec_driver_sql(
                            views_sql.read_text(encoding="utf-8")
                        )
                raise RuntimeError(f"Vistas pendientes: {', '.join(missing)}")
        except Exception as exc:  # pragma: no cover - depende del entorno
            last_error = exc
            print(f"[bootstrap] Esperando vistas KPI en PostgreSQL: {exc}")
            time.sleep(3)
    raise RuntimeError(f"No se pudieron leer las vistas KPI: {last_error}")


def _get_database():
    database = db.session.query(Database).filter_by(database_name=DATABASE_NAME).first()
    if database is None:
        database = Database(
            database_name=DATABASE_NAME,
            sqlalchemy_uri=DATABASE_URL,
            expose_in_sqllab=True,
        )
        db.session.add(database)
    else:
        database.set_sqlalchemy_uri(DATABASE_URL)
        database.expose_in_sqllab = True
    db.session.commit()
    return database


def _get_dataset(database, schema, view):
    table = (
        db.session.query(SqlaTable)
        .filter_by(table_name=view, schema=schema)
        .first()
    )
    if table is None:
        table = SqlaTable(table_name=view, schema=schema)
        db.session.add(table)

    table.database = database
    table.filter_select_enabled = True
    table.fetch_metadata()

    spec = DATASETS[view]
    if spec.get("main_dttm_col"):
        table.main_dttm_col = spec["main_dttm_col"]
        for column in table.columns:
            if column.column_name == spec["main_dttm_col"]:
                column.is_dttm = True

    existing_metrics = {metric.metric_name for metric in table.metrics}
    for metric_name, expression in spec["metrics"]:
        if metric_name not in existing_metrics:
            table.metrics.append(
                SqlMetric(metric_name=metric_name, expression=expression)
            )
    db.session.commit()
    return table


def _line_params(table):
    return {
        "adhoc_filters": [],
        "annotation_layers": [],
        "bottom_margin": "auto",
        "color_scheme": COLOR_SCHEME,
        "comparison_type": "values",
        "contribution": False,
        "datasource": f"{table.id}__table",
        "granularity_sqla": "fecha",
        "groupby": [],
        "left_margin": "auto",
        "line_interpolation": "linear",
        "metrics": ["sum_venta_neta"],
        "order_desc": True,
        "rich_tooltip": True,
        "rolling_type": "None",
        "row_limit": 10000,
        "show_brush": "auto",
        "show_legend": True,
        "show_markers": False,
        "time_grain_sqla": "P1M",
        "time_range": "No filter",
        "url_params": {},
        "viz_type": "line",
        "x_axis_format": "smart_date",
        "x_axis_label": "Fecha",
        "y_axis_format": "SMART_NUMBER",
        "y_axis_label": "Ventas netas (USD)",
    }


def _bar_params(table, groupby, x_label):
    return {
        "adhoc_filters": [],
        "annotation_layers": [],
        "bar_stacked": False,
        "bottom_margin": "auto",
        "color_scheme": COLOR_SCHEME,
        "contribution": False,
        "datasource": f"{table.id}__table",
        "granularity_sqla": None,
        "groupby": [groupby],
        "left_margin": "auto",
        "metrics": ["sum_venta_neta"],
        "order_desc": True,
        "row_limit": 100,
        "show_legend": True,
        "time_range": "No filter",
        "url_params": {},
        "viz_type": "dist_bar",
        "x_axis_label": x_label,
        "y_axis_format": "SMART_NUMBER",
        "y_axis_label": "Ventas netas (USD)",
    }


def _big_number_params(table, metric, subheader, number_format):
    return {
        "adhoc_filters": [],
        "datasource": f"{table.id}__table",
        "header_font_size": 0.4,
        "metric": metric,
        "queryFields": {"metric": "metrics"},
        "subheader": subheader,
        "subheader_font_size": 0.125,
        "time_range": "No filter",
        "url_params": {},
        "viz_type": "big_number_total",
        "y_axis_format": number_format,
    }


def _get_slice(name, table, viz_type, params, admin):
    slice_obj = db.session.query(Slice).filter_by(slice_name=name).first()
    if slice_obj is None:
        slice_obj = Slice(
            slice_name=name,
            datasource_type="table",
            datasource_id=table.id,
            viz_type=viz_type,
            uuid=_chart_uuid(name),
        )
        db.session.add(slice_obj)

    slice_obj.datasource_type = "table"
    slice_obj.datasource_id = table.id
    slice_obj.datasource_name = f"{table.schema}.{table.table_name}" if table.schema else table.table_name
    slice_obj.viz_type = viz_type
    slice_obj.params = json.dumps(params, indent=4, sort_keys=True)
    if admin is not None:
        slice_obj.owners = [admin]

    db.session.flush()
    params["slice_id"] = slice_obj.id
    slice_obj.params = json.dumps(params, indent=4, sort_keys=True)
    return slice_obj


def _chart_component(component_id, slice_obj, row_id, width, height=50):
    return {
        "children": [],
        "id": component_id,
        "meta": {
            "chartId": slice_obj.id,
            "height": height,
            "sliceName": slice_obj.slice_name,
            "uuid": str(slice_obj.uuid),
            "width": width,
        },
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "type": "CHART",
    }


def _create_dashboard(kpi_slices, chart_slices, admin, dashboard=None):
    line_slice, category_slice, branch_slice, segment_slice = chart_slices
    kpi_components = [
        _chart_component(component_id, slice_obj, "ROW-KPI-1" if index < 3 else "ROW-KPI-2", 4, 28)
        for index, (slice_obj, component_id) in enumerate(kpi_slices)
    ]
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {
            "children": ["GRID_ID"],
            "id": "ROOT_ID",
            "type": "ROOT",
        },
        "GRID_ID": {
            "children": ["ROW-KPI-1", "ROW-KPI-2", "ROW-LINE", "ROW-BARS"],
            "id": "GRID_ID",
            "parents": ["ROOT_ID"],
            "type": "GRID",
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "meta": {"text": DASHBOARD_TITLE},
            "type": "HEADER",
        },
        "ROW-KPI-1": {
            "children": [component["id"] for component in kpi_components[:3]],
            "id": "ROW-KPI-1",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "ROW-KPI-2": {
            "children": [component["id"] for component in kpi_components[3:]],
            "id": "ROW-KPI-2",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "ROW-LINE": {
            "children": ["CHART-LINE"],
            "id": "ROW-LINE",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "CHART-LINE": _chart_component("CHART-LINE", line_slice, "ROW-LINE", 12),
        "ROW-BARS": {
            "children": ["CHART-CATEGORY", "CHART-BRANCH", "CHART-SEGMENT"],
            "id": "ROW-BARS",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "CHART-CATEGORY": _chart_component(
            "CHART-CATEGORY", category_slice, "ROW-BARS", 4
        ),
        "CHART-BRANCH": _chart_component(
            "CHART-BRANCH", branch_slice, "ROW-BARS", 4
        ),
        "CHART-SEGMENT": _chart_component(
            "CHART-SEGMENT", segment_slice, "ROW-BARS", 4
        ),
    }
    for component in kpi_components:
        position[component["id"]] = component

    metadata = {
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "default_filters": "{}",
        "color_scheme": COLOR_SCHEME,
        "label_colors": {},
        "native_filter_configuration": [],
    }
    if dashboard is None:
        dashboard = Dashboard(
            dashboard_title=DASHBOARD_TITLE,
            slug=DASHBOARD_SLUG,
        )
        db.session.add(dashboard)

    dashboard.dashboard_title = DASHBOARD_TITLE
    dashboard.slug = DASHBOARD_SLUG
    dashboard.position_json = json.dumps(position, indent=4)
    dashboard.json_metadata = json.dumps(metadata)
    dashboard.published = True
    dashboard.slices = [
        slice_obj for slice_obj, _ in kpi_slices
    ] + list(chart_slices)
    if admin is not None:
        dashboard.owners = [admin]
    db.session.commit()
    return dashboard


def main():
    if not DATABASE_URL:
        print("[bootstrap] Sin DATABASE_URL: no se crea el dashboard.")
        return

    app = create_app()
    with app.app_context():
        _import_superset()
        admin = security_manager.find_user(username=ADMIN_USERNAME)
        if admin is not None:
            g.user = admin

        existing = (
            db.session.query(Dashboard).filter_by(slug=DASHBOARD_SLUG).first()
        )
        if existing is not None and FORCE:
            print("[bootstrap] Eliminando dashboard anterior por SUPERSET_BOOTSTRAP_FORCE.")
            db.session.delete(existing)
            db.session.commit()
            existing = None

        database = _get_database()
        schema = _wait_for_views(database)

        tables = {
            view: _get_dataset(database, schema, view) for view in DATASETS
        }

        kpi_slices = []
        for title, metric, number_format, subheader, component_id in KPI_CARDS:
            slice_obj = _get_slice(
                title,
                tables["v_kpis_consolidados"],
                "big_number_total",
                _big_number_params(
                    tables["v_kpis_consolidados"],
                    metric,
                    subheader,
                    number_format,
                ),
                admin,
            )
            kpi_slices.append((slice_obj, component_id))

        line = _get_slice(
            "Evolución de Ventas",
            tables["v_ventas_mes"],
            "line",
            _line_params(tables["v_ventas_mes"]),
            admin,
        )
        category = _get_slice(
            "Ventas por Categoría",
            tables["v_ventas_categoria"],
            "dist_bar",
            _bar_params(tables["v_ventas_categoria"], "categoria", "Categoría"),
            admin,
        )
        branch = _get_slice(
            "Desempeño por Sucursal",
            tables["v_ventas_sucursal"],
            "dist_bar",
            _bar_params(tables["v_ventas_sucursal"], "nombre_sucursal", "Sucursal"),
            admin,
        )
        segment = _get_slice(
            "Ventas por Segmento",
            tables["v_ventas_segmento"],
            "dist_bar",
            _bar_params(tables["v_ventas_segmento"], "segmento", "Segmento"),
            admin,
        )
        db.session.commit()

        _create_dashboard(
            kpi_slices,
            [line, category, branch, segment],
            admin,
            dashboard=existing,
        )
        print("[bootstrap] Dashboard Sales Analytics creado/actualizado correctamente.")


if __name__ == "__main__":
    main()
