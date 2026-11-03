"""Construye un dashboard HTML estatico con Bootstrap 5 a partir del DW SQLite."""
import html
import json
import math
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "03_dw" / "dw.db"
OUT = Path(__file__).resolve().parent / "dashboard.html"
GEO = Path(__file__).resolve().parent / "data" / "provincias.geojson"


def query(conn, sql, params=()):
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def scope_data(conn, where="", params=()):
    """Agrega todos los cortes del dashboard para un filtro geografico."""
    clause = f"WHERE {where}" if where else ""
    kpis = dict(conn.execute(
        "SELECT COALESCE(SUM(f.venta_neta), 0) ingresos, "
        "COALESCE(SUM(f.cantidad), 0) unidades, "
        "COALESCE(SUM(f.margen), 0) margen, "
        "COUNT(DISTINCT f.id_venta) transacciones, "
        "COALESCE(SUM(f.venta_neta) * 1.0 / NULLIF(COUNT(DISTINCT f.id_venta), 0), 0) ticket, "
        "COALESCE(SUM(f.margen) * 1.0 / NULLIF(SUM(f.venta_neta), 0), 0) margen_pct "
        "FROM FactVentas f JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause}", params
    ).fetchone())

    mes = query(conn, (
        "SELECT t.anio, t.mes, t.mes_nombre, SUM(f.venta_neta) venta_neta "
        "FROM FactVentas f "
        "JOIN DimTiempo t ON f.id_tiempo = t.id_tiempo "
        "JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause} GROUP BY t.anio, t.mes, t.mes_nombre ORDER BY t.anio, t.mes"
    ), params)

    categoria = query(conn, (
        "SELECT p.categoria, SUM(f.venta_neta) venta_neta "
        "FROM FactVentas f "
        "JOIN DimProducto p ON f.id_producto = p.id_producto "
        "JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause} GROUP BY p.categoria ORDER BY venta_neta DESC"
    ), params)

    sucursal = query(conn, (
        "SELECT s.nombre_sucursal, SUM(f.venta_neta) venta_neta "
        "FROM FactVentas f "
        "JOIN DimSucursal s ON f.id_sucursal = s.id_sucursal "
        "JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause} GROUP BY s.nombre_sucursal ORDER BY venta_neta DESC"
    ), params)

    segmento = query(conn, (
        "SELECT c.segmento, SUM(f.venta_neta) venta_neta "
        "FROM FactVentas f JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause} GROUP BY c.segmento ORDER BY venta_neta DESC"
    ), params)

    canal = query(conn, (
        "SELECT COALESCE(NULLIF(f.canal_venta, ''), 'No especificado') canal_venta, "
        "SUM(f.venta_neta) venta_neta "
        "FROM FactVentas f JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause} GROUP BY canal_venta ORDER BY venta_neta DESC"
    ), params)

    metodo_pago = query(conn, (
        "SELECT COALESCE(NULLIF(f.metodo_pago, ''), 'No especificado') metodo_pago, "
        "SUM(f.venta_neta) venta_neta "
        "FROM FactVentas f JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause} GROUP BY metodo_pago ORDER BY venta_neta DESC"
    ), params)

    producto = query(conn, (
        "SELECT p.nombre_producto, SUM(f.venta_neta) venta_neta "
        "FROM FactVentas f "
        "JOIN DimProducto p ON f.id_producto = p.id_producto "
        "JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        f"{clause} GROUP BY p.nombre_producto ORDER BY venta_neta DESC LIMIT 8"
    ), params)

    return {
        "kpis": kpis,
        "mes": mes,
        "categoria": categoria,
        "sucursal": sucursal,
        "segmento": segmento,
        "canal": canal,
        "metodo_pago": metodo_pago,
        "producto": producto,
    }


def _is_point(value):
    return (isinstance(value, (list, tuple)) and len(value) == 2
            and all(isinstance(v, (int, float)) for v in value))


def _iter_rings(geometry):
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if kind == "Polygon":
        for ring in coords:
            yield ring
    elif kind == "MultiPolygon":
        if coords and _is_point(coords[0]):
            for ring in coords:
                yield ring
        else:
            for polygon in coords:
                if polygon and _is_point(polygon[0]):
                    yield polygon
                else:
                    for ring in polygon:
                        yield ring


