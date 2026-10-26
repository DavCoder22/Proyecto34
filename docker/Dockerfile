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
RUN pip install --no-cache-dir -r /tmp/requirements.txt psycopg2-binary matplotlib seaborn ipywidgets

COPY --chown=${NB_UID}:${NB_GID} . /home/jovyan/work

# Dejar lista la evidencia: fuentes, staging, DW, reportes y dashboard HTML.
RUN python 02_etl/main.py && \
    python 04_dashboard/build_dashboard.py

EXPOSE 8888

CMD start-notebook.sh \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --NotebookApp.token=${JUPYTER_TOKEN} \
    --NotebookApp.password=''
