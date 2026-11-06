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

DASHBOARD_CSS = """
/* Tema empresarial UCE */
body, .dashboard { background: #eef2f9 !important; }

/* Barra superior */
header#main-menu.top {
  background: linear-gradient(90deg, #002b87 0%, #0033A0 60%, #0b49c9 100%) !important;
  border-top: 4px solid #CE1126 !important;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .18) !important;
}
header#main-menu .navbar-brand img { height: 38px !important; width: auto !important; }
header#main-menu .main-nav,
header#main-menu .ant-menu { background: transparent !important; border-bottom: 0 !important; }
header#main-menu .ant-menu-item a,
header#main-menu .ant-menu-submenu-title,
header#main-menu .ant-menu-item .anticon { color: #fff !important; font-weight: 600 !important; }
header#main-menu .ant-menu-item-selected,
header#main-menu .ant-menu-item:hover,
header#main-menu .ant-menu-submenu-title:hover {
  background: rgba(255, 255, 255, .14) !important;
  border-bottom: 3px solid #CE1126 !important;
}
header#main-menu .ant-menu-item-selected a { color: #fff !important; }
header#main-menu .ant-btn,
header#main-menu .anticon { color: #fff !important; }
header#main-menu .ant-btn-text:hover { background: rgba(255, 255, 255, .14) !important; }

/* Encabezado del dashboard */
.dashboard-header-container {
  background: linear-gradient(90deg, #0033A0 0%, #0033A0 65%, #CE1126 100%) !important;
  padding: 18px 24px 20px !important;
  border-radius: 0 0 18px 18px !important;
  box-shadow: 0 10px 26px rgba(0, 51, 160, .22) !important;
}
.dashboard-header-container .header-with-actions {
  background: transparent !important;
  box-shadow: none !important;
}
.dashboard-header-container .dynamic-title,
.dashboard-header-container .editable-title,
.dashboard-header-container .header-title {
  color: #fff !important;
  font-weight: 800 !important;
  letter-spacing: .2px;
}
.dashboard-header-container .dynamic-title::after {
  content: " · UCE";
  color: #ffd7dc;
  font-weight: 600;
}
.dashboard-header-container .ant-tag {
  background: rgba(255, 255, 255, .18) !important;
  color: #fff !important;
  border: 0 !important;
}
.dashboard-header-container .ant-btn.superset-button,
.dashboard-header-container .action-button {
  background: #fff !important;
  color: #0033A0 !important;
  border: 0 !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
}
.dashboard-header-container .ant-btn.superset-button:hover,
.dashboard-header-container .action-button:hover { background: #eef3ff !important; }
.dashboard-header-container .ant-btn.superset-button .anticon,
.dashboard-header-container .ant-btn.action-button .anticon { color: #0033A0 !important; }
.dashboard-header-container .fave-unfave-icon,
.dashboard-header-container .fave-unfave-icon span,
.dashboard-header-container .anticon { color: #fff !important; }

/* Lienzo y tarjetas */
.dashboard-content { background: #eef2f9 !important; padding: 18px 24px 42px !important; }
.dashboard-grid .grid-row { gap: 16px !important; }
.dashboard-component-chart-holder {
  background: #fff !important;
  border: 1px solid #dbe2f0 !important;
  border-top: 4px solid #0033A0 !important;
  border-radius: 14px !important;
  box-shadow: 0 8px 22px rgba(16, 32, 64, .08) !important;
  overflow: hidden !important;
}
.dashboard-chart-id-5 .dashboard-component-chart-holder,
.dashboard-chart-id-6 .dashboard-component-chart-holder,
.dashboard-chart-id-7 .dashboard-component-chart-holder,
.dashboard-chart-id-8 .dashboard-component-chart-holder,
.dashboard-chart-id-9 .dashboard-component-chart-holder,
.dashboard-chart-id-10 .dashboard-component-chart-holder { border-top-color: #CE1126 !important; }
.dashboard-component-chart-holder:has(.header-line) { border-top-color: #CE1126 !important; }
.dashboard-component-chart-holder .chart-container { padding: 10px 16px 14px !important; }
.dashboard-component-chart-holder .header-line {
  color: #0033A0 !important;
  font-weight: 800 !important;
  font-size: 1.55rem !important;
}
.dashboard-component-chart-holder .subheader-line { color: #64748b !important; }
.dashboard-component-chart-holder .header-title { color: #0033A0 !important; font-weight: 700 !important; }
.dashboard-component-chart-holder .slice_container { padding: 10px 14px !important; }
.dashboard-component-chart-holder:hover { box-shadow: 0 12px 28px rgba(16, 32, 64, .14) !important; }
/* El mapa usa un estilo propio sin basemap: ocultar el logo de Mapbox. */
.mapboxgl-ctrl-logo,
.mapboxgl-ctrl-attrib { display: none !important; }
"""


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
# Estilo propio sin basemap: solo se dibujan las provincias con datos.
MAP_STYLE = os.environ.get(
    "SUPERSET_MAP_STYLE",
    "/static/assets/ecuador-blank-style.json",
)
MAP_VIEWPORT = {
    "longitude": -78.6,
    "latitude": -1.3,
    "zoom": 6,
    "bearing": 0,
    "pitch": 0,
}