def _project(points, box, width, height, pad):
    lon0, lat0, lon1, lat1 = box
    mid_lat = math.radians((lat0 + lat1) / 2)
    scale_x = max(0.15, math.cos(mid_lat))
    span_x = (lon1 - lon0) * scale_x
    span_y = (lat1 - lat0)
    scale = min((width - 2 * pad) / span_x, (height - 2 * pad) / span_y)
    offset_x = (width - span_x * scale) / 2
    offset_y = (height - span_y * scale) / 2

    def convert(point):
        lon, lat = point
        x = offset_x + (lon - lon0) * scale_x * scale
        y = offset_y + (lat1 - lat) * scale
        return x, y

    return [convert(p) for p in points]


def _rings_to_path(rings, box, width, height, pad):
    parts = []
    for ring in rings:
        if len(ring) < 3:
            continue
        projected = _project(ring, box, width, height, pad)
        head, *tail = projected
        segment = [f"M{head[0]:.1f},{head[1]:.1f}"]
        segment += [f"L{x:.1f},{y:.1f}" for x, y in tail]
        parts.append("".join(segment) + "Z")
    return "".join(parts)


def build_map_svg():
    """Genera un coropleta SVG autocontenido de las 24 provincias del Ecuador."""
    if not GEO.exists():
        return '<div class="alert alert-warning mb-0">No se encontro el GeoJSON de provincias.</div>'

    features = json.loads(GEO.read_text(encoding="utf-8"))["features"]
    mainland = [f for f in features if f["properties"]["province"] != "Galápagos"]
    islands = [f for f in features if f["properties"]["province"] == "Galápagos"]

    coords = [p for f in mainland for ring in _iter_rings(f["geometry"]) for p in ring]
    lon0, lon1 = min(p[0] for p in coords), max(p[0] for p in coords)
    lat0, lat1 = min(p[1] for p in coords), max(p[1] for p in coords)
    main_box = (lon0, lat0, lon1, lat1)

    width, height = 720, 560
    paths = []
    for feature in mainland:
        province = feature["properties"]["province"]
        rings = list(_iter_rings(feature["geometry"]))
        d = _rings_to_path(rings, main_box, width, height, 18)
        if d:
            name = html.escape(province, quote=True)
            paths.append(
                f'<path class="provincia" data-provincia="{name}" d="{d}" '
                f'aria-label="{name}"></path>'
            )

    inset = ""
    if islands:
        island_coords = [p for f in islands for ring in _iter_rings(f["geometry"]) for p in ring]
        if island_coords:
            ilon0, ilon1 = min(p[0] for p in island_coords), max(p[0] for p in island_coords)
            ilat0, ilat1 = min(p[1] for p in island_coords), max(p[1] for p in island_coords)
            island_box = (ilon0, ilat0, ilon1, ilat1)
            island_paths = []
            for feature in islands:
                province = feature["properties"]["province"]
                rings = list(_iter_rings(feature["geometry"]))
                d = _rings_to_path(rings, island_box, 118, 96, 8)
                if d:
                    name = html.escape(province, quote=True)
                    island_paths.append(
                        f'<path class="provincia" data-provincia="{name}" d="{d}" '
                        f'aria-label="{name}"></path>'
                    )
            inset = (
                '<g class="map-inset" transform="translate(8, 452)">'
                '<rect x="0" y="0" width="118" height="104" rx="10"></rect>'
                f'{"".join(island_paths)}'
                '<text x="59" y="99" text-anchor="middle">Galápagos</text>'
                '</g>'
            )

    return (
        f'<svg id="mapa" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Mapa de ventas por provincia del Ecuador">'
        f'<g class="map-mainland">{"".join(paths)}</g>{inset}</svg>'
    )


