FROM jupyter/scipy-notebook:python-3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

USER $NB_UID

WORKDIR /home/jovyan/work

# Instalar las dependencias declaradas por el proyecto y copiar el repositorio
# dentro de la imagen. En la nube no existe el volumen local de docker-compose.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --only-binary=:all: -r /tmp/requirements.txt \
    psycopg2-binary==2.9.13 \
    matplotlib==3.11.2 \
    seaborn==0.13.2 \
    ipywidgets==8.1.9

COPY --chown=${NB_UID}:${NB_GID} 01_datos /home/jovyan/work/01_datos
COPY --chown=${NB_UID}:${NB_GID} 02_etl /home/jovyan/work/02_etl
COPY --chown=${NB_UID}:${NB_GID} 03_dw /home/jovyan/work/03_dw
COPY --chown=${NB_UID}:${NB_GID} 04_dashboard /home/jovyan/work/04_dashboard
COPY --chown=${NB_UID}:${NB_GID} 05_lineage.md /home/jovyan/work/05_lineage.md
COPY --chown=${NB_UID}:${NB_GID} 06_calidad /home/jovyan/work/06_calidad
COPY --chown=${NB_UID}:${NB_GID} 07_presentacion /home/jovyan/work/07_presentacion
COPY --chown=${NB_UID}:${NB_GID} README.md LICENSE /home/jovyan/work/
COPY --chown=${NB_UID}:${NB_GID} docker/entrypoint.sh /usr/local/bin/poc-entrypoint.sh
COPY --chown=${NB_UID}:${NB_GID} docker/notebook.sh /usr/local/bin/poc-notebook.sh

# Dejar lista la evidencia: fuentes, staging, DW, reportes y dashboard HTML.
RUN chmod +x /usr/local/bin/poc-entrypoint.sh /usr/local/bin/poc-notebook.sh \
    && python 02_etl/main.py \
    && python 04_dashboard/build_dashboard.py

EXPOSE 8888

# Al arrancar, si DATABASE_URL existe, se recarga el DW en PostgreSQL y luego inicia Jupyter.
ENTRYPOINT ["/usr/local/bin/poc-entrypoint.sh"]
CMD ["/usr/local/bin/poc-notebook.sh"]
