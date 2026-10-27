"""Construye un dashboard HTML estatico con Bootstrap 5 a partir del DW SQLite."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "03_dw" / "dw.db"
OUT = Path(__file__).resolve().parent / "dashboard.html"


def query(conn, sql):
    return [dict(row) for row in conn.execute(sql).fetchall()]


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
.navbar-uce .navbar-brand {
  font-weight: 700;
  letter-spacing: .2px;
}
.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--uce-blue), #0b49c9);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 13px;
  border: 1px solid rgba(255, 255, 255, .35);
}
.hero {
  background: linear-gradient(135deg, #ffffff 0%, #eef3ff 55%, #ffecef 100%);
  border: 1px solid #dbe4f5;
  border-radius: 18px;
  padding: 28px 32px;
  box-shadow: 0 12px 30px rgba(16, 32, 64, .07);
}
.hero h1 {
  color: var(--uce-blue);
  font-weight: 800;
  letter-spacing: -.5px;
}
.badge-uce {
  background: var(--uce-red);
  color: #fff;
}
.kpi-card {
  border: 0;
  border-top: 4px solid var(--uce-blue);
  border-radius: 14px;
  box-shadow: 0 8px 22px rgba(16, 32, 64, .08);
  transition: transform .15s ease, box-shadow .15s ease;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(16, 32, 64, .14);
}
.kpi-card.kpi-red { border-top-color: var(--uce-red); }
.kpi-card.kpi-gold { border-top-color: var(--uce-gold); }
.kpi-card.kpi-green { border-top-color: var(--uce-green); }
.kpi-label {
  color: #64748b;
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.kpi-value {
  color: var(--uce-blue);
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -.5px;
}
.chart-card {
  border: 0;
  border-radius: 14px;
  box-shadow: 0 8px 22px rgba(16, 32, 64, .08);
}
.chart-card .card-header {
  background: #fff;
  border-bottom: 1px solid #e5ebf5;
  font-weight: 700;
  color: var(--uce-blue);
}
.chart-box {
  position: relative;
  height: 300px;
}
.chart-box.tall {
  height: 340px;
}
.footer-uce {
  color: #64748b;
  font-size: .85rem;
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
        <p class="text-secondary mb-0">Universo válido integrado por el proceso ETL · Fuente: <code>03_dw/dw.db</code></p>
      </div>
      <div class="text-end">
        <span class="badge badge-uce rounded-pill px-3 py-2">4 índices + 2 indicadores</span>
        <div class="small text-secondary mt-2">Vista ejecutiva</div>
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

  <div class="row g-4">
    <div class="col-12">
      <div class="card chart-card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <span>Evolución de ventas</span>
          <span class="badge text-bg-light text-secondary fw-normal">Mensual</span>
        </div>
        <div class="card-body"><div class="chart-box tall"><canvas id="mes"></canvas></div></div>
      </div>
    </div>
    <div class="col-12 col-lg-4">
      <div class="card chart-card">
        <div class="card-header">Ventas por categoría</div>
        <div class="card-body"><div class="chart-box"><canvas id="categoria"></canvas></div></div>
      </div>
    </div>
    <div class="col-12 col-lg-4">
      <div class="card chart-card">
        <div class="card-header">Desempeño por sucursal</div>
        <div class="card-body"><div class="chart-box"><canvas id="sucursal"></canvas></div></div>
      </div>
    </div>
    <div class="col-12 col-lg-4">
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
const palette = ['#0033A0', '#CE1126', '#F2A900', '#1E7B3C', '#4F81BD', '#C0504D', '#9BBB59', '#8064A2'];

document.getElementById('ingresos').textContent = money(data.kpis.ingresos);
document.getElementById('unidades').textContent = num(data.kpis.unidades);
document.getElementById('margen').textContent = money(data.kpis.margen);
document.getElementById('transacciones').textContent = num(data.kpis.transacciones);
document.getElementById('ticket').textContent = money(data.kpis.ticket);
document.getElementById('margen_pct').textContent = pct(data.kpis.margen_pct);

Chart.defaults.font.family = 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif';
Chart.defaults.color = '#64748b';
const common = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {display: false},
    tooltip: {backgroundColor: '#0033A0', padding: 12, cornerRadius: 8}
  },
  scales: {
    x: {grid: {display: false}, ticks: {maxRotation: 45, minRotation: 0}},
    y: {beginAtZero: true, grid: {color: '#e5ebf5'}, ticks: {callback: value => axisMoney(value)}}
  }
};
const bar = (id, rows, label) => new Chart(document.getElementById(id), {
  type: 'bar',
  data: {
    labels: rows.map(x => x[label]),
    datasets: [{
      data: rows.map(x => x.venta_neta),
      backgroundColor: rows.map((_, index) => palette[index % palette.length]),
      borderRadius: 6,
      maxBarThickness: 54
    }]
  },
  options: common
});
new Chart(document.getElementById('mes'), {
  type: 'line',
  data: {
    labels: data.mes.map(x => x.anio + '-' + String(x.mes).padStart(2, '0')),
    datasets: [{
      data: data.mes.map(x => x.venta_neta),
      borderColor: '#CE1126',
      backgroundColor: 'rgba(206, 17, 38, .12)',
      pointBackgroundColor: '#CE1126',
      fill: true,
      tension: .3,
      borderWidth: 2
    }]
  },
  options: common
});
bar('categoria', data.categoria, 'categoria');
bar('sucursal', data.sucursal, 'nombre_sucursal');
bar('segmento', data.segmento, 'segmento');
</script>
</body>
</html>
"""


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    data = {
        "kpis": dict(conn.execute(
            "SELECT SUM(venta_neta) ingresos, SUM(cantidad) unidades, "
            "SUM(margen) margen, COUNT(DISTINCT id_venta) transacciones, "
            "SUM(venta_neta) * 1.0 / COUNT(DISTINCT id_venta) ticket, "
            "SUM(margen) * 1.0 / SUM(venta_neta) margen_pct "
            "FROM FactVentas"
        ).fetchone()),
        "mes": query(conn, "SELECT anio, mes, mes_nombre, venta_neta FROM v_ventas_mes ORDER BY anio, mes"),
        "categoria": query(conn, "SELECT categoria, venta_neta FROM v_ventas_categoria ORDER BY venta_neta DESC"),
        "sucursal": query(conn, "SELECT nombre_sucursal, venta_neta FROM v_ventas_sucursal ORDER BY venta_neta DESC"),
        "segmento": query(conn, "SELECT segmento, venta_neta FROM v_ventas_segmento ORDER BY venta_neta DESC"),
    }
    conn.close()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(HTML_TEMPLATE.replace("__PAYLOAD__", payload), encoding="utf-8")
    print(f"Dashboard generado: {OUT}")


if __name__ == "__main__":
    main()