# Colorea el mapa por intensidad. Sin filtro de categoria cada provincia /
# sucursal aparece varias veces (una por categoria); en ese caso usa la venta
# total. Con una categoria seleccionada queda una fila por provincia / sucursal
# y se usa la venta de esa categoria.
MAP_JS_DATA_MUTATOR = """
function(data){
  var cp={},cs={};
  data.forEach(function(f){
    var p=f.properties||{};
    if(p.tipo==='provincia'){cp[p.provincia]=(cp[p.provincia]||0)+1;}
    else if(p.tipo==='sucursal'){cs[p.sucursal]=(cs[p.sucursal]||0)+1;}
  });
  var pi=[],si=[];
  data.forEach(function(f){
    var p=f.properties||{};
    if(p.tipo==='provincia'){
      var m=cp[p.provincia]>1;
      pi.push([f,Number(m?p.ventaTotal:p.ventaNeta)||0]);
    }else if(p.tipo==='sucursal'){
      var m2=cs[p.sucursal]>1;
      si.push([f,Number(m2?p.ventaTotal:p.ventaNeta)||0]);
    }
  });
  var rc={'Costa':[0,128,128,255],'Sierra':[120,72,20,255],
          'Amazonía':[0,140,60,255],'Amazonia':[0,140,60,255],
          'Oriente':[0,140,60,255]};
  function apply(items,lo,hi){
    var vals=items.map(function(x){return x[1];}).sort(function(a,b){return a-b;});
    var mn=vals.length?vals[0]:0,mx=vals.length?vals[vals.length-1]:0;
    items.forEach(function(x){
      var t=mx>mn?(x[1]-mn)/(mx-mn):0.5;
      var p=x[0].properties||{};
      p.fillColor=[
        Math.round(lo[0]+(hi[0]-lo[0])*t),
        Math.round(lo[1]+(hi[1]-lo[1])*t),
        Math.round(lo[2]+(hi[2]-lo[2])*t),
        215
      ];
      if(rc[p.region]){p.strokeColor=rc[p.region];}
    });
  }
  apply(pi,[201,220,255],[0,51,160]);
  apply(si,[255,205,210],[206,17,38]);
  return data;
}
"""

MAP_LEGEND_MARKDOWN = """
**Leyenda del mapa**

- **Relleno (intensidad):** azul claro = menor venta; azul oscuro = mayor venta. Al seleccionar una categoría en el pastel, la intensidad corresponde a esa categoría.
- **Borde de la provincia (región):** turquesa = Costa; café = Sierra; verde = Amazonía.
- **Puntos rojos:** sucursales. Clic en un punto para filtrar todo el dashboard por esa sucursal; clic en una provincia para filtrar por provincia.
"""

