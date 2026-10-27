FROM apache/superset:3.1.1

USER root

RUN pip install --no-cache-dir --only-binary=:all: "psycopg2-binary==2.9.12"

COPY docker/superset/superset_config.py /app/pythonpath/superset_config.py
COPY docker/superset/bootstrap_dashboard.py /app/bootstrap_dashboard.py
COPY 04_dashboard/kpi_views_postgres.sql /app/kpi_views_postgres.sql
COPY docker/superset/assets/uce_logo.svg /app/superset/static/assets/images/uce_logo.svg
COPY docker/superset/assets/uce_favicon.svg /app/superset/static/assets/images/uce_favicon.svg
COPY docker/superset/entrypoint.sh /usr/local/bin/superset-entrypoint.sh
RUN chmod +x /usr/local/bin/superset-entrypoint.sh

USER superset

ENV SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py

EXPOSE 8088

ENTRYPOINT ["/usr/local/bin/superset-entrypoint.sh"]
