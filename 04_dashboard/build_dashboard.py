"""Construye un dashboard HTML estatico a partir del DW SQLite."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "03_dw" / "dw.db"
OUT = Path(__file__).resolve().parent / "dashboard.html"


def query(conn, sql):
    return [dict(row) for row in conn.execute(sql).fetchall()]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    data = {
        "kpis": dict(conn.execute("SELECT SUM(venta_neta) ingresos, SUM(cantidad) unidades, SUM(margen) margen, COUNT(DISTINCT id_venta) transacciones FROM FactVentas").fetchone()),
        "mes": query(conn, "SELECT anio, mes, mes_nombre, venta_neta FROM v_ventas_mes ORDER BY anio, mes"),
        "categoria": query(conn, "SELECT categoria, venta_neta FROM v_ventas_categoria ORDER BY venta_neta DESC"),
        "sucursal": query(conn, "SELECT nombre_sucursal, venta_neta FROM v_ventas_sucursal ORDER BY venta_neta DESC"),
        "segmento": query(conn, "SELECT segmento, venta_neta FROM v_ventas_segmento ORDER BY venta_neta DESC"),
    }
    conn.close()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sales Analytics | PoC ETL</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
body{{margin:0;background:#f4f1ea;color:#172121;font:16px system-ui,sans-serif}}main{{max-width:1200px;margin:auto;padding:32px}}
h1{{font:700 42px Georgia,serif;margin:0 0 8px}}.sub{{color:#68716d;margin:0 0 28px}}.cards,.charts{{display:grid;gap:16px}}.cards{{grid-template-columns:repeat(4,1fr)}}.charts{{grid-template-columns:repeat(2,1fr);margin-top:16px}}
.card,.panel{{background:#fffdf8;border:1px solid #ddd8cb;border-radius:14px;padding:20px;box-shadow:0 5px 18px #17312b0d}}.label{{color:#68716d;font-size:13px;text-transform:uppercase;letter-spacing:.08em}}.value{{font-size:28px;font-weight:700;margin-top:8px}}.panel h2{{font-size:18px;margin:0 0 12px}}canvas{{max-height:290px}}
@media(max-width:800px){{main{{padding:20px}}h1{{font-size:32px}}.cards,.charts{{grid-template-columns:1fr 1fr}}}}@media(max-width:500px){{.cards,.charts{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>Sales Analytics</h1><p class="sub">Universo valido integrado por el proceso ETL | generado desde 03_dw/dw.db</p>
<section class="cards"><div class="card"><div class="label">Ingresos netos</div><div class="value" id="ingresos"></div></div><div class="card"><div class="label">Unidades</div><div class="value" id="unidades"></div></div><div class="card"><div class="label">Margen bruto</div><div class="value" id="margen"></div></div><div class="card"><div class="label">Transacciones</div><div class="value" id="transacciones"></div></div></section>
<section class="charts"><div class="panel"><h2>Evolucion de ventas</h2><canvas id="mes"></canvas></div><div class="panel"><h2>Ventas por categoria</h2><canvas id="categoria"></canvas></div><div class="panel"><h2>Desempeno por sucursal</h2><canvas id="sucursal"></canvas></div><div class="panel"><h2>Ventas por segmento</h2><canvas id="segmento"></canvas></div></section>
<script>const data={payload};const money=n=>new Intl.NumberFormat('es-EC',{{style:'currency',currency:'USD'}}).format(n||0);const num=n=>new Intl.NumberFormat('es-EC').format(n||0);
document.getElementById('ingresos').textContent=money(data.kpis.ingresos);document.getElementById('unidades').textContent=num(data.kpis.unidades);document.getElementById('margen').textContent=money(data.kpis.margen);document.getElementById('transacciones').textContent=num(data.kpis.transacciones);
const common={{responsive:true,plugins:{{legend:{{display:false}}}}}};const bar=(id,rows,label)=>new Chart(document.getElementById(id),{{type:'bar',data:{{labels:rows.map(x=>x[label]),datasets:[{{data:rows.map(x=>x.venta_neta),backgroundColor:'#d26a3a',borderRadius:6}}]}},options:common}});
new Chart(document.getElementById('mes'),{{type:'line',data:{{labels:data.mes.map(x=>x.anio+'-'+String(x.mes).padStart(2,'0')),datasets:[{{data:data.mes.map(x=>x.venta_neta),borderColor:'#12645b',backgroundColor:'#12645b22',fill:true,tension:.3}}]}},options:common}});bar('categoria',data.categoria,'categoria');bar('sucursal',data.sucursal,'nombre_sucursal');bar('segmento',data.segmento,'segmento');</script></main></body></html>'''
    OUT.write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {OUT}")


if __name__ == "__main__":
    main()