DATASETS = {
    # Vista unica a nivel de detalle: todos los cortes comparten dimensiones,
    # por lo que el cross-filtering funciona entre graficos.
    "v_ventas_detalle": {
        "main_dttm_col": "fecha",
        "metrics": [
            ("sum_venta_neta", "SUM(venta_neta)"),
            ("sum_unidades", "SUM(cantidad)"),
            ("sum_margen", "SUM(margen)"),
            ("sum_descuento", "SUM(descuento_usd)"),
            ("count_ventas", "COUNT(DISTINCT id_venta)"),
            ("ticket_promedio", "SUM(venta_neta) / NULLIF(COUNT(DISTINCT id_venta), 0)"),
            ("margen_pct", "SUM(margen) / NULLIF(SUM(venta_neta), 0)"),
            ("kpi_ingresos", "SUM(venta_neta)"),
            ("kpi_unidades", "SUM(cantidad)"),
            ("kpi_margen", "SUM(margen)"),
            ("kpi_descuento", "SUM(descuento_usd)"),
            ("kpi_transacciones", "COUNT(DISTINCT id_venta)"),
            ("kpi_ticket_promedio", "SUM(venta_neta) / NULLIF(COUNT(DISTINCT id_venta), 0)"),
            ("kpi_margen_pct", "SUM(margen) / NULLIF(SUM(venta_neta), 0)"),
        ],
    },
    # Hecho de rechazos: perdidas estimadas por sucursal, fecha y motivo.
    "v_rechazos": {
        "main_dttm_col": "fecha_venta",
        "metrics": [
            ("sum_perdida", "SUM(venta_perdida)"),
            ("count_rechazos", "COUNT(*)"),
            ("kpi_perdida", "SUM(venta_perdida)"),
        ],
    },
    "v_mapa_consolidado": {},
}

KPI_CARDS = [
    ("Ingresos Netos", "v_ventas_detalle", "kpi_ingresos", "$,.2f", "USD · ventas válidas", "CHART-KPI-INGRESOS"),
    ("Unidades Vendidas", "v_ventas_detalle", "kpi_unidades", ",.0f", "unidades integradas", "CHART-KPI-UNIDADES"),
    ("Margen Bruto", "v_ventas_detalle", "kpi_margen", "$,.2f", "USD · rentabilidad", "CHART-KPI-MARGEN"),
    ("Descuento Otorgado", "v_ventas_detalle", "kpi_descuento", "$,.2f", "USD · descuentos aplicados", "CHART-KPI-DESCUENTO"),
    ("Transacciones", "v_ventas_detalle", "kpi_transacciones", ",.0f", "ventas únicas", "CHART-KPI-TRANSACCIONES"),
    ("Ticket Promedio", "v_ventas_detalle", "kpi_ticket_promedio", "$,.2f", "USD por transacción", "CHART-KPI-TICKET"),
    ("Margen %", "v_ventas_detalle", "kpi_margen_pct", ".2%", "sobre ingresos netos", "CHART-KPI-MARGEN-PCT"),
    ("Pérdida por Rechazos", "v_rechazos", "kpi_perdida", "$,.2f", "USD · no integrado", "CHART-KPI-PERDIDA"),
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


PROVINCE_GEOJSON = Path(__file__).with_name("provincias.geojson")
PROVINCE_ALIASES = {"Santo Domingo": "Santo Domingo de los Tsáchilas"}


def _ring_area(ring):
    area = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _province_rows():
    if not PROVINCE_GEOJSON.exists():
        return []
    features = json.loads(PROVINCE_GEOJSON.read_text(encoding="utf-8"))["features"]
    rows = []
    for feature in features:
        name = feature["properties"]["province"]
        if name == "Galápagos":
            continue
        name = PROVINCE_ALIASES.get(name, name)
        geometry = feature.get("geometry") or {}
        rings = []
        if geometry.get("type") == "Polygon":
            rings = geometry.get("coordinates") or []
        else:
            for polygon in geometry.get("coordinates") or []:
                rings.extend(polygon)
        if not rings:
            continue
        ring = max(rings, key=_ring_area)
        points = [
            [round(float(point[0]), 5), round(float(point[1]), 5)]
            for point in ring
        ]
        if len(points) < 3:
            continue
        rows.append({
            "provincia": name,
            "polygon": json.dumps(points, separators=(",", ":")),
            "lat": round(sum(point[1] for point in points) / len(points), 6),
            "lon": round(sum(point[0] for point in points) / len(points), 6),
        })
    return rows


def _ensure_province_map(database):
    """Crea y puebla dim_provincia_mapa sin depender de volver a correr el job ETL."""
    rows = _province_rows()
    if not rows:
        print("[bootstrap] Sin GeoJSON de provincias; se omite dim_provincia_mapa.")
        return
    with database.get_sqla_engine_with_context() as engine:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE IF NOT EXISTS dim_provincia_mapa ("
                "provincia VARCHAR(80) PRIMARY KEY, "
                "polygon TEXT NOT NULL, "
                "lat NUMERIC(10,6), "
                "lon NUMERIC(10,6))"
            )
            connection.exec_driver_sql("TRUNCATE TABLE dim_provincia_mapa")
            connection.execute(
                text(
                    "INSERT INTO dim_provincia_mapa "
                    "(provincia, polygon, lat, lon) VALUES "
                    "(:provincia, :polygon, :lat, :lon)"
                ),
                rows,
            )
    print(f"[bootstrap] dim_provincia_mapa lista con {len(rows)} provincias.")


def _apply_views(database):
    """Recrea las vistas KPI para que el contenedor no dependa del job ETL."""
    views_path = Path("/app/kpi_views_postgres.sql")
    if not views_path.exists():
        return
    with database.get_sqla_engine_with_context() as engine:
        with engine.begin() as connection:
            connection.exec_driver_sql(views_path.read_text(encoding="utf-8"))
    print("[bootstrap] Vistas KPI recreadas desde kpi_views_postgres.sql.")


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

    for column in table.columns:
        if column.column_name == "geom":
            column.verbose_name = "Provincia"
            column.description = "Geometría de la provincia para filtrar el mapa"
        elif column.column_name == "provincia":
            column.verbose_name = "Provincia (nombre)"

    spec = DATASETS[view]
    if spec.get("main_dttm_col"):
        table.main_dttm_col = spec["main_dttm_col"]
        for column in table.columns:
            if column.column_name == spec["main_dttm_col"]:
                column.is_dttm = True

    existing_metrics = {metric.metric_name: metric for metric in table.metrics}
    for metric_name, expression in spec.get("metrics", []):
        metric = existing_metrics.get(metric_name)
        if metric is None:
            table.metrics.append(
                SqlMetric(metric_name=metric_name, expression=expression)
            )
        elif metric.expression != expression:
            metric.expression = expression
    db.session.commit()
    return table


def _line_params(table, dttm="fecha", metric="sum_venta_neta", y_label="Ventas netas (USD)"):
    return {
        "adhoc_filters": [],
        "annotation_layers": [],
        "bottom_margin": "auto",
        "color_scheme": COLOR_SCHEME,
        "comparison_type": "values",
        "contribution": False,
        "datasource": f"{table.id}__table",
        "granularity_sqla": dttm,
        "groupby": [],
        "left_margin": "auto",
        "line_interpolation": "linear",
        "metrics": [metric],
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
        "y_axis_label": y_label,
    }


def _bar_params(table, groupby, x_label, metric="sum_venta_neta", y_label="Ventas netas (USD)", row_limit=100):
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
        "metrics": [metric],
        "order_desc": True,
        "row_limit": row_limit,
        "show_legend": True,
        "time_range": "No filter",
        "url_params": {},
        "viz_type": "dist_bar",
        "x_axis_label": x_label,
        "y_axis_format": "SMART_NUMBER",
        "y_axis_label": y_label,
    }


