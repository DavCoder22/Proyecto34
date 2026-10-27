"""Configuración de Apache Superset para la PoC."""
import os


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Define SUPERSET_SECRET_KEY antes de iniciar Superset")

# Base de metadatos de Superset (dashboards, usuarios, datasets).
# Por defecto SQLite persistente; para producción usar PostgreSQL.
def _normalize_postgres_url(value):
    if value.startswith("postgres://"):
        return "postgresql+psycopg2://" + value[len("postgres://"):]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg2://" + value[len("postgresql://"):]
    return value


SQLALCHEMY_DATABASE_URI = _normalize_postgres_url(
    os.environ.get(
        "SUPERSET_METADATA_DATABASE_URL",
        "sqlite:////app/superset_home/superset.db",
    )
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = _env_bool("SUPERSET_TALISMAN_ENABLED", "false")
SESSION_COOKIE_SECURE = _env_bool("SUPERSET_COOKIE_SECURE", "false")
ENABLE_PROXY_FIX = True
PREVENT_UNSAFE_DB_CONNECTIONS = False

ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = int(os.environ.get("SUPERSET_PORT", "8088"))
APP_NAME = os.environ.get("SUPERSET_APP_NAME", "Sales Analytics UCE")
APP_ICON = "/static/assets/images/uce_logo.svg"
FAVICONS = [{"href": "/static/assets/images/uce_favicon.svg"}]
LOGO_TOOLTIP = "Sales Analytics · Universidad Central del Ecuador"
LOGO_TARGET_PATH = "/"
LOGO_RIGHT_TEXT = ""

# Identidad visual UCE: rojo escarlata y azul cobalto.
UCE_AZUL = "#0033A0"
UCE_ROJO = "#CE1126"
UCE_ORO = "#F2A900"
UCE_VERDE = "#1E7B3C"

THEME_OVERRIDES = {
    "borderRadius": 6,
    "colors": {
        "primary": {"base": UCE_AZUL},
        "secondary": {"base": UCE_ROJO},
        "grayscale": {"base": "#1F2937"},
    },
}

EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "id": "uceColors",
        "description": "Paleta UCE",
        "isDiverging": False,
        "colors": [
            UCE_AZUL,
            UCE_ROJO,
            UCE_ORO,
            UCE_VERDE,
            "#4F81BD",
            "#C0504D",
            "#9BBB59",
            "#8064A2",
            "#4BACC6",
            "#F79646",
        ],
    }
]
