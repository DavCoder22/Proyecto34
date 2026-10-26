FROM apache/superset:3.1.1

USER root

RUN pip install --no-cache-dir --only-binary=:all: "psycopg2-binary==2.9.13"

COPY docker/superset/superset_config.py /app/pythonpath/superset_config.py
COPY docker/superset/bootstrap_dashboard.py /app/bootstrap_dashboard.py
COPY docker/superset/entrypoint.sh /usr/local/bin/superset-entrypoint.sh
RUN chmod +x /usr/local/bin/superset-entrypoint.sh

USER superset

ENV SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py

EXPOSE 8088

ENTRYPOINT ["/usr/local/bin/superset-entrypoint.sh"]