def _table_params(table, groupby, metrics, row_limit=50, order_metric=None):
    params = {
        "adhoc_filters": [],
        "all_columns": [],
        "color_pn": True,
        "datasource": f"{table.id}__table",
        "granularity_sqla": None,
        "groupby": groupby,
        "include_search": True,
        "metrics": metrics,
        "order_desc": True,
        "page_length": 20,
        "query_mode": "aggregate",
        "row_limit": row_limit,
        "show_cell_bars": True,
        "table_filter": False,
        "time_range": "No filter",
        "url_params": {},
        "viz_type": "table",
    }
    if order_metric:
        params["timeseries_limit_metric"] = order_metric
    return params


def _pie_params(table, groupby):
    return {
        "adhoc_filters": [],
        "color_scheme": COLOR_SCHEME,
        "datasource": f"{table.id}__table",
        "donut": True,
        "granularity_sqla": None,
        "groupby": [groupby],
        "innerRadius": 40,
        "label_type": "key_percent",
        "labels_outside": True,
        "legendOrientation": "right",
        "legendType": "scroll",
        "metric": "sum_venta_neta",
        "number_format": "SMART_NUMBER",
        "outerRadius": 70,
        "row_limit": 100,
        "show_labels": True,
        "show_legend": True,
        "show_labels_threshold": 3,
        "show_total": True,
        "time_range": "No filter",
        "url_params": {},
        "viz_type": "pie",
    }


