"""Configuracion central del ETL. Paths y reglas de negocio."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "01_datos" / "raw"
DATA_STAGING = ROOT / "01_datos" / "staging"
DW_PATH = ROOT / "03_dw" / "dw.db"
LOG_PATH = ROOT / "06_calidad"

# Fuentes originales (copiar a raw/ antes de correr)
SOURCES = {
    "clientes":   {"file": "clientes.csv",   "sep": ",", "encoding": "utf-8-sig"},
    "sucursales": {"file": "sucursales.csv", "sep": ",", "encoding": "utf-8-sig"},
    "productos":  {"file": "productos.xlsx", "sheet": 0},
    "ventas":     {"file": "ventas_sucursales.csv", "sep": ",", "encoding": "utf-8-sig"},
}

# Claves primarias por entidad
PK = {
    "clientes": "cod_cliente",
    "sucursales": "cod_sucursal",
    "productos": "cod_producto",
    "ventas": "id_venta",
}

# Columnas de texto a homologar (variantes -> canonico)
HOMOLOGACION = {
    "categoria": {
        "TECNOLOGÍA": "Tecnología", "TECNOLOGIA": "Tecnología",
        "tecnología": "Tecnología", "tecnologia": "Tecnología",
    },
    "segmento": {
        "": "Sin segmento", "nan": "Sin segmento", "None": "Sin segmento",
    },
    "canal_venta": {
        "": "No especificado", "nan": "No especificado",
    },
    "metodo_pago": {
        "": "No especificado", "nan": "No especificado",
    },
}

# Columnas de descuento que pueden venir en decimal (0.05) o porcentaje (5.0)
DESCUENTO_COLS = ["descuento_pct"]
# Columnas de fecha a parsear
DATE_COLS = {
    "clientes": ["fecha_registro"],
    "sucursales": ["fecha_apertura"],
    "ventas": ["fecha_venta"],
}

# FK a validar: (tabla_hija, col_fk, tabla_padre)
FK_CHECKS = [
    ("ventas", "cod_cliente", "clientes"),
    ("ventas", "cod_producto", "productos"),
    ("ventas", "cod_sucursal", "sucursales"),
]