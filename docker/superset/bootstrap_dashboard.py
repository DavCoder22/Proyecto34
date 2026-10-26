"""Crea el dashboard Sales Analytics en Superset a partir del DW PostgreSQL.

Se ejecuta dentro del contenedor de Superset después de `superset init`.
Es idempotente: si el dashboard ya existe, no hace nada.
"""
import json
import os
import time
import uuid

from flask import g
from sqlalchemy import inspect, text

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

DATASETS = {
    "v_ventas_mes": {
        "main_dttm_col": "fecha",
        "metrics": [("sum_venta_neta", "SUM(venta_neta)")],
    },
    "v_ventas_categoria": {
        "metrics": [("sum_venta_neta", "SUM(venta_neta)")],
    },
    "v_ventas_sucursal": {
        "metrics": [("sum_venta_neta", "SUM(venta_neta)")],
    },
    "v_ventas_segmento": {
        "metrics": [("sum_venta_neta", "SUM(venta_neta)")],
    },
}


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
    while time.time() < deadline:
        try:
            with database.get_sqla_engine_with_context() as engine:
                schema = inspect(engine).default_schema_name or "public"
                with engine.connect() as connection:
                    for view in DATASETS:
                        connection.execute(text(f"SELECT 1 FROM {view} LIMIT 1"))
                return schema
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
        "color_scheme": "supersetColors",
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
        "color_scheme": "supersetColors",
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


def _chart_component(component_id, slice_obj, row_id, width):
    return {
        "children": [],
        "id": component_id,
        "meta": {
            "chartId": slice_obj.id,
            "height": 50,
            "sliceName": slice_obj.slice_name,
            "uuid": str(slice_obj.uuid),
            "width": width,
        },
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "type": "CHART",
    }


def _create_dashboard(slices, admin):
    line_slice, category_slice, branch_slice, segment_slice = slices
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {
            "children": ["GRID_ID"],
            "id": "ROOT_ID",
            "type": "ROOT",
        },
        "GRID_ID": {
            "children": ["ROW-LINE", "ROW-BARS"],
            "id": "GRID_ID",
            "parents": ["ROOT_ID"],
            "type": "GRID",
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "meta": {"text": DASHBOARD_TITLE},
            "type": "HEADER",
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
    metadata = {
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "default_filters": "{}",
        "color_scheme": "supersetColors",
        "label_colors": {},
        "native_filter_configuration": [],
    }
    dashboard = Dashboard(
        dashboard_title=DASHBOARD_TITLE,
        slug=DASHBOARD_SLUG,
        position_json=json.dumps(position, indent=4),
        json_metadata=json.dumps(metadata),
        published=True,
    )
    dashboard.slices = list(slices)
    if admin is not None:
        dashboard.owners = [admin]
    db.session.add(dashboard)
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
        if existing is not None and not FORCE:
            print("[bootstrap] El dashboard Sales Analytics ya existe; se omite.")
            return
        if existing is not None:
            print("[bootstrap] Eliminando dashboard anterior por SUPERSET_BOOTSTRAP_FORCE.")
            db.session.delete(existing)
            db.session.commit()

        database = _get_database()
        schema = _wait_for_views(database)

        tables = {
            view: _get_dataset(database, schema, view) for view in DATASETS
        }

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

        _create_dashboard([line, category, branch, segment], admin)
        print("[bootstrap] Dashboard Sales Analytics creado correctamente.")


if __name__ == "__main__":
    main()