def _geojson_map_params(table):
    return {
        "adhoc_filters": [],
        "autozoom": False,
        "datasource": f"{table.id}__table",
        "extruded": False,
        "fill_color_picker": {"r": 0, "g": 0, "b": 0, "a": 0},
        "filled": True,
        "filter_nulls": True,
        "geojson": "geojson",
        "js_data_mutator": MAP_JS_DATA_MUTATOR,
        # geo_key lleva el prefijo "provincia:" o "sucursal:" para que el clic
        # emita el filtro correcto (provincia o nombre de sucursal).
        "line_column": "geo_key",
        "line_width": 1.5,
        "line_width_unit": "pixels",
        "mapbox_style": MAP_STYLE,
        # Puntos de sucursal seleccionables sin tapar el poligono provincial.
        "point_unit": "pixels",
        "point_radius_fixed": {"type": "fix", "value": 7},
        "point_radius_scale": 100,
        "point_radius_min_pixels": 4,
        "point_radius_max_pixels": 9,
        "row_limit": 100,
        "stroke_color_picker": {"r": 255, "g": 255, "b": 255, "a": 0},
        "stroked": True,
        "table_filter": True,
        "time_range": "No filter",
        "url_params": {},
        "viewport": dict(MAP_VIEWPORT),
        "viz_type": "deck_geojson",
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


def _create_dashboard(kpi_slices, chart_slices, tables, admin, dashboard=None):
    (
        line_slice,
        category_slice,
        branch_slice,
        segment_slice,
        map_slice,
        pie_slice,
    ) = chart_slices
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
            "children": [
                "ROW-KPI-1",
                "ROW-KPI-2",
                "ROW-LINE",
                "ROW-MAP",
                "ROW-BARS",
            ],
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
        "ROW-MAP": {
            "children": ["CHART-MAP", "CHART-PIE"],
            "id": "ROW-MAP",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "CHART-MAP": _chart_component("CHART-MAP", map_slice, "ROW-MAP", 8, 100),
        "CHART-PIE": _chart_component("CHART-PIE", pie_slice, "ROW-MAP", 4, 100),
        "ROW-LINE": {
            "children": ["CHART-LINE"],
            "id": "ROW-LINE",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "CHART-LINE": _chart_component("CHART-LINE", line_slice, "ROW-LINE", 12),
        "ROW-BRANCH": {
            "children": ["CHART-BRANCH"],
            "id": "ROW-BRANCH",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "CHART-BRANCH": _chart_component("CHART-BRANCH", branch_slice, "ROW-BRANCH", 12),
        "ROW-SEG-CAT": {
            "children": ["CHART-SEGMENT", "CHART-CATEGORY"],
            "id": "ROW-SEG-CAT",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        },
        "CHART-SEGMENT": _chart_component("CHART-SEGMENT", segment_slice, "ROW-SEG-CAT", 6),
        "CHART-CATEGORY": _chart_component("CHART-CATEGORY", category_slice, "ROW-SEG-CAT", 6),
    }
    for component in kpi_components:
        position[component["id"]] = component

    all_slices = [slice_obj for slice_obj, _ in kpi_slices] + list(chart_slices)
    all_slice_ids = [slice_obj.id for slice_obj in all_slices]
    cross_filter_scope = {"rootPath": ["ROOT_ID"], "excluded": []}
    province_targets = [
        {"datasetId": table.id, "column": {"name": "provincia"}}
        for table in (
            tables["v_ventas_mes"],
            tables["v_ventas_categoria"],
            tables["v_ventas_sucursal"],
            tables["v_ventas_segmento"],
            tables["v_ventas_provincia"],
            tables["v_sucursales_mapa"],
            tables["v_mapa_consolidado"],
            tables["v_kpis_consolidados"],
        )
    ]
    metadata = {
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "default_filters": "{}",
        "color_scheme": COLOR_SCHEME,
        "label_colors": {},
        "native_filter_configuration": [
            {
                "cascadeParentIds": [],
                "chartsInScope": all_slice_ids,
                "controlValues": {
                    "enableEmptyFilter": False,
                    "defaultToFirstItem": False,
                    "inverseSelection": False,
                    "multiSelect": False,
                    "searchAllOptions": False,
                    "sortAscending": True,
                    "sortMetric": None,
                },
                "defaultValue": None,
                "description": "Filtra todos los gráficos por provincia del cliente.",
                "filterType": "filter_select",
                "id": "NATIVE_FILTER-provincia",
                "name": "Provincia",
                "scope": cross_filter_scope,
                "tabsInScope": [],
                "targets": province_targets,
                "type": "NATIVE_FILTER",
            }
        ],
        "cross_filters_enabled": True,
        "chart_configuration": {
            str(slice_id): {
                "id": slice_id,
                "crossFilters": {
                    "scope": cross_filter_scope,
                    "chartsInScope": [
                        other
                        for other in all_slice_ids
                        if other != slice_id
                    ],
                },
            }
            for slice_id in all_slice_ids
        },
        "global_chart_configuration": {
            "scope": cross_filter_scope,
            "chartsInScope": all_slice_ids,
        },
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
    dashboard.css = DASHBOARD_CSS
    dashboard.published = True
    dashboard.slices = [
        slice_obj for slice_obj, _ in kpi_slices
    ] + list(chart_slices)
    if admin is not None:
        dashboard.owners = [admin]
    db.session.commit()
    return dashboard


def _native_filter(filter_id, name, rows, all_slice_ids):
    return {
        "cascadeParentIds": [],
        "chartsInScope": all_slice_ids,
        "controlValues": {
            "enableEmptyFilter": False,
            "defaultToFirstItem": False,
            "inverseSelection": False,
            "multiSelect": False,
            "searchAllOptions": True,
            "sortAscending": True,
            "sortMetric": None,
        },
        "defaultValue": None,
        "description": f"Filtra el dashboard por {name.lower()}.",
        "filterType": "filter_select",
        "id": f"NATIVE_FILTER-{filter_id}",
        "name": name,
        "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
        "tabsInScope": [],
        "targets": [
            {"datasetId": table.id, "column": {"name": column}}
            for table, column in rows
        ],
        "type": "NATIVE_FILTER",
    }


def _build_dashboard(kpi_slices, layout, tables, admin, dashboard=None):
    kpi_components = []
    for index, (slice_obj, component_id) in enumerate(kpi_slices):
        row_id = "ROW-KPI-1" if index < 4 else "ROW-KPI-2"
        kpi_components.append(_chart_component(component_id, slice_obj, row_id, 3, 30))

    chart_components = []
    row_children = {"ROW-KPI-1": [], "ROW-KPI-2": []}
    for row_id, charts in layout:
        row_children.setdefault(row_id, [])
        for component_id, slice_obj, width, height in charts:
            component = _chart_component(component_id, slice_obj, row_id, width, height)
            chart_components.append(component)
            row_children[row_id].append(component_id)
    row_children["ROW-KPI-1"] = [c["id"] for c in kpi_components[:4]]
    row_children["ROW-KPI-2"] = [c["id"] for c in kpi_components[4:]]

    rows_order = ["ROW-KPI-1", "ROW-KPI-2"]
    for row_id, _ in layout:
        rows_order.append(row_id)
        if row_id == "ROW-MAP":
            rows_order.append("ROW-LEGEND")
    row_children["ROW-LEGEND"] = ["MARKDOWN-LEGEND"]
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"children": ["GRID_ID"], "id": "ROOT_ID", "type": "ROOT"},
        "GRID_ID": {
            "children": rows_order,
            "id": "GRID_ID",
            "parents": ["ROOT_ID"],
            "type": "GRID",
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "meta": {"text": DASHBOARD_TITLE},
            "type": "HEADER",
        },
    }
    for row_id in rows_order:
        position[row_id] = {
            "children": row_children.get(row_id, []),
            "id": row_id,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": ["ROOT_ID", "GRID_ID"],
            "type": "ROW",
        }
    for component in kpi_components + chart_components:
        position[component["id"]] = component
    position["MARKDOWN-LEGEND"] = {
        "children": [],
        "id": "MARKDOWN-LEGEND",
        "meta": {"code": MAP_LEGEND_MARKDOWN, "height": 18, "width": 12},
        "parents": ["ROOT_ID", "GRID_ID", "ROW-LEGEND"],
        "type": "MARKDOWN",
    }

    slice_by_component = {}
    for slice_obj, component_id in kpi_slices:
        slice_by_component[component_id] = slice_obj.id
    for _, charts in layout:
        for component_id, slice_obj, _, _ in charts:
            slice_by_component[component_id] = slice_obj.id
    component_by_slice = {sid: comp for comp, sid in slice_by_component.items()}
    all_slice_ids = list(slice_by_component.values())

    loss_components = {
        comp for comp in slice_by_component
        if comp.startswith("CHART-LOSS") or comp == "CHART-KPI-PERDIDA"
    }
    sales_ids = [
        sid for comp, sid in slice_by_component.items()
        if comp not in loss_components
    ]
    loss_ids = [
        sid for comp, sid in slice_by_component.items() if comp in loss_components
    ]
    map_id = slice_by_component.get("CHART-MAP")
    scope_all_sales = sales_ids + ([map_id] if map_id else [])

    def excluded_for(slice_id):
        """Graficos que NO deben recibir el filtro de este grafico.

        El frontend recalcula chartsInScope a partir de scope.excluded, por lo
        que aqui se excluyen los datasets que no tienen la columna emitida.
        """
        comp = component_by_slice.get(slice_id)
        excluded = {slice_id}
        if comp == "CHART-MAP":
            # Emite provincia o nombre_sucursal; ambos existen en ventas y rechazos.
            return sorted(excluded)
        if comp in loss_components:
            # Rechazos: no mezclar con ventas (columnas y fecha distintas).
            excluded.update(sales_ids)
            if map_id:
                excluded.add(map_id)
            return sorted(excluded)
        # Graficos de ventas: no enviar a rechazos.
        excluded.update(loss_ids)
        if comp in {
            "CHART-PIE", "CHART-CATEGORY", "CHART-DISCOUNT",
            "CHART-TOP-CATEGORIA", "CHART-REGION",
            "CHART-BRANCH", "CHART-TOP-SUCURSAL",
        }:
            # El mapa tiene categoria, region y nombre_sucursal.
            pass
        elif map_id:
            # line (fecha), segmento, marca o canal no existen en el mapa.
            excluded.add(map_id)
        return sorted(excluded)

    det = tables["v_ventas_detalle"]
    mp = tables["v_mapa_consolidado"]
    rec = tables["v_rechazos"]
    native_filters = [
        _native_filter(
            "provincia", "Provincia",
            [(det, "provincia"), (mp, "provincia"), (rec, "provincia")],
            all_slice_ids,
        ),
        _native_filter(
            "categoria", "Categoría",
            [(det, "categoria"), (mp, "categoria"), (rec, "categoria")],
            all_slice_ids,
        ),
        _native_filter(
            "sucursal", "Sucursal",
            [(det, "nombre_sucursal"), (rec, "nombre_sucursal")],
            all_slice_ids,
        ),
        _native_filter(
            "marca", "Marca",
            [(det, "marca"), (rec, "marca")],
            all_slice_ids,
        ),
        _native_filter(
            "region", "Región",
            [(det, "region"), (mp, "region"), (rec, "region")],
            all_slice_ids,
        ),
    ]

    cross_filter_scope = {"rootPath": ["ROOT_ID"], "excluded": []}
    metadata = {
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "default_filters": "{}",
        "color_scheme": COLOR_SCHEME,
        "label_colors": {},
        "native_filter_configuration": native_filters,
        "cross_filters_enabled": True,
        "chart_configuration": {
            str(slice_id): {
                "id": slice_id,
                "crossFilters": {
                    "scope": {
                        "rootPath": ["ROOT_ID"],
                        "excluded": excluded_for(slice_id),
                    },
                    "chartsInScope": [
                        other for other in all_slice_ids
                        if other not in excluded_for(slice_id)
                    ],
                },
            }
            for slice_id in all_slice_ids
        },
        "global_chart_configuration": {
            "scope": cross_filter_scope,
            "chartsInScope": all_slice_ids,
        },
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
    dashboard.css = DASHBOARD_CSS
    dashboard.published = True
    dashboard.slices = [
        slice_obj for slice_obj, _ in kpi_slices
    ] + [
        slice_obj for _, charts in layout for _, slice_obj, _, _ in charts
    ]
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
        _ensure_province_map(database)
        _apply_views(database)
        schema = _wait_for_views(database)

        tables = {
            view: _get_dataset(database, schema, view) for view in DATASETS
        }

        kpi_slices = []
        for title, table_key, metric, number_format, subheader, component_id in KPI_CARDS:
            table = tables[table_key]
            slice_obj = _get_slice(
                title,
                table,
                "big_number_total",
                _big_number_params(table, metric, subheader, number_format),
                admin,
            )
            kpi_slices.append((slice_obj, component_id))

        det = tables["v_ventas_detalle"]
        rec = tables["v_rechazos"]

        map_slice = _get_slice(
            "Mapa de Ventas y Sucursales",
            tables["v_mapa_consolidado"],
            "deck_geojson",
            _geojson_map_params(tables["v_mapa_consolidado"]),
            admin,
        )
        pie = _get_slice(
            "Participación por Categoría",
            det,
            "pie",
            _pie_params(det, "categoria"),
            admin,
        )
        line = _get_slice(
            "Evolución de Ventas",
            det,
            "line",
            _line_params(det),
            admin,
        )
        category = _get_slice(
            "Ventas por Categoría",
            det,
            "dist_bar",
            _bar_params(det, "categoria", "Categoría"),
            admin,
        )
        branch = _get_slice(
            "Desempeño por Sucursal",
            det,
            "dist_bar",
            _bar_params(det, "nombre_sucursal", "Sucursal"),
            admin,
        )
        segment = _get_slice(
            "Ventas por Segmento",
            det,
            "dist_bar",
            _bar_params(det, "segmento", "Segmento"),
            admin,
        )
        region = _get_slice(
            "Ventas por Región",
            det,
            "dist_bar",
            _bar_params(det, "region", "Región"),
            admin,
        )
        channel = _get_slice(
            "Ventas por Canal",
            det,
            "dist_bar",
            _bar_params(det, "canal_venta", "Canal"),
            admin,
        )
        brand = _get_slice(
            "Ventas por Marca",
            det,
            "dist_bar",
            _bar_params(det, "marca", "Marca", row_limit=15),
            admin,
        )
        discount = _get_slice(
            "Descuento por Categoría",
            det,
            "dist_bar",
            _bar_params(
                det, "categoria", "Categoría",
                metric="sum_descuento", y_label="Descuento (USD)",
            ),
            admin,
        )
        top_marca = _get_slice(
            "Marca Más Vendida",
            det,
            "table",
            _table_params(
                det, ["marca"], ["sum_venta_neta", "sum_unidades"],
                row_limit=1, order_metric="sum_venta_neta",
            ),
            admin,
        )
        top_categoria = _get_slice(
            "Categoría Más Vendida",
            det,
            "table",
            _table_params(
                det, ["categoria"], ["sum_venta_neta", "sum_unidades"],
                row_limit=1, order_metric="sum_venta_neta",
            ),
            admin,
        )
        top_sucursal = _get_slice(
            "Sucursal con Más Ventas",
            det,
            "table",
            _table_params(
                det, ["nombre_sucursal"], ["sum_venta_neta", "sum_unidades"],
                row_limit=1, order_metric="sum_venta_neta",
            ),
            admin,
        )
        loss_branch = _get_slice(
            "Pérdidas por Sucursal",
            rec,
            "dist_bar",
            _bar_params(
                rec, "nombre_sucursal", "Sucursal",
                metric="sum_perdida", y_label="Pérdida estimada (USD)",
            ),
            admin,
        )
        loss_date = _get_slice(
            "Pérdidas por Fecha",
            rec,
            "line",
            _line_params(
                rec, dttm="fecha_venta",
                metric="sum_perdida", y_label="Pérdida estimada (USD)",
            ),
            admin,
        )
        db.session.commit()

        layout = [
            ("ROW-MAP", [
                ("CHART-MAP", map_slice, 8, 100),
                ("CHART-PIE", pie, 4, 100),
            ]),
            ("ROW-LINE", [
                ("CHART-LINE", line, 12, 55),
            ]),
            ("ROW-BARS-1", [
                ("CHART-CATEGORY", category, 6, 60),
                ("CHART-BRANCH", branch, 6, 60),
            ]),
            ("ROW-BARS-2", [
                ("CHART-SEGMENT", segment, 4, 60),
                ("CHART-BRAND", brand, 4, 60),
                ("CHART-DISCOUNT", discount, 4, 60),
            ]),
            ("ROW-REGION", [
                ("CHART-REGION", region, 6, 55),
                ("CHART-CHANNEL", channel, 6, 55),
            ]),
            ("ROW-TOP", [
                ("CHART-TOP-MARCA", top_marca, 4, 45),
                ("CHART-TOP-CATEGORIA", top_categoria, 4, 45),
                ("CHART-TOP-SUCURSAL", top_sucursal, 4, 45),
            ]),
            ("ROW-LOSS-1", [
                ("CHART-LOSS-BRANCH", loss_branch, 6, 70),
                ("CHART-LOSS-DATE", loss_date, 6, 70),
            ]),
        ]

        _build_dashboard(kpi_slices, layout, tables, admin, dashboard=existing)
        print("[bootstrap] Dashboard Sales Analytics creado/actualizado correctamente.")


if __name__ == "__main__":
    main()