HTML_TEMPLATE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sales Analytics UCE | PoC ETL</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js" integrity="sha384-NrKB+u6Ts6AtkIhwPixiKTzgSKNblyhlk0Sohlgar9UHUBzai/sgnNNWWd291xqt" crossorigin="anonymous"></script>
<style>
:root {
  --uce-blue: #0033A0;
  --uce-red: #CE1126;
  --uce-gold: #F2A900;
  --uce-green: #1E7B3C;
  --uce-bg: #f2f5fb;
}
body {
  background: var(--uce-bg);
  color: #1f2937;
  font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
}
.navbar-uce {
  background: linear-gradient(90deg, #002b87 0%, #0033A0 60%, #0b49c9 100%);
  border-bottom: 4px solid var(--uce-red);
}
.navbar-uce .navbar-brand { font-weight: 700; letter-spacing: .2px; }
.brand-mark {
  width: 38px; height: 38px; border-radius: 10px;
  background: linear-gradient(135deg, var(--uce-blue), #0b49c9);
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 800; font-size: 13px;
  border: 1px solid rgba(255, 255, 255, .35);
}
.hero {
  background: linear-gradient(135deg, #ffffff 0%, #eef3ff 55%, #ffecef 100%);
  border: 1px solid #dbe4f5; border-radius: 18px; padding: 28px 32px;
  box-shadow: 0 12px 30px rgba(16, 32, 64, .07);
}
.hero h1 { color: var(--uce-blue); font-weight: 800; letter-spacing: -.5px; }
.badge-uce { background: var(--uce-red); color: #fff; }
.filter-bar {
  background: #fff; border: 1px solid #dbe4f5; border-radius: 14px;
  box-shadow: 0 6px 16px rgba(16, 32, 64, .05);
}
.filter-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--uce-red); box-shadow: 0 0 0 4px rgba(206, 17, 38, .15); }
.kpi-card {
  border: 0; border-top: 4px solid var(--uce-blue); border-radius: 14px;
  box-shadow: 0 8px 22px rgba(16, 32, 64, .08);
  transition: transform .15s ease, box-shadow .15s ease;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(16, 32, 64, .14); }
.kpi-card.kpi-red { border-top-color: var(--uce-red); }
.kpi-card.kpi-gold { border-top-color: var(--uce-gold); }
.kpi-card.kpi-green { border-top-color: var(--uce-green); }
.kpi-label { color: #64748b; font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.kpi-value { color: var(--uce-blue); font-size: 1.65rem; font-weight: 800; letter-spacing: -.5px; }
.chart-card { border: 0; border-radius: 14px; box-shadow: 0 8px 22px rgba(16, 32, 64, .08); height: 100%; }
.chart-card .card-header {
  background: #fff; border-bottom: 1px solid #e5ebf5;
  font-weight: 700; color: var(--uce-blue);
}
.chart-box { position: relative; height: 300px; }
.chart-box.tall { height: 340px; }
.chart-box.map { height: 540px; display: flex; align-items: center; justify-content: center; }
.map-wrap { position: relative; width: 100%; height: 100%; }
#mapa { width: 100%; height: 100%; display: block; overflow: visible; }
.provincia { fill: #e2e8f0; stroke: #ffffff; stroke-width: 1.1; cursor: pointer; transition: fill .18s ease, stroke .18s ease; vector-effect: non-scaling-stroke; }
.provincia:hover { stroke: var(--uce-red); stroke-width: 2; }
.provincia.activa { stroke: var(--uce-red); stroke-width: 2.6; }
.provincia.sin-datos { fill: #eef2f7; cursor: default; }
.map-inset rect { fill: #f8fafc; stroke: #cbd5e1; stroke-dasharray: 4 3; }
.map-inset text { fill: #64748b; font-size: 8px; font-weight: 600; }
.map-tooltip {
  position: absolute; z-index: 5; min-width: 190px; pointer-events: none;
  background: rgba(0, 31, 96, .95); color: #fff; border-radius: 10px;
  padding: 10px 12px; font-size: .8rem; opacity: 0; transform: translateY(4px);
  transition: opacity .12s ease, transform .12s ease; box-shadow: 0 10px 24px rgba(0, 0, 0, .2);
}
.map-tooltip.show { opacity: 1; transform: translateY(0); }
.map-tooltip .tt-title { font-weight: 700; font-size: .88rem; margin-bottom: 2px; }
.map-tooltip .tt-row { display: flex; justify-content: space-between; gap: 14px; opacity: .9; }
.map-gradient { height: 8px; width: 130px; border-radius: 999px; background: linear-gradient(90deg, #c9dcff, #0033A0); }
.province-row {
  width: 100%; border: 1px solid #e5ebf5; border-radius: 10px; background: #fff;
  padding: 7px 10px; text-align: left; transition: border-color .15s, background .15s, transform .15s;
}
.province-row:hover { border-color: #b9cdf5; background: #f8faff; transform: translateX(2px); }
.province-row.active { border-color: var(--uce-red); background: #fff5f6; box-shadow: inset 3px 0 0 var(--uce-red); }
.province-row .progress { height: 5px; background: #edf1f8; }
.province-row .progress-bar { background: linear-gradient(90deg, #4f81bd, var(--uce-blue)); }
.progress-auto { display: flex; flex-direction: column; gap: 4px; max-height: 470px; overflow: auto; padding-right: 4px; }
.share-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 6px 14px; }
.share-item { display: flex; align-items: center; gap: 8px; font-size: .82rem; }
.share-swatch { width: 10px; height: 10px; border-radius: 3px; flex: 0 0 auto; }
.share-name { flex: 1 1 auto; color: #475569; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.share-value { font-weight: 700; color: #1e293b; }
.insight-box { border-left: 4px solid var(--uce-gold); background: #fffaf0; border-radius: 10px; padding: 12px 14px; font-size: .86rem; color: #5c4a1e; }
.footer-uce { color: #64748b; font-size: .85rem; }
@media (max-width: 767px) {
  .chart-box.map { height: 320px; }
  .chart-box { height: 260px; }
}
</style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark navbar-uce shadow-sm">
  <div class="container-fluid px-4">
    <a class="navbar-brand d-flex align-items-center gap-2" href="#">
      <span class="brand-mark">UCE</span>
      <span>Sales Analytics <span class="fw-normal opacity-75">| UCE</span></span>
    </a>
    <span class="navbar-text text-white-50 small d-none d-md-inline">Universidad Central del Ecuador · Inteligencia de Negocios</span>
  </div>
</nav>
<main class="container-fluid px-3 px-lg-4 py-4">
  <section class="hero mb-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
      <div>
        <div class="text-uppercase small fw-bold text-danger mb-1">PoC · Integración y calidad de datos</div>
        <h1 class="h2 mb-1">Dashboard Comercial</h1>
        <p class="text-secondary mb-0">Universo válido integrado por el ETL · Fuente: <code>03_dw/dw.db</code></p>
      </div>
      <div class="text-end">
        <span class="badge badge-uce rounded-pill px-3 py-2">Mapa provincial · 6 KPIs · 6 gráficos</span>
        <div class="small text-secondary mt-2">Vista ejecutiva interactiva</div>
      </div>
    </div>
  </section>

  <section class="filter-bar p-3 mb-4">
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3">
      <div class="d-flex align-items-center gap-3">
        <span class="filter-dot"></span>
        <div>
          <div class="kpi-label mb-0">Filtro geográfico</div>
          <div class="fw-bold" id="filterName">Todas las provincias</div>
          <div class="small text-secondary" id="filterSub">Universo nacional validado</div>
        </div>
      </div>
      <div class="d-flex flex-wrap align-items-center gap-2">
        <span class="small text-secondary d-none d-lg-inline">Haz clic en una provincia del mapa o del ranking</span>
        <button type="button" class="btn btn-outline-danger btn-sm d-none" id="resetFilter">Quitar filtro</button>
      </div>
    </div>
  </section>

  <div class="row g-3 mb-4">
    <div class="col-12 col-sm-6 col-lg-4 col-xxl-2">
      <div class="card kpi-card h-100"><div class="card-body">
        <div class="kpi-label">Ingresos netos</div>
        <div class="kpi-value" id="ingresos"></div>
        <div class="small text-secondary">USD · universo validado</div>
      </div></div>
    </div>
    <div class="col-12 col-sm-6 col-lg-4 col-xxl-2">
      <div class="card kpi-card h-100"><div class="card-body">
        <div class="kpi-label">Unidades</div>
        <div class="kpi-value" id="unidades"></div>
        <div class="small text-secondary">volumen físico vendido</div>
      </div></div>
    </div>
    <div class="col-12 col-sm-6 col-lg-4 col-xxl-2">
      <div class="card kpi-card kpi-red h-100"><div class="card-body">
        <div class="kpi-label">Margen bruto</div>
        <div class="kpi-value" id="margen"></div>
        <div class="small text-secondary">rentabilidad absoluta</div>
      </div></div>
    </div>
    <div class="col-12 col-sm-6 col-lg-4 col-xxl-2">
      <div class="card kpi-card kpi-gold h-100"><div class="card-body">
        <div class="kpi-label">Transacciones</div>
        <div class="kpi-value" id="transacciones"></div>
        <div class="small text-secondary">ventas únicas</div>
      </div></div>
    </div>
    <div class="col-12 col-sm-6 col-lg-4 col-xxl-2">
      <div class="card kpi-card kpi-green h-100"><div class="card-body">
        <div class="kpi-label">Ticket promedio</div>
        <div class="kpi-value" id="ticket"></div>
        <div class="small text-secondary">USD por transacción</div>
      </div></div>
    </div>
    <div class="col-12 col-sm-6 col-lg-4 col-xxl-2">
      <div class="card kpi-card h-100"><div class="card-body">
        <div class="kpi-label">Margen %</div>
        <div class="kpi-value" id="margen_pct"></div>
        <div class="small text-secondary">sobre ingresos netos</div>
      </div></div>
    </div>
  </div>

  <div class="row g-4 mb-4">
    <div class="col-12">
      <div class="card chart-card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span>Evolución de ventas</span>
          <span class="badge text-bg-light text-secondary fw-normal">Mensual</span>
        </div>
        <div class="card-body"><div class="chart-box tall"><canvas id="mes"></canvas></div></div>
      </div>
    </div>
  </div>

  <div class="row g-4 mb-4">
    <div class="col-12">
      <div class="card chart-card">
        <div class="card-header d-flex flex-wrap justify-content-between align-items-center gap-2">
          <span>Geografía de ventas por provincia</span>
          <span class="badge text-bg-light text-secondary fw-normal">Provincia del cliente</span>
        </div>
        <div class="card-body">
          <div class="row g-4">
            <div class="col-12 col-lg-7">
              <div class="chart-box map">
                <div class="map-wrap" id="mapWrap">
                  __MAP_SVG__
                  <div class="map-tooltip" id="mapTooltip"></div>
                </div>
              </div>
              <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mt-2">
                <div class="d-flex align-items-center gap-2 small text-secondary">
                  <span>Menor venta</span><span class="map-gradient"></span><span>Mayor venta</span>
                </div>
                <div class="small text-secondary">Fuente: <code>DimCliente.provincia</code></div>
              </div>
            </div>
            <div class="col-12 col-lg-5 d-flex flex-column">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="kpi-label mb-0">Ranking de provincias</span>
                <span class="small text-secondary">Participación</span>
              </div>
              <div class="progress-auto flex-grow-1" id="ranking"></div>
              <div class="insight-box mt-3" id="provinceInsight"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="row g-4 mb-4">
    <div class="col-12 col-lg-5">
      <div class="card chart-card">
        <div class="card-header d-flex flex-wrap justify-content-between align-items-center gap-2">
          <span>Participación porcentual</span>
          <select class="form-select form-select-sm w-auto" id="dimension" aria-label="Dimensión del pastel">
            <option value="categoria">Categoría</option>
            <option value="canal">Canal de venta</option>
            <option value="metodo_pago">Método de pago</option>
            <option value="segmento">Segmento</option>
          </select>
        </div>
        <div class="card-body">
          <div class="chart-box"><canvas id="participacion"></canvas></div>
          <div class="share-legend mt-3" id="shareLegend"></div>
        </div>
      </div>
    </div>
    <div class="col-12 col-lg-7">
      <div class="card chart-card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span>Top productos por venta neta</span>
          <span class="badge text-bg-light text-secondary fw-normal">8 primeros</span>
        </div>
        <div class="card-body"><div class="chart-box"><canvas id="producto"></canvas></div></div>
      </div>
    </div>
  </div>

  <div class="row g-4">
    <div class="col-12 col-lg-6">
      <div class="card chart-card">
        <div class="card-header">Desempeño por sucursal</div>
        <div class="card-body"><div class="chart-box"><canvas id="sucursal"></canvas></div></div>
      </div>
    </div>
    <div class="col-12 col-lg-6">
      <div class="card chart-card">
        <div class="card-header">Ventas por segmento</div>
        <div class="card-body"><div class="chart-box"><canvas id="segmento"></canvas></div></div>
      </div>
    </div>
  </div>

  <footer class="footer-uce text-center mt-4">
    Sales Analytics UCE · Universidad Central del Ecuador · Dashboard generado desde el data warehouse validado.
  </footer>
</main>
<script>
const data = __PAYLOAD__;
const money = n => new Intl.NumberFormat('es-EC', {style: 'currency', currency: 'USD'}).format(n || 0);
const num = n => new Intl.NumberFormat('es-EC').format(n || 0);
const pct = n => new Intl.NumberFormat('es-EC', {style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2}).format(n || 0);
const compact = n => new Intl.NumberFormat('es-EC', {notation: 'compact', compactDisplay: 'short', maximumFractionDigits: 1}).format(n || 0);
const axisMoney = n => '$' + compact(n);
const palette = ['#0033A0', '#CE1126', '#F2A900', '#1E7B3C', '#4F81BD', '#C0504D', '#9BBB59', '#8064A2', '#2E75B6', '#B45309'];
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

const dimensions = {
  categoria: {field: 'categoria', label: 'Categoría'},
  canal: {field: 'canal_venta', label: 'Canal de venta'},
  metodo_pago: {field: 'metodo_pago', label: 'Método de pago'},
  segmento: {field: 'segmento', label: 'Segmento'}
};
const state = {provincia: null, dimension: 'categoria'};
const provinceAlias = {'Santo Domingo': 'Santo Domingo de los Tsáchilas'};
const provinceKey = name => provinceAlias[name] || name;
const provData = Object.fromEntries(data.provincias.map(p => [p.provincia, p]));
const provinceValues = data.provincias.map(p => p.venta_neta);
const maxProvince = Math.max(...provinceValues, 1);
const minProvince = Math.min(...provinceValues);
const nationalIncome = data.total.kpis.ingresos || 1;

function currentScope() {
  return state.provincia ? data.porProvincia[state.provincia] : data.total;
}

function setKpis(scope) {
  document.getElementById('ingresos').textContent = money(scope.kpis.ingresos);
  document.getElementById('unidades').textContent = num(scope.kpis.unidades);
  document.getElementById('margen').textContent = money(scope.kpis.margen);
  document.getElementById('transacciones').textContent = num(scope.kpis.transacciones);
  document.getElementById('ticket').textContent = money(scope.kpis.ticket);
  document.getElementById('margen_pct').textContent = pct(scope.kpis.margen_pct);
}

function mixColor(from, to, t) {
  const a = from.match(/[0-9a-f]{2}/gi).map(x => parseInt(x, 16));
  const b = to.match(/[0-9a-f]{2}/gi).map(x => parseInt(x, 16));
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * t));
  return '#' + c.map(v => v.toString(16).padStart(2, '0')).join('');
}

Chart.defaults.font.family = 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif';
Chart.defaults.color = '#64748b';
const vertical = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {legend: {display: false}, tooltip: {backgroundColor: '#0033A0', padding: 12, cornerRadius: 8}},
  scales: {
    x: {grid: {display: false}, ticks: {maxRotation: 45, minRotation: 0}},
    y: {beginAtZero: true, grid: {color: '#e5ebf5'}, ticks: {callback: value => axisMoney(value)}}
  }
};
const horizontal = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {legend: {display: false}, tooltip: {backgroundColor: '#0033A0', padding: 12, cornerRadius: 8,
    callbacks: {label: ctx => money(ctx.parsed.x)}}},
  scales: {
    x: {beginAtZero: true, grid: {color: '#e5ebf5'}, ticks: {callback: value => axisMoney(value)}},
    y: {grid: {display: false}, ticks: {autoSkip: false, font: {size: 11}}}
  }
};

const lineChart = new Chart(document.getElementById('mes'), {
  type: 'line',
  data: {labels: [], datasets: [{
    data: [], borderColor: '#CE1126', backgroundColor: 'rgba(206, 17, 38, .12)',
    pointBackgroundColor: '#CE1126', pointRadius: 3, fill: true, tension: .3, borderWidth: 2
  }]},
  options: vertical
});
const shareChart = new Chart(document.getElementById('participacion'), {
  type: 'doughnut',
  data: {labels: [], datasets: [{data: [], backgroundColor: palette, borderColor: '#fff', borderWidth: 2, hoverOffset: 6}]},
  options: {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '58%',
    plugins: {
      legend: {display: false},
      tooltip: {backgroundColor: '#0033A0', padding: 12, cornerRadius: 8,
        callbacks: {label: ctx => `${ctx.label}: ${money(ctx.parsed)} (${pct(ctx.parsed / (ctx.dataset.data.reduce((a, b) => a + b, 0) || 1))})`}}
    }
  }
});
const productChart = new Chart(document.getElementById('producto'), {
  type: 'bar',
  data: {labels: [], datasets: [{data: [], backgroundColor: '#0033A0', borderRadius: 5, maxBarThickness: 22}]},
  options: horizontal
});
const branchChart = new Chart(document.getElementById('sucursal'), {
  type: 'bar',
  data: {labels: [], datasets: [{data: [], backgroundColor: [], borderRadius: 6, maxBarThickness: 42}]},
  options: vertical
});
const segmentChart = new Chart(document.getElementById('segmento'), {
  type: 'bar',
  data: {labels: [], datasets: [{data: [], backgroundColor: ['#0033A0', '#CE1126', '#F2A900', '#1E7B3C', '#4F81BD'], borderRadius: 6, maxBarThickness: 42}]},
  options: vertical
});

function updateLine(scope) {
  lineChart.data.labels = scope.mes.map(x => x.anio + '-' + String(x.mes).padStart(2, '0'));
  lineChart.data.datasets[0].data = scope.mes.map(x => x.venta_neta);
  lineChart.update();
}

function dimensionRows(scope) {
  const field = dimensions[state.dimension].field;
  return (scope[state.dimension] || [])
    .map(row => ({label: row[field], value: Number(row.venta_neta) || 0}))
    .filter(row => row.value > 0);
}

function renderShareLegend(rows) {
  const total = rows.reduce((sum, row) => sum + row.value, 0) || 1;
  const legend = document.getElementById('shareLegend');
  legend.innerHTML = rows.map((row, i) => `
    <div class="share-item">
      <span class="share-swatch" style="background:${palette[i % palette.length]}"></span>
      <span class="share-name" title="${esc(row.label)}">${esc(row.label)}</span>
      <span class="share-value">${pct(row.value / total)}</span>
    </div>`).join('');
}

function updateShare(scope) {
  const rows = dimensionRows(scope);
  shareChart.data.labels = rows.map(row => row.label);
  shareChart.data.datasets[0].data = rows.map(row => row.value);
  shareChart.update();
  renderShareLegend(rows);
}

function updateProducts(scope) {
  productChart.data.labels = scope.producto.map(row => row.nombre_producto);
  productChart.data.datasets[0].data = scope.producto.map(row => row.venta_neta);
  productChart.update();
}

function updateBranches(scope) {
  branchChart.data.labels = scope.sucursal.map(row => row.nombre_sucursal);
  branchChart.data.datasets[0].data = scope.sucursal.map(row => row.venta_neta);
  branchChart.data.datasets[0].backgroundColor = scope.sucursal.map((_, i) => palette[i % palette.length]);
  branchChart.update();
}

function updateSegments(scope) {
  segmentChart.data.labels = scope.segmento.map(row => row.segmento);
  segmentChart.data.datasets[0].data = scope.segmento.map(row => row.venta_neta);
  segmentChart.update();
}

function paintMap() {
  document.querySelectorAll('#mapa .provincia[data-provincia]').forEach(path => {
    const name = provinceKey(path.dataset.provincia);
    const info = provData[name];
    if (!info) {
      path.classList.add('sin-datos');
      path.style.fill = '#eef2f7';
      path.classList.remove('activa');
      return;
    }
    path.classList.remove('sin-datos');
    const span = maxProvince - minProvince;
    const t = span > 0 ? 0.12 + 0.88 * ((info.venta_neta - minProvince) / span) : 0.7;
    path.style.fill = mixColor('#c9dcff', '#0033A0', Math.min(1, Math.max(0, t)));
    path.classList.toggle('activa', state.provincia === name);
  });
}

function showTooltip(event, name) {
  const info = provData[name];
  if (!info) return;
  const tip = document.getElementById('mapTooltip');
  tip.innerHTML = `
    <div class="tt-title">${esc(name)}</div>
    <div class="tt-row"><span>Venta neta</span><strong>${money(info.venta_neta)}</strong></div>
    <div class="tt-row"><span>Participación</span><strong>${pct(info.venta_neta / nationalIncome)}</strong></div>
    <div class="tt-row"><span>Transacciones</span><strong>${num(info.transacciones)}</strong></div>`;
  const wrap = document.getElementById('mapWrap');
  const rect = wrap.getBoundingClientRect();
  const x = Math.min(event.clientX - rect.left + 16, rect.width - 210);
  const y = Math.min(event.clientY - rect.top + 16, rect.height - 110);
  tip.style.left = Math.max(8, x) + 'px';
  tip.style.top = Math.max(8, y) + 'px';
  tip.classList.add('show');
}

function hideTooltip() {
  document.getElementById('mapTooltip').classList.remove('show');
}

function renderRanking() {
  const ranking = document.getElementById('ranking');
  ranking.innerHTML = data.provincias.map(p => {
    const share = p.venta_neta / nationalIncome;
    return `
      <button type="button" class="province-row" data-provincia="${esc(p.provincia)}">
        <div class="d-flex justify-content-between align-items-center gap-2">
          <span class="fw-semibold text-truncate">${esc(p.provincia)}</span>
          <span class="text-nowrap"><span class="fw-bold text-primary">${money(p.venta_neta)}</span>
            <span class="small text-secondary ms-1">${pct(share)}</span></span>
        </div>
        <div class="progress mt-1"><div class="progress-bar" style="width:${(p.venta_neta / maxProvince * 100).toFixed(1)}%"></div></div>
      </button>`;
  }).join('');
  ranking.querySelectorAll('[data-provincia]').forEach(button => {
    button.addEventListener('click', () => applyProvince(button.dataset.provincia));
  });
}

function highlightRanking() {
  document.querySelectorAll('#ranking .province-row').forEach(row => {
    row.classList.toggle('active', row.dataset.provincia === state.provincia);
  });
}

function updateFilterUi() {
  document.getElementById('filterName').textContent = state.provincia || 'Todas las provincias';
  document.getElementById('filterSub').textContent = state.provincia
    ? `Ventas de clientes en ${state.provincia}`
    : 'Universo nacional validado';
  const reset = document.getElementById('resetFilter');
  reset.classList.toggle('d-none', !state.provincia);
  hideTooltip();
}

function updateInsight(scope) {
  const top = (scope.categoria || [])[0];
  const topProduct = (scope.producto || [])[0];
  const prov = (scope.sucursal || [])[0];
  const total = scope.kpis.ingresos || 1;
  const pieces = [];
  if (top) pieces.push(`<strong>${esc(top.categoria)}</strong> concentra ${pct(top.venta_neta / total)} de la venta neta.`);
  if (topProduct) pieces.push(`El producto líder es <strong>${esc(topProduct.nombre_producto)}</strong>.`);
  if (prov) pieces.push(`La sucursal con mayor aporte es <strong>${esc(prov.nombre_sucursal)}</strong>.`);
  document.getElementById('provinceInsight').innerHTML = pieces.join(' ');
}

function applyProvince(name) {
  if (state.provincia === name) {
    state.provincia = null;
  } else {
    state.provincia = name;
  }
  refresh();
}

function refresh() {
  const scope = currentScope();
  setKpis(scope);
  updateLine(scope);
  updateShare(scope);
  updateProducts(scope);
  updateBranches(scope);
  updateSegments(scope);
  updateInsight(scope);
  updateFilterUi();
  paintMap();
  highlightRanking();
}

document.getElementById('resetFilter').addEventListener('click', () => {
  state.provincia = null;
  refresh();
});
document.getElementById('dimension').addEventListener('change', event => {
  state.dimension = event.target.value;
  updateShare(currentScope());
});

document.querySelectorAll('#mapa .provincia[data-provincia]').forEach(path => {
  const name = provinceKey(path.dataset.provincia);
  if (!provData[name]) return;
  path.addEventListener('click', () => applyProvince(name));
  path.addEventListener('mousemove', event => showTooltip(event, name));
  path.addEventListener('mouseleave', hideTooltip);
});

const initialProvince = new URLSearchParams(location.search).get('provincia');
if (initialProvince && data.porProvincia[initialProvince]) {
  state.provincia = initialProvince;
}

renderRanking();
refresh();
</script>
</body>
</html>
"""


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    provincias = query(conn, (
        "SELECT c.provincia, SUM(f.venta_neta) venta_neta, SUM(f.cantidad) unidades, "
        "SUM(f.margen) margen, COUNT(DISTINCT f.id_venta) transacciones, "
        "SUM(f.venta_neta) * 1.0 / NULLIF(COUNT(DISTINCT f.id_venta), 0) ticket, "
        "SUM(f.margen) * 1.0 / NULLIF(SUM(f.venta_neta), 0) margen_pct "
        "FROM FactVentas f JOIN DimCliente c ON f.id_cliente = c.id_cliente "
        "GROUP BY c.provincia ORDER BY venta_neta DESC"
    ))
    total = scope_data(conn)
    por_provincia = {
        row["provincia"]: scope_data(conn, "c.provincia = ?", (row["provincia"],))
        for row in provincias
    }
    conn.close()

    data = {
        "provincias": provincias,
        "total": total,
        "porProvincia": por_provincia,
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (HTML_TEMPLATE
            .replace("__MAP_SVG__", build_map_svg())
            .replace("__PAYLOAD__", payload))
    OUT.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {OUT}")


if __name__ == "__main__":
    main()
