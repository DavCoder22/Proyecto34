"""Configuración de Apache Superset para la PoC."""
import os


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Define SUPERSET_SECRET_KEY antes de iniciar Superset")

# Base de metadatos de Superset (dashboards, usuarios, datasets).
# Por defecto SQLite persistente; para producción usar PostgreSQL.
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_METADATA_DATABASE_URL",
    "sqlite:////app/superset_home/superset.db",
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = _env_bool("SUPERSET_TALISMAN_ENABLED", "false")
SESSION_COOKIE_SECURE = _env_bool("SUPERSET_COOKIE_SECURE", "false")
ENABLE_PROXY_FIX = True
PREVENT_UNSAFE_DB_CONNECTIONS = False

ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088
APP_NAME = "PoC Sales Analytics"
